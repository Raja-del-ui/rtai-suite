# Project 04 — C2 Detection Lab

**MITRE ATT&CK:** Command and Control (T1071.001, T1043, T1090) — *simulated in a lab*

## Runs Natively on Windows & Kali Linux

Fully standalone: vendored `rtai_core` ships inside this folder; stdlib-only runtime,
100% offline capable.

| OS | One-time setup | Run |
|---|---|---|
| Windows | *(nothing to install)* | `python listener.py` + `python beacon.py --count 12` |
| Kali / Debian | *(nothing to install; venv optional)* | `python3 listener.py` + `python3 beacon.py --count 12` |

A complete, **fully offline** purple-team lab: a local HTTP "C2" listener, a jittered
beacon simulator with UA rotation and chunked exfil, and an AI detection engineer that
turns the recorded telemetry into Sigma + Suricata rules.

```
   beacon.py (implant sim)                listener.py (observation point)
   jittered sleep ── GET /poll ────────▶  logs JSONL telemetry
   random UA       ◀── {"task": ...} ──   serves fake task list only
   exfil chunks    ── POST /exfil ─────▶  hashes, sizes, never stores content
                                             │
   analyze.py ◀── beacons.jsonl              │
        │  interval mean/stdev histogram     │
        ▼                                    ▼
   detection_report.md  ◀──────── LLM (Sigma/Suricata author)
```

## Setup

No dependencies at all — pure standard library.

## Usage (three terminals or background jobs)

```powershell
# terminal 1 — the "victim network" observation point
python listener.py --host 127.0.0.1 --port 8080

# terminal 2 — the simulated implant
python beacon.py --count 12
python beacon.py --profile profile.example.json --count 20

# terminal 3 — analysis
python analyze.py --log beacons.jsonl --stats-only     # offline stats
python analyze.py --log beacons.jsonl                  # + AI detection report
```

## Safety Design

- `assert_lab_host()` refuses any target resolving to a public IP.
- Listener **never executes** returned tasks; beacons print `[sim] would execute` lines only.
- Exfil content is hashed, never stored.

## Talking Points

- Why beacon stdev/jitter defeats naive fixed-interval alerts; how the AI quantifies it.
- Sigma/Suricata authored by an LLM from raw telemetry — human-review workflow.
- Map every artifact to ATT&CK T1071.001 for your writeup.

## v2 Features

- **Timing presets** (`--preset regular|low_slow|bursty|office_hours`) mimicking common
  beaconing families generically - run two presets, then diff them.
- **Schedule-aware evasion** - office-hours preset only beacons weekdays 09:00-17:00,
  sleeping until the window reopens (classic dwell-time tradecraft).
- **Kill switch** (`--kill-after 30`) - implant self-terminates after N minutes,
  simulating a kill date.
- **Encoded task channel** - start the listener with `--encode-tasks`; commands are
  base64-served and decoded by the beacon (detection implications!).
- **Richer statistics** - coefficient of variation, regularity index (1/(1+cv)),
  lag-1 autocorrelation quantify "metronomic vs human-like" timing.
- **`analyze.py --compare A.jsonl B.jsonl`** - side-by-side table with automatic
  takeaways; perfect before/after demo for your professor.
