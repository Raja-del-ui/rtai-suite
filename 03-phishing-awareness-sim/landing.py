"""Click-tracking landing server for phishing awareness campaigns (lab/loopback use).

Usage:
    python landing.py --links out/<run>/campaign_links.csv --company "Acme Corp"

Flow: recipient clicks the unique tokenized link -> click logged to clicks.jsonl ->
browser shows a friendly "this was a simulation" education page with red-flag recap.
"""

import argparse
import csv
import datetime as dt
import json
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from rtai_core.audit import actor_from_env, record as audit_record
from rtai_core.validation import assert_lab_address

LOCK = threading.Lock()
TOKENS = {}

EDUCATION_PAGE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Security Awareness - Simulation Result</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;background:#f4f6f8;margin:0}}
.card{{max-width:640px;margin:8vh auto;background:#fff;border-radius:12px;padding:32px;
box-shadow:0 4px 20px rgba(0,0,0,.08)}} h1{{color:#b3541e;font-size:22px}}
li{{margin:.5em 0}} .ok{{color:#2e7d32}}</style></head>
<body><div class="card">
<h1>Good instinct to pause - this was an authorized phishing simulation</h1>
<p>Hello {recipient},</p>
<p>You clicked a link in the <b>{template}</b> simulation sent by your security team
for <b>{company}</b>. No credentials were collected and nothing was installed.</p>
<h2>Red flags this email contained</h2>
<ul>{red_flags}</ul>
<p class="ok"><b>What to do next:</b> report suspicious mail with the Report Phish button,
and when in doubt, verify via a known-good channel.</p>
<p style="color:#888;font-size:12px">Questions? Contact your security awareness team.</p>
</div></body></html>"""

MISSING_PAGE = """<!DOCTYPE html><html><body style="font-family:sans-serif">
<h2>Unknown or expired simulation link.</h2>
<p>If you believe this is an error, contact your security team.</p></body></html>"""


def load_links(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            TOKENS[row["token"]] = {
                "recipient": row["recipient"],
                "template": row["template"],
                "file": row.get("file", ""),
            }


class LandingHandler(BaseHTTPRequestHandler):
    def _html(self, text, status=200):
        body = text.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/l/"):
            token = parsed.path[len("/l/"):].split("/")[0]
            info = TOKENS.get(token)
            self._log("click" if info else "unknown_token", token=token)
            if not info:
                self._html(MISSING_PAGE, status=404)
                return
            red_items = "".join(f"<li>{rf}</li>" for rf in RED_FLAGS_BY_TEMPLATE.get(
                info["template"], ["urgency pressure", "lookalike sender domain",
                                   "link does not match its label"]))
            page = EDUCATION_PAGE.format(recipient=info["recipient"],
                                         template=info["template"],
                                         company=self.server.company,
                                         red_flags=red_items)
            self._html(page)
        elif parsed.path == "/health":
            self._log("health")
            self._html("<h3>landing server healthy</h3>")
        else:
            self._log("other_path", path=parsed.path)
            self._html(MISSING_PAGE, status=404)

    def do_POST(self):
        length = min(int(self.headers.get("Content-Length") or 0), 4096)
        if length:
            self.rfile.read(length)
        self._log("post_blocked", path=self.path)
        self._html(MISSING_PAGE, status=404)

    def _log(self, event, **extra):
        row = {"ts": dt.datetime.now().isoformat(timespec="seconds"),
               "event": event, "ip": self.client_address[0],
               "ua": self.headers.get("User-Agent"), **extra}
        with LOCK:
            with open(self.server.click_log, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
        print(f"[{row['ts']}] {event:14} {row.get('token', ''):16} {extra}")

def log_message(self, msg):
        print(f"[landing] {msg}")
class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


RED_FLAGS_BY_TEMPLATE = {}


def main():
    parser = argparse.ArgumentParser(description="Awareness-campaign landing server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--links", required=True, help="campaign_links.csv from campaign.py")
    parser.add_argument("--log", default="clicks.jsonl")
    parser.add_argument("--company", default="your organization")
    parser.add_argument("--allow-public", action="store_true",
                        help="allow binding to non-lab address (explicit + audited)")
    args = parser.parse_args()

    # Lab-only guard (G6)
    try:
        if args.allow_public:
            try:
                audit_record("landing_allow_public", actor=actor_from_env(), host=args.host)
            except Exception:
                pass
            print(f"[!] WARNING: --allow-public landing on {args.host} without lab guard")
        else:
            assert_lab_address(args.host)
    except ValueError as exc:
        try:
            audit_record("landing_refused", actor=actor_from_env(), host=args.host, reason=str(exc)[:120])
        except Exception:
            pass
        print(f"[x] {exc}")
        return 74

    load_links(args.links)
    print(f"[*] loaded {len(TOKENS)} tokenized links")

    try:
        import templates as campaign_templates
        for key, tpl in campaign_templates.TEMPLATES.items():
            RED_FLAGS_BY_TEMPLATE[key] = [rf["flag"] for rf in tpl["red_flags"]]
    except ImportError:
        pass

    server = ReusableThreadingHTTPServer((args.host, args.port), LandingHandler)
    server.company = args.company
    server.click_log = args.log
    print(f"[*] landing page on http://{args.host}:{args.port}/l/<token> "
          f"(clicks -> {args.log})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        print("\n[*] stopped")


if __name__ == "__main__":
    main()
