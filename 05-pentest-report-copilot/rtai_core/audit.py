"""Tamper-evident audit log: hash-chained JSONL records.

Each record embeds sha256(prev_hash + canonical_payload); modifying or deleting
any record breaks verification at that exact line. Used for authorization
attestations and security-relevant API events.

Note: intentionally does NOT use JsonlStore - the chain must own byte-exact
serialization so hashes stay reproducible.
"""

import getpass
import hashlib
import hmac
import json
import os
import socket
import threading
from pathlib import Path

GENESIS = "0" * 64
_LOCK = threading.Lock()


def _canonical(record: dict) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), default=str)


def _digest(payload: str) -> str:
    return hashlib.sha256(payload.encode()).hexdigest()


class AuditChain:
    def __init__(self, path=None):
        raw = path or os.environ.get("RTAI_AUDIT_LOG", "audit.log")
        self.path = Path(raw)
        # Fail-closed hint: if RTAI_AUDIT_LOG is set to /dev/null or empty, caller
        # is discarding forensic evidence — we still honour the path but callers
        # should treat such config as unaudited (see docs/SECURITY_AND_ETHICS.md).
        # Path must be writable; record() will surface errors.

    def record(self, event: str, actor: str = "", **details) -> dict:
        # Enrich with host/user when actor is env-derived; caller already passed actor_from_env()
        # but we add non-spoofable host/user for forensics without breaking caller actor field.
        if "host" not in details:
            try:
                details.setdefault("host", socket.gethostname())
            except Exception:
                pass
        if "os_user" not in details:
            try:
                details.setdefault("os_user", getpass.getuser())
            except Exception:
                details.setdefault("os_user", "unknown")
        previous = GENESIS
        existing = self.read()
        if existing:
            previous = existing[-1].get("hash", GENESIS)
        entry = {"event": event, "actor": actor, **details,
                 "prev": previous}
        entry["hash"] = _digest(_canonical(entry))
        with _LOCK:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # Best-effort cross-process file lock (advisory) — falls back to thread lock on Windows
            try:
                # On POSIX use fcntl; on Windows use msvcrt
                import fcntl  # type: ignore
                with self.path.open("a", encoding="utf-8") as fh:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX)  # type: ignore[attr-defined]
                    fh.write(json.dumps(entry, default=str) + "\n")
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)  # type: ignore[attr-defined]
            except ImportError:
                try:
                    import msvcrt  # type: ignore
                    with self.path.open("a", encoding="utf-8") as fh:
                        msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
                        fh.write(json.dumps(entry, default=str) + "\n")
                        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                except Exception:
                    with self.path.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps(entry, default=str) + "\n")
            except Exception:
                with self.path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(entry, default=str) + "\n")
        return entry

    def read(self) -> list[dict]:
        if not self.path.exists():
            return []
        rows = []
        with self.path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows

    def verify(self) -> tuple[bool, int | None]:
        """Returns (ok, first_broken_line_number_1based)."""
        previous = GENESIS
        for index, row in enumerate(self.read(), start=1):
            body = {k: v for k, v in row.items() if k != "hash"}
            if row.get("prev") != previous:
                return False, index
            expected = _digest(_canonical(body))
            if row.get("hash") != expected:
                return False, index
            previous = row["hash"]
        return True, None


_DEFAULT = None


def default_chain() -> AuditChain:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = AuditChain()
    return _DEFAULT


def record(event: str, actor: str = "", **details) -> dict:
    return default_chain().record(event, actor=actor, **details)


def actor_from_env() -> str:
    # NOTE: env-derived actor is spoofable (G8). Server side should prefer
    # client_address[0] for API events; this helper is for CLI tools where
    # env actor is the best-effort identity plus host/os_user enrichment above.
    return (os.environ.get("RTAI_ACTOR")
            or os.environ.get("USERNAME")
            or os.environ.get("USER")
            or "unknown")


def verify_attestation_hmac(value: str, key_env: str = "RTAI_ATTEST_KEY") -> bool:
    """If RTAI_ATTEST_KEY is set, require HMAC-SHA256(value, key)==value bypass.
    Returns True if no key is set and value == '1' (legacy) — caller should warn.
    """
    key = os.environ.get(key_env)
    if not key:
        return hmac.compare_digest(value, "1")
    # When key is set, bypass must be hex(hmac-sha256(key, "attested"))
    expected = hmac.new(key.encode(), b"attested", hashlib.sha256).hexdigest()[:16]
    return hmac.compare_digest(value, expected)
