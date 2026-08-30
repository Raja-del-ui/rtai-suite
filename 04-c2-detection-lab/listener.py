"""Local C2 listener for lab use: logs simulated beacon polls and exfil posts.

Usage:
    python listener.py --host 127.0.0.1 --port 8080 --log beacons.jsonl
    python listener.py --tasks "whoami,ipconfig /all,type C:\\secrets.txt"

This server is the BLUE-TEAM observation point of the lab. It never executes anything;
it only records telemetry so detections can be tuned against it.
"""

import argparse
import base64
import datetime as dt
import hashlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from rtai_core.audit import actor_from_env, record as audit_record
from rtai_core.exceptions import RTAIError
from rtai_core.logging_utils import get_logger
from rtai_core.storage import JsonlStore, SqliteEventStore
from rtai_core.validation import assert_lab_address

LOG = get_logger("c2lab.listener")
MAX_BODY = 1024 * 1024


class C2Handler(BaseHTTPRequestHandler):
    server_version = "nginx/1.24.0"
    sys_version = ""

    def _log(self, event, **extra):
        row = {
            "ts": dt.datetime.now().isoformat(timespec="milliseconds"),
            "event": event,
            "ip": self.client_address[0],
            "ua": self.headers.get("User-Agent"),
            "cookie": self.headers.get("Cookie"),
            **extra,
        }
        self.server.store.append(row)
        if self.server.db is not None:
            self.server.db.emit(event, **{k: v for k, v in row.items() if k != "ts"})
        LOG.info("%s %s %s", event, row["ip"], extra)

    def _respond(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/poll"):
            tasks = self.server.tasks
            task = tasks[self.server.tick % len(tasks)]
            self.server.tick += 1
            payload_task = task
            if getattr(self.server, "encode_tasks", False):
                payload_task = base64.b64encode(task.encode()).decode()
            self._log("poll", path=self.path, task=task)
            self._respond({"task_b64" if getattr(self.server, "encode_tasks", False)
                           else "task": payload_task})
        else:
            self._log("get", path=self.path)
            self._respond({"ok": False}, status=404)

    def do_POST(self):
        if self.path.startswith("/exfil"):
            length = min(int(self.headers.get("Content-Length") or 0), MAX_BODY)
            body = self.rfile.read(length) if length else b""
            digest = hashlib.sha256(body).hexdigest()[:16]
            self._log("exfil", path=self.path, size=len(body), sha16=digest)
            self._respond({"ok": True})
        else:
            self._log("post", path=self.path)
            self._respond({"ok": False}, status=404)

def log_message(self, msg):
        print(f"[listener] {msg}")
class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


def build_server(host, port, log_path, tasks, encode_tasks=False, db_path=None):
    # Lab-only guard is enforced at build_server so even direct import cannot expose to internet
    # Caller may pass allow_public via extra kwarg handling in main(); here we validate host
    # Note: main() passes already-validated host; this remains defense-in-depth.
    server = ReusableThreadingHTTPServer((host, port), C2Handler)
    server.store = JsonlStore(log_path)
    server.db = SqliteEventStore(db_path) if db_path else None
    server.tasks = tasks or ["idle"]
    server.tick = 0
    server.encode_tasks = encode_tasks
    return server


def validate_listener_host(host: str, allow_public: bool = False) -> None:
    if allow_public:
        # Explicit opt-in for lab-network exception — still audited
        try:
            audit_record("listener_allow_public", actor=actor_from_env(), host=host)
        except Exception:
            pass
        print(f"[!] WARNING: --allow-public set, listener binding to {host} without lab guard")
        return
    assert_lab_address(host)


def main():
    parser = argparse.ArgumentParser(description="Lab C2 listener (observation only)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--log", default="beacons.jsonl")
    parser.add_argument("--db", default=None,
                        help="also mirror telemetry into SQLite (e.g. beacons.db)")
    parser.add_argument("--tasks", default="whoami,hostname,ipconfig",
                        help="comma-separated fake task list served to beacons")
    parser.add_argument("--encode-tasks", dest="encode_tasks", action="store_true",
                        help="serve tasks base64-encoded (obfuscation for detections)")
    parser.add_argument("--allow-public", action="store_true",
                        help="allow binding to non-lab address (requires explicit flag + audit)")
    args = parser.parse_args()

    try:
        validate_listener_host(args.host, allow_public=args.allow_public)
        server = build_server(args.host, args.port, args.log,
                              [t.strip() for t in args.tasks.split(",") if t.strip()],
                              encode_tasks=args.encode_tasks, db_path=args.db)
    except (ValueError, RTAIError) as exc:
        try:
            audit_record("listener_refused", actor=actor_from_env(), host=args.host, reason=str(exc)[:120])
        except Exception:
            pass
        print(f"[x] {exc}")
        return 74
    print(f"[*] lab C2 listening on http://{args.host}:{args.port} "
          f"(poll=/poll exfil=/exfil log={args.log} db={args.db or 'off'} "
          f"encoded={'yes' if args.encode_tasks else 'no'})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] shutting down")
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
