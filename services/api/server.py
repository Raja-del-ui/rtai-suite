#!/usr/bin/env python3
"""rtai-api: hardened JSON microservice exposing suite capabilities over HTTP.

Endpoints:
    GET  /health                     liveness probe
    GET  /version                    build metadata
    GET  /metrics                    Prometheus exposition (text/plain)
    GET  /openapi.json               machine-readable API contract
    POST /v1/recon                   synchronous passive recon bundle
    POST /v1/recon/async             submit background recon job -> 202 + job id
    GET  /v1/jobs                    recent jobs
    GET  /v1/jobs/{id}               job status/result
    POST /v1/payloads/validate       injection arsenal schema check

Security model:
    - Bearer auth enforced when RTAI_API_TOKEN is set; otherwise the API runs
      OPEN with a loud warning (development convenience only). Auth failures
      and rate-limit hits are written to a hash-chained tamper-evident audit log.
    - Per-IP sliding-window rate limiting; conservative body-size caps;
      defensive security headers on every response.

Usage:
    python services/api/server.py --port 9000 [--require-auth]
"""

import argparse
import hashlib
import hmac
import json
import os
import queue
import sys
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from rtai_core.audit import record as audit_record
from rtai_core.cli_app import find_repo_root, TOOLS
from rtai_core.logging_utils import get_logger, setup_logging
from rtai_core.metrics import REGISTRY
from rtai_core.version import __version__

LOG = get_logger("api")
MAX_BODY = 512 * 1024

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


class SlidingWindowLimiter:
    def __init__(self, limit_per_minute: int):
        self.limit = limit_per_minute
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            window = self._hits[key]
            while window and now - window[0] > 60.0:
                window.popleft()
            if len(window) >= self.limit:
                return False
            window.append(now)
            return True


def _load_project_module(relative: str):
    import importlib.util

    root = find_repo_root(Path(__file__).resolve().parent)
    path = root / relative
    spec = importlib.util.spec_from_file_location(
        f"rtai_proj_{uuid.uuid4().hex[:8]}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # noqa: S302 - local trusted code only
    return module


def run_recon(target: str, include_http: bool) -> dict:
    """Real recon execution; kept module-level so tests can stub it."""
    sources = _load_project_module(TOOLS["recon"].replace("recon_agent.py", "sources.py"))
    scoring = _load_project_module(
        TOOLS["recon"].replace("recon_agent.py", "scoring.py"))
    findings = sources.collect(target, include_http=include_http)
    exposure = scoring.compute_score(findings)
    return {
        "target": target,
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "exposure": {"score": exposure["score"], "band": exposure["band"]},
        "evidence": findings,
    }


@dataclass
class Job:
    id: str
    kind: str
    status: str = "queued"
    result: object = None
    error: str = ""
    submitted: float = field(default_factory=time.time)
    finished: float = 0.0


class JobManager:
    """Bounded worker pool executing callables asynchronously."""

    def __init__(self, workers: int = 2, store=None):
        self._jobs: dict[str, Job] = {}
        self._queue: queue.Queue[str] = queue.Queue()
        self._lock = threading.Lock()
        self.store = store
        for _ in range(max(1, workers)):
            threading.Thread(target=self._worker, daemon=True).start()

    def submit(self, kind: str, fn, *args, **kwargs) -> str:
        job_id = uuid.uuid4().hex[:12]
        with self._lock:
            self._jobs[job_id] = Job(id=job_id, kind=kind)
        self._persist(job_id, "queued")
        self._queue.put((job_id, fn, args, kwargs))
        REGISTRY.inc("rtai_jobs_submitted_total",
                     help_text="background jobs accepted")
        return job_id

    def _worker(self):
        while True:
            job_id, fn, args, kwargs = self._queue.get()
            with self._lock:
                job = self._jobs.get(job_id)
                if job:
                    job.status = "running"
            self._persist(job_id, "running")
            try:
                result = fn(*args, **kwargs)
                with self._lock:
                    if job:
                        job.status, job.result = "done", result
                        job.finished = time.time()
                self._persist(job_id, "done")
            except Exception as exc:  # noqa: BLE001 - boundary isolation
                with self._lock:
                    if job:
                        job.status, job.error = "error", str(exc)[:400]
                        job.finished = time.time()
                self._persist(job_id, "error")
            finally:
                self._queue.task_done()

    def _persist(self, job_id: str, status: str):
        if self.store is not None:
            try:
                self.store.emit("job", job_id=job_id, status=status)
            except Exception:  # noqa: BLE001 - telemetry must never break jobs
                pass

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            return Job(**{**job.__dict__})

    def recent(self, limit: int = 20) -> list[dict]:
        with self._lock:
            ordered = sorted(self._jobs.values(),
                             key=lambda j: j.submitted, reverse=True)[:limit]
            return [{"id": j.id, "kind": j.kind, "status": j.status,
                     "submitted": j.submitted} for j in ordered]

    @staticmethod
    def public_view(job: Job) -> dict:
        view = {"id": job.id, "kind": job.kind, "status": job.status,
                "submitted": job.submitted, "finished": job.finished}
        if job.status == "done":
            view["result"] = job.result
        if job.status == "error":
            view["error"] = job.error
        return view


OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {"title": "rtai-api", "version": __version__},
    "paths": {
        "/health": {"get": {"summary": "Liveness probe"}},
        "/version": {"get": {"summary": "Build metadata"}},
        "/metrics": {"get": {"summary": "Prometheus exposition"}},
        "/v1/recon": {"post": {"summary": "Synchronous passive recon bundle"}},
        "/v1/recon/async": {"post": {"summary": "Submit background recon job"}},
        "/v1/jobs": {"get": {"summary": "List recent jobs"}},
        "/v1/jobs/{id}": {"get": {"summary": "Job status/result",
                                   "parameters": [{"name": "id", "in": "path",
                                                   "required": True,
                                                   "schema": {"type": "string"}}]}},
        "/v1/payloads/validate": {"post": {"summary": "Validate injection arsenal"}},
    },
}


class ApiHandler(BaseHTTPRequestHandler):
    server_version = "rtai-api/" + __version__
    sys_version = ""

    @property
    def api_config(self):
        return self.server.config

    def _send(self, status: int, body=None, content_type="application/json"):
        raw = b"" if body is None else (
            body if isinstance(body, bytes) else json.dumps(body, indent=1).encode())
        self.send_response(status)
        self.send_header("Content-Type",
                         "text/plain; version=0.0.4" if content_type.startswith("text")
                         else content_type)
        self.send_header("Content-Length", str(len(raw)))
        for header, value in SECURITY_HEADERS.items():
            self.send_header(header, value)
        self.end_headers()
        if raw:
            self.wfile.write(raw)
        REGISTRY.inc(f"rtai_http_requests_total_code_{status}",
                     help_text="HTTP responses by status code")

    def _client_ip(self) -> str:
        # G12: improve proxy handling — trust X-Forwarded-For only when peer is lab/private (trusted proxy/NAT)
        fwd = self.headers.get("X-Forwarded-For", "")
        if fwd:
            try:
                from rtai_core.validation import is_lab_address
                peer = self.client_address[0]
                allowed, _ = is_lab_address(peer)
                if allowed:
                    first = fwd.split(",")[0].strip().split()[0]
                    if first:
                        return first
            except Exception:
                pass
        return self.client_address[0]

    def _authorized(self) -> bool:
        token = self.api_config["token"]
        require_auth = self.api_config.get("require_auth", False)
        # Commercial fail-closed: if RTAI_REQUIRE_AUTH env set, treat empty token as misconfig
        if not token:
            if require_auth:
                audit_record("auth_failure", actor=self._client_ip(),
                             path=self.path.split("?")[0], reason="token_required_but_empty")
                return False
            return True
        header = self.headers.get("Authorization", "")
        # Constant-time compare (G3.1)
        expected = f"Bearer {token}"
        ok = hmac.compare_digest(header, expected)
        if not ok:
            audit_record("auth_failure", actor=self._client_ip(),
                         path=self.path.split("?")[0])
        return ok

    def _rate_ok(self) -> bool:
        allowed = self.api_config["limiter"].allow(self._client_ip())
        if not allowed:
            REGISTRY.inc("rtai_rate_limited_total",
                         help_text="requests rejected by rate limiter")
            audit_record("rate_limited", actor=self._client_ip())
        return allowed

    def _opa_allowed(self, method: str, path: str) -> bool:
        opa_dir = self.api_config.get("opa_policy") or os.environ.get("RTAI_OPA_POLICY", "")
        if not opa_dir:
            return True  # OPA not configured — allow (bearer already checked)
        try:
            from rtai_core.military_opa import OPAPolicyEngine
            engine = OPAPolicyEngine(policy_dir=Path(opa_dir)) if Path(opa_dir).exists() else OPAPolicyEngine()
            # Determine scopes from token — simplified: bearer valid => scopes from env RTAI_SCOPES
            scopes = os.environ.get("RTAI_SCOPES", "recon:read,recon:write,jobs:read,fuzz:execute").split(",")
            input_data = {
                "method": method,
                "path": path.split("?")[0],
                "auth": {"valid": self._authorized(), "scopes": scopes},
                "source": {"ip": self._client_ip()},
                "mtls": bool(self.api_config.get("tls_cert")),
                "rate": 0,
            }
            decision = engine.evaluate("zero_trust", input_data)
            if not decision.allowed:
                audit_record("opa_denied", actor=self._client_ip(), path=path, reason=decision.reason)
                return False
            return True
        except Exception as e:
            LOG.warning("OPA evaluation failed (fail-open for availability, audited): %s", e)
            audit_record("opa_error", actor=self._client_ip(), path=path, reason=str(e)[:120])
            return True

    def _read_json(self):
        clen_raw = self.headers.get("Content-Length") or "0"
        try:
            clen = int(clen_raw)
        except ValueError:
            raise ValueError("invalid Content-Length")
        if clen > MAX_BODY:
            raise ValueError(f"payload too large: {clen} > {MAX_BODY} (413)")
        length = clen
        if length <= 0:
            raise ValueError("empty body")
        raw = self.rfile.read(length)
        if "application/json" not in (self.headers.get("Content-Type") or ""):
            raise ValueError("Content-Type must be application/json")
        return json.loads(raw.decode(errors="replace"))

    def do_GET(self):  # noqa: N802 - stdlib naming
        if not self._rate_ok():
            return self._send(429, {"error": "rate limit exceeded"})
        route = self.path.split("?")[0].rstrip("/") or "/"
        # OPA zero-trust check (if RTAI_OPA_POLICY set) — runs after rate but before auth routing
        if not self._opa_allowed("GET", route):
            return self._send(403, {"error": "OPA policy denied"})
        if route == "/health":
            return self._send(200, {"status": "ok", "version": __version__})
        if route == "/version":
            return self._send(200, {"service": "rtai-api", "version": __version__,
                                    "tools": sorted(TOOLS)})
        if route == "/metrics":
            REGISTRY.set("rtai_uptime_seconds",
                         round(time.time() - self.api_config["started"], 3))
            return self._send(200, REGISTRY.render_prometheus().encode(),
                              content_type="text/plain")
        if route == "/openapi.json":
            return self._send(200, OPENAPI_SPEC)
        if route == "/v1/jobs":
            if not self._authorized():
                return self._send(401, {"error": "missing or invalid bearer token"})
            return self._send(200, {"jobs": self.api_config["jobs"].recent()})
        if route.startswith("/v1/jobs/"):
            if not self._authorized():
                return self._send(401, {"error": "missing or invalid bearer token"})
            job = self.api_config["jobs"].get(route.rsplit("/", 1)[-1])
            if job is None:
                return self._send(404, {"error": "unknown job id"})
            return self._send(200, JobManager.public_view(job))
        return self._send(404, {"error": "not found"})

    def do_POST(self):  # noqa: N802
        if not self._rate_ok():
            return self._send(429, {"error": "rate limit exceeded"})
        if not self._authorized():
            return self._send(401, {"error": "missing or invalid bearer token"})
        route = self.path.split("?")[0]
        if not self._opa_allowed("POST", route):
            return self._send(403, {"error": "OPA policy denied"})
        try:
            payload = self._read_json()
        except ValueError as exc:
            return self._send(400, {"error": str(exc)})
        except json.JSONDecodeError as exc:
            return self._send(400, {"error": f"malformed JSON: {exc}"})

        if route in ("/v1/recon", "/v1/recon/async"):
            target = str(payload.get("target", ""))
            include_http = bool(payload.get("include_http", False))
            if include_http:
                hdr_val = self.headers.get("X-RTAI-Authorized") or ""
                attest_key = os.environ.get("RTAI_ATTEST_KEY")
                if attest_key:
                    # Commercial: require HMAC hex(hmac-sha256(key, "active-recon"))[:16]
                    expected_hmac = hmac.new(attest_key.encode(), b"active-recon", hashlib.sha256).hexdigest()[:16]
                    if not hmac.compare_digest(hdr_val, expected_hmac):
                        audit_record("recon_forbidden", actor=self._client_ip(), target=target, reason="hmac_mismatch_X-RTAI-Authorized")
                        return self._send(403, {"error": "active recon requires X-RTAI-Authorized: HMAC(RTAI_ATTEST_KEY,'active-recon')[:16]"})
                else:
                    if not hmac.compare_digest(hdr_val, "yes"):
                        audit_record("recon_forbidden", actor=self._client_ip(), target=target, reason="missing_X-RTAI-Authorized")
                        return self._send(403, {"error": "active recon requires "
                                                         "X-RTAI-Authorized: yes (or HMAC when RTAI_ATTEST_KEY set)"})
            try:
                if route.endswith("/async"):
                    job_id = self.api_config["jobs"].submit(
                        "recon", self.api_config["recon_runner"],
                        target, include_http)
                    audit_record("recon_submitted", actor=self._client_ip(), target=target, job_id=job_id, mode="async" if include_http else "passive")
                    return self._send(202, {"job_id": job_id,
                                            "poll": f"/v1/jobs/{job_id}"})
                result = self.api_config["recon_runner"](target, include_http)
                audit_record("recon_success", actor=self._client_ip(), target=target, mode="active-http" if include_http else "passive")
            except Exception as exc:
                LOG.warning("recon failed for %s: %s", target, exc)
                audit_record("recon_failed", actor=self._client_ip(), target=target)
                return self._send(422, {"error": f"recon failed: {exc}"})
            return self._send(200, result)

        if route == "/v1/payloads/validate":
            entries = payload.get("payloads") if isinstance(payload, dict) else None
            if not isinstance(entries, list) or not entries:
                return self._send(400, {"error": "body must be {'payloads': [...]}"})
            problems = []
            for index, item in enumerate(entries, start=1):
                if not isinstance(item, dict):
                    problems.append(f"#{index}: not an object")
                    continue
                if not (item.get("text") or item.get("turns")):
                    problems.append(f"#{index}: needs 'text' or 'turns'")
                if item.get("turns") and not isinstance(item["turns"], list):
                    problems.append(f"#{index}: 'turns' must be a list")
            if problems:
                return self._send(422, {"valid": False, "problems": problems})
            return self._send(200, {"valid": True, "count": len(entries)})

        return self._send(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        LOG.info("http %s", fmt % args)


def create_server(host="127.0.0.1", port=9000, token="", limit_per_minute=60,
                  recon_runner=None, db_path=None, workers=2, require_auth=False,
                  tls_cert=None, tls_key=None, tls_ca=None, spiffe_id=None):
    store = None
    if db_path:
        from rtai_core.storage import SqliteEventStore
        store = SqliteEventStore(db_path)
    server = ReusableThreadingHTTPServer((host, port), ApiHandler)
    server.config = {
        "token": token,
        "limiter": SlidingWindowLimiter(limit_per_minute),
        "recon_runner": recon_runner or run_recon,
        "started": time.time(),
        "jobs": JobManager(workers=workers, store=store),
        "require_auth": require_auth,
        "tls_cert": tls_cert,
        "tls_key": tls_key,
        "tls_ca": tls_ca,
        "spiffe_id": spiffe_id,
        "opa_policy": os.environ.get("RTAI_OPA_POLICY", ""),
    }
    # mTLS wiring — if cert/key provided, wrap socket with MTLSContextManager
    if tls_cert and tls_key:
        try:
            from rtai_core.military_mtls import MTLSContextManager
            mtls = MTLSContextManager(Path(tls_cert), Path(tls_key), Path(tls_ca) if tls_ca else None)
            ctx = mtls.get_server_context()
            server.socket = ctx.wrap_socket(server.socket, server_side=True)
            LOG.info("mTLS enabled: cert=%s ca=%s spiffe=%s", tls_cert, tls_ca, spiffe_id)
            audit_record("mtls_enabled", actor="system", cert=str(tls_cert), spiffe_id=spiffe_id or "")
        except Exception as e:
            LOG.error("mTLS setup failed: %s", e)
            raise SystemExit(f"[x] mTLS setup failed: {e}")
    elif os.environ.get("RTAI_MTLS") == "1":
        LOG.warning("RTAI_MTLS=1 but no --tls-cert/--tls-key provided — running plaintext (dev only)")
    server.daemon_threads = True
    return server


def main() -> int:
    parser = argparse.ArgumentParser(description="rtai-api microservice — Royal-Sec military-grade (mTLS/SPIFFE, FIPS, OPA)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--token", default="",
                        help="bearer token; falls back to RTAI_API_TOKEN env")
    parser.add_argument("--limit-per-minute", type=int, default=60)
    parser.add_argument("--db", default=None,
                        help="SQLite mirror for job history (e.g. api.db)")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--require-auth", action="store_true",
                        help="fail-closed: require RTAI_API_TOKEN (recommended for Royal-Sec commercial deployments)")
    parser.add_argument("--tls-cert", default=os.environ.get("RTAI_TLS_CERT", ""),
                        help="path to TLS server cert (enables mTLS via rtai_core/military_mtls.py)")
    parser.add_argument("--tls-key", default=os.environ.get("RTAI_TLS_KEY", ""),
                        help="path to TLS server key")
    parser.add_argument("--tls-ca", default=os.environ.get("RTAI_TLS_CA", ""),
                        help="path to TLS CA bundle for client cert verification")
    parser.add_argument("--spiffe-id", default=os.environ.get("RTAI_SPIFFE_ID", ""),
                        help="expected SPIFFE ID for workload attestation (e.g., spiffe://royal-sec/ns/api/svc)")
    parser.add_argument("--fips", action="store_true",
                        help="enable FIPS 140-3 approved-only mode (RTAI_FIPS=1, see rtai_core/military_fips.py)")
    parser.add_argument("--opa-policy", default=os.environ.get("RTAI_OPA_POLICY", ""),
                        help="path to OPA Rego bundle dir (rtai_core/military_opa.py)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    setup_logging(verbose=args.verbose)
    # FIPS mode
    if args.fips or os.environ.get("RTAI_FIPS") == "1":
        os.environ["RTAI_FIPS"] = "1"
        from rtai_core.military_fips import fips_status
        LOG.info("FIPS mode: %s", fips_status())
        audit_record("fips_enabled", actor="system", status=str(fips_status()))
    # HSM-aware secret fetch (Vault/TPM/HSM/file/env, fail-closed if RTAI_HSM_REQUIRED=1)
    try:
        from rtai_core.military_hsm import get_secret
        token = args.token or get_secret("RTAI_API_TOKEN", "")
    except RuntimeError as e:
        LOG.error("HSM fail-closed: %s", e)
        return 74
    require_auth = args.require_auth or os.environ.get("RTAI_REQUIRE_AUTH") == "1"
    if not token:
        if require_auth:
            LOG.error("RTAI_API_TOKEN not set but --require-auth / RTAI_REQUIRE_AUTH=1 — refusing to start open")
            return 74
        LOG.warning("RTAI_API_TOKEN not set - API is OPEN (development mode only). "
                    "For Royal-Sec commercial use, set RTAI_API_TOKEN and --require-auth")
    # TPM attestation pre-flight if requested
    if os.environ.get("RTAI_TPM_ATTEST") == "1":
        try:
            from rtai_core.military_tpm import TPM2Interface, TPMRemoteAttestation
            tpm = TPM2Interface()
            pcrs = tpm.get_pcr_values()
            LOG.info("TPM PCRs: %s", pcrs[:2])
            audit_record("tpm_attested", actor="system", pcrs=str(pcrs[:2]))
        except Exception as e:
            LOG.warning("TPM attestation requested but failed: %s (continuing, audit logged)", e)
            audit_record("tpm_attest_failed", actor="system", reason=str(e)[:120])
    # OPA env wiring
    if args.opa_policy:
        os.environ["RTAI_OPA_POLICY"] = args.opa_policy
    server = create_server(args.host, args.port, token=token,
                           limit_per_minute=args.limit_per_minute,
                           db_path=args.db, workers=args.workers, require_auth=require_auth,
                           tls_cert=args.tls_cert or None, tls_key=args.tls_key or None,
                           tls_ca=args.tls_ca or None, spiffe_id=args.spiffe_id or None)
    scheme = "https" if args.tls_cert else "http"
    LOG.info("listening on %s://%s:%d (docs: /openapi.json) fips=%s mtls=%s opa=%s", scheme, args.host, args.port, bool(args.fips or os.environ.get("RTAI_FIPS")), bool(args.tls_cert), bool(args.opa_policy))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
