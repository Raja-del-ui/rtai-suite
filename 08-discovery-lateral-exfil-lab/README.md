# Project 08 — Discovery / Lateral / Exfil Lab

**MITRE ATT&CK:** TA0005 Defense Evasion · TA0007 Discovery · TA0008 Lateral Movement · TA0009 Collection · TA0010 Exfiltration · TA0040 Impact  
**Kill Chain:** Discovery → Lateral Movement → Collection → Exfiltration → Impact (enhances 04 C2)  
**Mode:** *Simulation in a lab — no real lateral, no real exfil, no real encryption.*

## Runs Natively on Windows & Kali Linux

Fully standalone: vendored `rtai_core` ships inside this folder; stdlib-only runtime, 100% offline capable.

| OS | One-time setup | Run |
|---|---|---|
| Windows | *(nothing to install)* | `python apt_lab.py --host 127.0.0.1 --log apt.jsonl` |
| Kali / Debian | *(nothing to install; venv optional)* | `python3 apt_lab.py --host 127.0.0.1 --log apt.jsonl` |

A full APT tradecraft **simulator** that walks the kill chain after initial access, emitting the same telemetry shapes a blue team would see — without ever touching real user data or the network. Every phase logs to JSONL and the tamper-evident audit chain, and can be observed by the 04 C2 listener and ingested by the 05 report copilot.

```
             Discovery (TA0007)              Defense Evasion (TA0005)        Collection (TA0009)
  ┌─────────────────────────────────┐   ┌──────────────────────────┐   ┌─────────────────────────┐
  │ T1082 env vars (names only)    │   │ T1027 UA rotation/base64 │   │ T1005 dummy files       │
  │ T1083 temp-dir file list       │──▶│ T1070 timestomp (log)    │──▶│ T1074 stage + 7z log   │
  │ T1018 resolve 127.0.0.1        │   │ T1036 masquerade log     │   │ (random bytes, not user)│
  │ T1069 groups (local only)      │   └──────────────────────────┘   └────────────┬────────────┘
  └─────────────────────────────────┘                                              │
                          Lateral Movement (TA0008)                      Exfiltration (TA0010)
                   ┌─────────────────────────────────┐            ┌──────────────────────────────┐
                   │ T1021 PsExec/WMI/SMB ->127.0.0.1│            │ T1041 POST random →127.0.0.1:8080/exfil
                   │ T1550 Pass-the-Hash (log only) │───────────▶│ T1048 DNS TXT sim (log only)
                   │ T1080 Taint Shared (log only)  │  jitter   │ T1048 cloud dead-drop (log)
                   │  + jitter + audit-chain        │            │  + UA rotation (enhances C2)
                   └─────────────────────────────────┘            └──────────────┬───────────────┘
                                                                                │
                                                              Impact (TA0040, report-only)
                                                               ┌─────────────────────────────┐
                                                               │ T1486 ransom note (log)     │
                                                               │ T1496 resource hijack (log) │
                                                               │ NO encryption executed       │
                                                               └──────────────┬──────────────┘
                                                                              │
                                   ┌──────────────────────────────────────────┘
                                   ▼
                          apt_telemetry.jsonl ──▶ 04/analyze.py (beacon stats)
                          apt_findings.json   ──▶ 05/copilot.py (report ingestion)
                          audit.log (hash-chained) ──▶ AuditChain.verify()
```

## Setup

```powershell
# No dependencies — pure standard library (same as 02,03,04)
# Optional: ensure listener side is visible
python -m py_compile apt_lab.py   # verify
```

## Usage

### 1) Authorization

Every run requires **typed attestation**. Two paths:

```powershell
# Interactive (human)
python apt_lab.py --host 127.0.0.1 --log apt_telemetry.jsonl --findings apt_findings.json
# -> Type ATTACK to certify lab-only use on 127.0.0.1 (authorized simulation):

# CI / scripted (HMAC, mirrors 02 fuzzer pattern)
$env:RTAI_ATTEST_KEY="lab-secret-key-32b"
$hmac = python -c "import hmac,hashlib,os;print(hmac.new(os.environ['RTAI_ATTEST_KEY'].encode(),b'attested',hashlib.sha256).hexdigest()[:16])"
$env:APT_LAB_ATTESTED=$hmac
python apt_lab.py --yes --host 127.0.0.1 --log apt.jsonl
```

Gate implementation: `apt_lab.py:78-120` (`ATTEST_PHRASE="ATTACK"`, `ENV_BYPASS="APT_LAB_ATTESTED"` + `RTAI_ATTEST_KEY` HMAC).

### 2) End-to-end with 04 listener (observe exfil)

Three terminals (or background jobs) — classic purple-team workflow:

```powershell
# terminal 1 — 04 listener (observation point, never executes)
python ..\04-c2-detection-lab\listener.py --host 127.0.0.1 --port 8080 --log beacons.jsonl

# terminal 2 — 08 apt lab (implant-side simulation)
python apt_lab.py --host 127.0.0.1 --port 8080 --log apt_telemetry.jsonl --findings apt_findings.json

# terminal 3 — analysis (works with either log)
python ..\04-c2-detection-lab\analyze.py --log apt_telemetry.jsonl --stats-only
python ..\04-c2-detection-lab\analyze.py --log beacons.jsonl --stats-only  # listener-side view
```

Exfil path: `apt_lab.py:430-505` POSTs synthetic random bytes to `http://127.0.0.1:8080/exfil` with UA rotation and jitter — identical to `04/beacon.py:146-151` so `04/listener.py:69-75` hashes it.

### 3) Report ingestion via 05 copilot

`apt_lab.py:590-650` emits `apt_findings.json` shaped for `05/parsers.py:1-188`:

```powershell
# Inspect the bundle (no LLM needed for deterministic pipeline proof)
cat apt_findings.json | python -m json.tool

# Ingest into 05 (skeleton report without API keys — proves shape compatibility)
python ..\05-pentest-report-copilot\copilot.py --nmap samples\sample-nmap.xml --company "Lab" --no-llm --out skeleton.md
# Or, treat apt_findings.json as a custom source: enrich via Jinja2 + LLM using copilot's emit-json shape.
```

Finding schema per entry (matches `05/copilot.py:151-170` bundle):
`{tool:"apt-lab", kind, host, hostname, location, title, severity, techniques:[...], tactic:"TA00xx"}`

### 4) Flags

```
--host 127.0.0.1        lab listener host (lab-only, assert_lab_address)
--port 8080             listener port (matches 04 default)
--log apt_telemetry.jsonl  JSONL telemetry (for analyze.py)
--findings apt_findings.json  findings bundle (for copilot)
--staging-dir PATH      staging dir (default: %TEMP%/apt_lab_stage_<id>)
--db apt_events.db      also mirror into SQLite (SqliteEventStore)
--exfil-count 2         synthetic POSTs per run
--dummy-files 3         dummy staged files
--jitter 0.35           jitter fraction (0.0-1.0) for lateral/exfil timing
--allow-public          allow non-lab host (audited, lab-network exception only)
--yes                   skip ATTACK prompt (requires APT_LAB_ATTESTED HMAC)
--verbose               debug logging
```

## ATT&CK Mapping — TA0005, TA0007, TA0008, TA0009, TA0010, TA0040

| Tactic | Techniques simulated | Code | Detection idea |
|---|---|---|---|
| **TA0005 Defense Evasion** | T1027 Obfuscated Files or Information (base64 + UA rotation), T1070.006 Timestomp (log mtime spoof), T1036 Masquerading (svchost/rundll32 masq) | `apt_lab.py:380-440` | Sigma: `Image|contains: apt_lab.py` + `UserAgent` rotation cardinality >3; EDR: `timestomp` event with `timestomped_mtime_sim` |
| **TA0007 Discovery** | T1082 System Information Discovery (platform.uname + env var names), T1083 File & Directory Discovery (temp-dir listing), T1018 Remote System Discovery (getaddrinfo 127.0.0.1 only), T1069 Permission Groups Discovery (whoami/id groups) | `apt_lab.py:135-260` | Risk: Discovery events are noisy but low severity — correlate >3 discovery events from one `run_id` within 60s |
| **TA0008 Lateral Movement** | T1021.001/.004/.006 Remote Services (PsExec/SMB/WMI), T1550.002 Use Alternate Authentication Material (PtH), T1080 Taint Shared Content (deprecated, simulated) | `apt_lab.py:265-310` | Network: SMB `445` to 127.0.0.1 only in lab; real rule = `dst_ip != lab` + `EventID 7045 Service Install` |
| **TA0009 Collection** | T1005 Data from Local System (dummy random files), T1074.001 Data Staged (staging dir + `7z a` placeholder) | `apt_lab.py:315-370` | File: `staging_dir` creation + `*.7z` placeholder in same minute; `total_bytes` threshold |
| **TA0010 Exfiltration** | T1041 Exfiltration Over C2 Channel (POST random to 127.0.0.1:8080/exfil), T1048.003 Exfil Over Alternative Protocol via DNS TXT, T1048 cloud dead-drop | `apt_lab.py:430-540` | HTTP: `POST /exfil` byte size 256-1024 + random UA; DNS: TXT query with hex labels; cloud: `lab-deaddrop.example` |
| **TA0040 Impact** | T1486 Data Encrypted for Impact (ransom note log, 0 files encrypted), T1496 Resource Hijacking (85% CPU sim) | `apt_lab.py:545-590` | Host: file creation `ransom*.txt` OR `impact` event with `T1486` — but note `report-only` watermark |

All events carry `tactic` (`TA00xx`), `technique` (`Txxxx`), `run_id`, and `note: LOG ONLY`.

## Safety Design (graded)

| Control | Implementation |
|---|---|
| **Authorized-use gate** | Must type `ATTACK` (`apt_lab.py:98-115`) or HMAC `APT_LAB_ATTESTED` via `RTAI_ATTEST_KEY` (`apt_lab.py:78-95`); audited (`audit.log` hash chain) — mirrors `02/inject_fuzzer.py:28-60` |
| **Lab-only guard** | `assert_lab_address(host)` at `apt_lab.py:118-135` AND per-phase (`run_discovery`, `simulate_lateral_movement`, `simulate_exfiltration`) — loopback/private/link-local only (`rtai_core/validation.py:27-87`); `--allow-public` is explicit opt-in + audited |
| **Read-only discovery** | Env values redacted (`apt_lab.py:210-225`), file enumeration limited to temp staging dir (`apt_lab.py:145-165`), process listing truncates to image names (`apt_lab.py:170-210`) — real docs never read |
| **No real lateral/exfil** | Lateral only logs (`apt_lab.py:265-310`, `result: simulated_blocked_lab_only`); exfil random bytes (`os.urandom`, `apt_lab.py:435`) POSTed to local listener (`apt_lab.py:445-470`), DNS query logged not sent (`apt_lab.py:485-510`), cloud URL logged not fetched |
| **No real impact** | T1486/T1496 set `files_would_encrypt:0`, watermark `REPORT-ONLY` (`apt_lab.py:545-590`) — never calls encryption or CPU burn |
| **Audit chain** | Hash-chained JSONL via `rtai_core/audit.py:40-145` (`prev` hash, `verify()` detects tampering at exact line); every phase records `discovery_sim`, `lateral_sim`, `exfil_sim`, `apt_run_complete` |
| **7z placeholder** | `simulate_collection: simulate_collection()` (`apt_lab.py:315-370`) builds `7z a` string but never spawns `7z`; dummy files are `stage_dummy_*.bin` with `os.urandom` |
| **Telemetry safety** | JSONL (`JsonlStore`, `rtai_core/storage.py:12-40`) and SQLite (`SqliteEventStore`) are local append-only; payload hashes (`sha16`) stored, not content |

> **Prohibited:** removing `assert_lab_address`, deleting `require_authorization`, or pointing `--host` at a public IP without `--allow-public` + written lab-network exception. Bypassing controls breaches `AUP.md` and `EULA.md` §3 (see `AUP.md:42-49`).

## Integration Points

- **04-c2-detection-lab listener** — POST target `http://127.0.0.1:8080/exfil` (`apt_lab.py:445`), UA rotation list (`apt_lab.py:38-50`) mirrors `04/beacon.py:31-36`, cookie `sid=` mirrors `04/beacon.py:120`. Listener logs (`listener.py:69-75`, `beacons.jsonl`) will show `event:"exfil"` with `size` + `sha16` for detection tuning.
- **05-pentest-report-copilot parsers** — findings bundle (`apt_lab.py:590-650`, `apt_findings.json`) uses normalized shape `{tool, kind, host, location, title, severity, techniques, tactic}` compatible with `05/parsers.py:9-50` + `05/copilot.py:151-170` `emit_json` stage. Ingest without LLM via `--no-llm` to prove pipeline, then enrich via `enrich.py`.

## Talking Points (for report/defense)

- Why beacon `jitter` (0.35 default, `apt_lab.py:430`) defeats fixed-interval NDR alerts — link to `04/analyze.py:38-66` CV/regularity/autocorr metrics.
- Defense evasion trade-off: UA rotation helps evade `User-Agent` IOCs but creates cardinality anomaly (detect via `distinct_user_agents` in `analyze.py:44`).
- Staging → exfil → impact chaining in the findings narrative (`05/copilot.py` Attack Narrative chapter) — demonstrates kill-chain coverage for purple-team debrief.
- Tamper-evident audit: mutate any `audit.log` line and `AuditChain.verify()` returns `(False, line_number)` (`rtai_core/audit.py:134-145`).

## Verification

```powershell
python -m py_compile apt_lab.py
python apt_lab.py --help
# full run (needs ATTACK phrase)
python apt_lab.py --host 127.0.0.1 --log apt_telemetry.jsonl --findings apt_findings.json
cat apt_telemetry.jsonl   # discovery/lateral/collection/exfil/impact events
cat apt_findings.json     # ingestable by 05 copilot
python -c "from rtai_core.audit import AuditChain; print(AuditChain().verify())"
```

## v2 Ideas

- Add `--profile` timing presets (regular/low_slow/bursty) like `04/beacon.py:38-46` for dwell-time experiments.
- Emit STIX 2.1 bundle via `rtai_core/military_stix.py` alongside findings JSON.
- Auto-generate Sigma YAML per technique (like `04/analyze.py:106-124`) from observed telemetry.
