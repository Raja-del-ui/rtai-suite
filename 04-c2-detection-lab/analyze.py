"""Beacon telemetry analysis: local statistics + LLM-written detection engineering report.

Usage:
    python analyze.py --log beacons.jsonl --stats-only
    python analyze.py --log beacons.jsonl --out detection_report.md
"""

import argparse
import datetime as dt
import json
import statistics
import sys

from llm_client import ChatClient, LLMError

ANALYST_SYSTEM = (
    "You are a senior detection engineer on the BLUE team. You receive telemetry from a "
    "simulated C2 beacon run in a lab. Produce practical, copy-pasteable detections "
    "(Sigma YAML and a Suricata rule), explain which fields make the beacon detectable, "
    "and note how jitter affects naive interval-based alerts. GitHub-flavoured Markdown."
)


def load_polls(path):
    polls = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("event") == "poll":
                polls.append(row)
    polls.sort(key=lambda r: r["ts"])
    return polls


def compute_stats(polls):
    times = [dt.datetime.fromisoformat(r["ts"]) for r in polls]
    intervals = [(b - a).total_seconds() for a, b in zip(times, times[1:])]
    if not intervals:
        return None
    uas = sorted({r.get("ua") for r in polls if r.get("ua")})
    mean = statistics.mean(intervals)
    stdev = statistics.pstdev(intervals)
    cv = stdev / mean if mean else 0.0
    regularity = 1 / (1 + cv)
    acf1 = _lag1_autocorrelation(intervals)
    stats = {
        "polls": len(polls),
        "intervals": {
            "mean": round(mean, 3),
            "stdev": round(stdev, 3),
            "cv": round(cv, 3),
            "regularity_index": round(regularity, 3),
            "autocorr_lag1": round(acf1, 3) if acf1 is not None else None,
            "min": round(min(intervals), 3),
            "max": round(max(intervals), 3),
            "values": [round(x, 2) for x in intervals],
        },
        "distinct_user_agents": uas,
        "first_seen": polls[0]["ts"],
        "last_seen": polls[-1]["ts"],
        "source_ips": sorted({r["ip"] for r in polls}),
    }
    return stats


def _pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    var_x = sum((x - mx) ** 2 for x in xs)
    var_y = sum((y - my) ** 2 for y in ys)
    denom = (var_x * var_y) ** 0.5
    return cov / denom if denom else 0.0


def _lag1_autocorrelation(intervals):
    if len(intervals) < 4:
        return None
    value = _pearson(intervals[:-1], intervals[1:])
    return value


def histogram(intervals, buckets=12):
    if not intervals:
        return ""
    lo, hi = min(intervals), max(intervals)
    width = max((hi - lo) / buckets, 1e-9)
    counts = [0] * buckets
    for value in intervals:
        index = min(buckets - 1, int((value - lo) / width))
        counts[index] += 1
    peak = max(counts) or 1
    lines = []
    for i, count in enumerate(counts):
        bar = "#" * (40 * count // peak)
        start = lo + i * width
        lines.append(f"{start:6.1f}-{start + width:6.1f}s | {bar} {count}")
    return "\n".join(lines)


def build_report(stats, client):
    prompt = f"""LAB BEACON TELEMETRY (JSON):
{json.dumps(stats, indent=1)[:6000]}

Interpretation aids: regularity_index = 1/(1+cv), so ~1.0 means metronomic beaconing;
autocorr_lag1 near 0 means intervals are independent (pure jitter).

Write a detection-engineering report with EXACTLY these sections:

## Beacon Pattern Analysis
## Estimated Configuration
(inferred sleep range and jitter % from the interval data)
## Indicators of Compromise
(paths, cookie pattern, UA set — as a bullet IOC list)
## Suggested Detections
A complete Sigma rule in YAML plus one Suricata rule, both copy-pasteable.
## Why Jitter Defeats Naive Alerts
Explain using the observed stdev, cv and autocorrelation."""
    return client.chat(prompt, ANALYST_SYSTEM)


def compare_runs(stats_a, stats_b, label_a, label_b):
    def row(metric, key="intervals"):
        va = stats_a[key]
        vb = stats_b[key]
        if isinstance(va, dict):
            return metric, va.get("mean"), vb.get("mean")
        return metric, va, vb

    lines = [
        f"Comparing {label_a} vs {label_b}",
        "",
        "| Metric | " + label_a + " | " + label_b + " |",
        "|---|---|---|",
    ]
    for name in ["polls", "distinct_user_agents"]:
        lines.append(f"| {name} | {stats_a[name]} | {stats_b[name]} |")
    for metric in ["mean", "stdev", "cv", "regularity_index", "autocorr_lag1"]:
        lines.append(f"| interval.{metric} | "
                     f"{stats_a['intervals'][metric]} | {stats_b['intervals'][metric]} |")
    verdict = []
    ra, rb = stats_a["intervals"]["regularity_index"], stats_b["intervals"]["regularity_index"]
    if abs(ra - rb) > 0.15:
        more = label_a if ra > rb else label_b
        verdict.append(f"{more} is significantly MORE regular -> easier to detect by timing.")
    ua_a, ua_b = len(stats_a["distinct_user_agents"]), len(stats_b["distinct_user_agents"])
    if ua_a != ua_b:
        verdict.append(f"{label_a} used {ua_a} distinct UAs vs {ua_b} for {label_b}.")
    lines += ["", "## Takeaways"] + [f"- {v}" for v in verdict or ["Profiles look similar."]]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="C2 beacon telemetry analyzer")
    parser.add_argument("--log", default="beacons.jsonl")
    parser.add_argument("--out", default="detection_report.md")
    parser.add_argument("--stats-only", action="store_true")
    parser.add_argument("--compare", nargs=2, metavar=("LOG_A", "LOG_B"),
                        help="compare two beacon runs statistically (no LLM)")
    parser.add_argument("--provider", choices=["openai", "anthropic", "ollama"])
    parser.add_argument("--model")
    args = parser.parse_args()

    if args.compare:
        stats_pair = []
        for log_path in args.compare:
            polls = load_polls(log_path)
            stats_pair.append(compute_stats(polls))
        if not all(stats_pair):
            sys.exit("[!] need at least two poll events in each log")
        print(compare_runs(stats_pair[0], stats_pair[1], *args.compare))
        return

    try:
        polls = load_polls(args.log)
    except OSError as exc:
        sys.exit(f"[!] {exc} (run listener.py + beacon.py first)")
    stats = compute_stats(polls)
    if not stats:
        sys.exit("[!] fewer than two poll events recorded — nothing to analyze")

    intervals = stats["intervals"]
    print(f"[*] polls={stats['polls']} mean={intervals['mean']}s stdev={intervals['stdev']}s "
          f"cv={intervals['cv']} regularity={intervals['regularity_index']} "
          f"autocorr1={intervals['autocorr_lag1']} UAs={len(stats['distinct_user_agents'])}")
    print("\nInterval distribution:")
    print(histogram(intervals["values"]))

    if args.stats_only:
        print(json.dumps(stats, indent=2))
        return

    try:
        client = ChatClient(provider=args.provider, model=args.model)
    except LLMError as exc:
        sys.exit(f"[!] {exc}")
    print(f"\n[*] writing detection report via {client.provider}:{client.model} ...")
    report = build_report(stats, client)

    header = (f"# C2 Beacon Detection Report\n\n*Generated {dt.datetime.now():%Y-%m-%d %H:%M} "
              f"from `{args.log}` ({stats['polls']} polls)*\n\n---\n\n")
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(header + report)
    print(f"[+] saved -> {args.out}")


if __name__ == "__main__":
    main()
