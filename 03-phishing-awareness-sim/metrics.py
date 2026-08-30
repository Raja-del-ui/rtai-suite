"""Campaign metrics dashboard from click telemetry.

Usage:
    python metrics.py --links out/<run>/campaign_links.csv --clicks clicks.jsonl
"""

import argparse
import csv
import datetime as dt
import json
import sys


def load_links(path):
    links = {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            links[row["token"]] = {"recipient": row["recipient"], "template": row["template"]}
    return links


def load_clicks(path, tokens):
    clicked = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            token = row.get("token")
            if row.get("event") == "click" and token in tokens and token not in clicked:
                clicked[token] = row["ts"]
    return clicked


def build_metrics(tokens, clicked):
    total = len(tokens)
    clicks = len(clicked)
    by_template = {}
    for token, info in tokens.items():
        bucket = by_template.setdefault(info["template"], {"sent": 0, "clicked": 0})
        bucket["sent"] += 1
        if token in clicked:
            bucket["clicked"] += 1
    clickers = sorted(
        ({"recipient": tokens[t]["recipient"], "template": tokens[t]["template"],
          "clicked_at": ts} for t, ts in clicked.items()),
        key=lambda x: x["clicked_at"])
    return {
        "generated": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_sent": total,
        "total_clicked": clicks,
        "click_rate_pct": round(100 * clicks / max(total, 1), 1),
        "by_template": dict(sorted(by_template.items())),
        "clickers": clickers,
    }


def render_html(metrics):
    max_clicked = max((b["clicked"] for b in metrics["by_template"].values()),
                      default=0) or 1
    rows = []
    for template, bucket in sorted(metrics["by_template"].items()):
        rate = round(100 * bucket["clicked"] / max(bucket["sent"], 1), 1)
        width = round(100 * bucket["clicked"] / max_clicked, 1)
        color = "#d84315" if rate >= 30 else ("#f9a825" if rate >= 15 else "#2e7d32")
        rows.append(
            f"<tr><td>{template}</td><td>{bucket['sent']}</td>"
            f"<td><div class=\"bar\" style=\"width:{max(width, 4)}%\">"
            f"<span style=\"background:{color}\">{bucket['clicked']}</span></div></td>"
            f"<td class='rate' style='color:{color}'>{rate}%</td></tr>")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Phishing Simulation Metrics</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#f4f6f8;margin:0;color:#222}}
header{{background:#1f2430;color:#fff;padding:20px 28px}}
main{{max-width:760px;margin:0 auto;padding:24px}}
.card{{display:flex;gap:18px;margin-bottom:20px}}
.kpi{{flex:1;background:#fff;border-radius:10px;padding:16px;text-align:center;
box-shadow:0 2px 10px rgba(0,0,0,.05)}}
.kpi b{{font-size:26px;display:block}}
section{{background:#fff;border-radius:10px;padding:18px 22px;
box-shadow:0 2px 10px rgba(0,0,0,.05);margin-bottom:16px}}
table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid #eceff1;font-size:14px;text-align:left}}
.bar{{background:#eceff1;border-radius:6px;height:18px;min-width:40px;position:relative}}
.bar span{{position:absolute;left:6px;top:0;color:#fff;font-size:11px;line-height:18px;
border-radius:4px;padding:0 8px}}
.rate{{font-weight:700}}.note{{color:#78909c;font-size:12px}}
</style></head><body>
<header><h1>Phishing Simulation Metrics</h1>
<div style="opacity:.75;font-size:13px">Generated {metrics['generated']} · internal training use only</div>
</header><main>
<div class="card">
<div class="kpi"><b>{metrics['total_sent']}</b>Sent</div>
<div class="kpi"><b>{metrics['total_clicked']}</b>Clicked</div>
<div class="kpi" style="background:#fff3e0"><b>{metrics['click_rate_pct']}%</b>Click rate</div>
</div>
<section><h2>By template</h2>
<table><tr><th>Template</th><th>Sent</th><th>Clicks</th><th>Rate</th></tr>
{''.join(rows)}
</table></section>
<section><h2>Click log</h2>
<table><tr><th>Recipient</th><th>Template</th><th>Clicked at</th></tr>
{''.join(f"<tr><td>{c['recipient']}</td><td>{c['template']}</td><td>{c['clicked_at']}</td></tr>" for c in metrics['clickers']) or '<tr><td colspan=3 class=note>No clicks recorded yet.</td></tr>'}
</table>
<p class="note">Follow up constructively with clickers; never shame publicly.</p>
</section></main></body></html>
"""


def render(metrics):
    lines = [
        "# Phishing Simulation Metrics",
        "",
        f"*Generated {metrics['generated']} - internal training use only.*",
        "",
        "| Sent | Clicked | Click rate |",
        "|---|---|---|",
        f"| {metrics['total_sent']} | {metrics['total_clicked']} | "
        f"**{metrics['click_rate_pct']}%** |",
        "",
        "## By template",
        "",
        "| Template | Sent | Clicked | Rate |",
        "|---|---|---|---|",
    ]
    for template, bucket in metrics["by_template"].items():
        rate = round(100 * bucket["clicked"] / max(bucket["sent"], 1), 1)
        lines.append(f"| {template} | {bucket['sent']} | {bucket['clicked']} | {rate}% |")
    lines += ["", "## Click log", ""]
    if metrics["clickers"]:
        lines += ["| Recipient | Template | Clicked at |", "|---|---|---|"]
        lines += [f"| {c['recipient']} | {c['template']} | {c['clicked_at']} |"
                  for c in metrics["clickers"]]
    else:
        lines.append("_No clicks recorded yet._")
    lines += ["", "## Trainer notes", "",
              "- Follow up individually with clickers; keep tone constructive.",
              "- Repeat the campaign after refresher training to measure improvement."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Simulation metrics dashboard")
    parser.add_argument("--links", required=True)
    parser.add_argument("--clicks", default="clicks.jsonl")
    parser.add_argument("--out", default="metrics.md")
    parser.add_argument("--html", dest="html_out", default=None,
                        help="also render an HTML dashboard (e.g. metrics.html)")
    args = parser.parse_args()

    try:
        tokens = load_links(args.links)
    except OSError as exc:
        sys.exit(f"[!] {exc}")
    try:
        clicked = load_clicks(args.clicks, tokens)
    except OSError:
        clicked = {}
        print("[*] no click log found yet - reporting zeros")
    metrics = build_metrics(tokens, clicked)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(render(metrics))
    print(f"[+] metrics -> {args.out} "
          f"(clicks {metrics['total_clicked']}/{metrics['total_sent']} "
          f"= {metrics['click_rate_pct']}%)")
    if args.html_out:
        with open(args.html_out, "w", encoding="utf-8") as fh:
            fh.write(render_html(metrics))
        print(f"[+] html dashboard -> {args.html_out}")


if __name__ == "__main__":
    main()
