# Project 07 — Persistence, Privilege Escalation & Credential Access Lab

**Cyber Kill Chain:** Installation · **MITRE ATT&CK:** TA0003 Persistence, TA0004 Privilege Escalation, TA0006 Credential Access — *simulated in a lab, no host mutation*

## Runs Natively on Windows & Kali Linux

Fully standalone: vendored `rtai_core` ships inside this folder; stdlib-only runtime, 100% offline capable.

| OS | One-time setup | Run |
|---|---|---|
| Windows | *(nothing to install)* | `python persist_lab.py --host 127.0.0.1 --technique all --dry-run` |
| Kali / Debian | *(nothing to install; venv optional)* | `python3 persist_lab.py --host 127.0.0.1 --technique all --dry-run` |

A **safe-by-design** lab that simulates the later Kill Chain stages every other project avoided: an attacker who already has a foothold now tries to **stay** (persistence), **escalate** (privilege), and **steal** (credentials). Every "implant" is a **JSONL record** describing what *would* have been created — the host registry, scheduled tasks, systemd units, WMI subscriptions, and Startup folder are **never touched**.

```
                         persist_lab.py (lab-only, audited)
                         ┌─────────────────────────────────┐
  --host 127.0.0.1 ─────▶│ assert_lab_address()  (lab guard)│
  --scope-domain lab.local│ valid_domain()      (scope guard)│
  I AM AUTHORIZED / HMAC │ require_authorization() (audit)  │
                         └────────────┬────────────────────┘
                                      ▼
              ┌──────────────────────────────────────────┐
              │  Persistence (TA0003)  — 5 simulated     │
              │  • T1547.001 Registry Run key            │
              │  • T1053.005 Scheduled Task              │
              │  • T1543.003 Systemd / Windows Service   │
              │  • T1546.003 WMI Event Subscription      │
              │  • T1547.001 Startup Folder .lnk         │
              │        ↕ JSONL only (no host write)      │
              │  Privilege Escalation (TA0004) — 3 RO    │
              │  • T1134  whoami /groups, id/groups     │
              │  • T1134.001 process token /priv         │
              │  • T1548.002 UAC status (reg query RO)   │
              │                                          │
              │  Credential Access (TA0006) — 3 RO       │
              │  • T1003 vault existence (no dump)       │
              │  • T1552 creds in files (existence only) │
              │  • T1555 browser vault (existence only)  │
              └──────────────┬───────────────────────────┘
                             ▼
                    persistence.jsonl (JSONL)
                    audit.log (hash-chained via rtai_core.audit)
```

## Setup

No third-party packages — pure standard library.

```powershell
# Windows
python -m py_compile persist_lab.py   # verify
python persist_lab.py --host 127.0.0.1 --technique all --dry-run

# Kali / Debian
python3 -m py_compile persist_lab.py
python3 persist_lab.py --host 127.0.0.1 --technique all --dry-run
```

For non-interactive / CI use, set the HMAC bypass:

```powershell
# With RTAI_ATTEST_KEY set, compute HMAC:
#   hex(hmac-sha256(RTAI_ATTEST_KEY, "attested"))[:16]
$env:RTAI_ATTEST_KEY="your-secret"
$env:PERSIST_LAB_ATTESTED="<hmac-hex-16>"
python persist_lab.py --host 127.0.0.1 --technique all --log persistence.jsonl

# Legacy (no HMAC key configured):
$env:PERSIST_LAB_ATTESTED="1"
python persist_lab.py --host 127.0.0.1 --technique all --dry-run
```

## Usage

```powershell
# Dry-run — preview what would be logged (no file written)
python persist_lab.py --host 127.0.0.1 --technique all --dry-run

# Simulate a single technique
python persist_lab.py --host 127.0.0.1 --technique registry_run --log persistence.jsonl
python persist_lab.py --host 127.0.0.1 --technique scheduled_task --log persistence.jsonl
python persist_lab.py --host 127.0.0.1 --technique service --log persistence.jsonl
python persist_lab.py --host 127.0.0.1 --technique wmi --log persistence.jsonl

# Hidden aliases (full 5-vector coverage) — also accepted
python persist_lab.py --host 127.0.0.1 --technique systemd --log persistence.jsonl
python persist_lab.py --host 127.0.0.1 --technique startup_folder --log persistence.jsonl

# All five persistence vectors + privesc + cred checks (default log)
python persist_lab.py --host 127.0.0.1 --technique all --log persistence.jsonl

# With scope domain validation (valid_domain guard)
python persist_lab.py --host 127.0.0.1 --technique all --scope-domain lab.local --log persistence.jsonl

# Skip optional stages
python persist_lab.py --host 127.0.0.1 --technique all --skip-privesc --skip-creds --log persistence.jsonl

# Inspect output
type persistence.jsonl          # Windows
cat persistence.jsonl           # Linux
python -m json.tool persistence.jsonl  # pretty (first record only: head -1 | python -m json.tool)
```

### CLI reference

| Flag | Default | Description |
|---|---|---|
| `--host` | `127.0.0.1` | Lab target host — must resolve to loopback/private (`assert_lab_address` guard) |
| `--technique` | `all` | One of `registry_run`, `scheduled_task`, `service`, `wmi`, `all` (hidden aliases: `systemd`, `startup_folder`) |
| `--log` | `persistence.jsonl` | JSONL output path for simulated events |
| `--dry-run` | off | Preview only — do not write JSONL, do not mutate host (audit still records) |
| `--scope-domain` | none | Optional scope domain validated via `valid_domain` (also accepts `--domain` alias) |
| `--skip-privesc` | off | Skip privilege-escalation read-only checks (T1548, T1134) |
| `--skip-creds` | off | Skip credential-access existence checks (T1003, T1552, T1555) |
| `--verbose` | off | Verbose logging including ATT&CK mapping table |

## ATT&CK Coverage

| Tactic | ID | Techniques simulated (log-only) | Artifact (simulated) |
|---|---|---|---|
| **Persistence** | **TA0003** | **T1547.001** Registry Run Keys | `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` |
| | | **T1053.005** Scheduled Task/Job | `\Microsoft\Windows\SimulatedTask` (task XML) |
| | | **T1543.003** Windows Service | `/etc/systemd/system/rtai-lab-sim.service` (unit) |
| | | **T1543.002** Systemd Service | `/etc/systemd/system/rtai-lab-sim.service` (unit alias) |
| | | **T1546.003** WMI Event Subscription | `ROOT\Subscription:__EventFilter` (MOF) |
| | | **T1547.001** Startup Folder | `%APPDATA%\...\Startup\rtai-lab-sim.lnk` |
| **Privilege Escalation** | **TA0004** | **T1134** Access Token Manipulation (enum) | `whoami /groups` / `id` + `groups` (read-only) |
| | | **T1134.001** Token Impersonation (enum) | `whoami /priv` / `id -a` + `capsh --print` (read-only) |
| | | **T1548.002** Bypass UAC (status check) | `reg query ...\EnableLUA` (read-only, no bypass) |
| **Credential Access** | **TA0006** | **T1003** OS Credential Dumping (simulated) | `C:\...\SAM` / `/etc/shadow` existence only (no dump) |
| | | **T1552.001** Unsecured Credentials In Files | `~/.aws/credentials`, `~/.ssh/id_rsa`, `.env` existence only |
| | | **T1555.003** Credentials from Password Stores | Chrome/Firefox `Login Data` existence only (no decryption) |

Every event carries `tactic`, `technique`, `technique_name`, `host`, `ts`, `safety`, and `simulated: true` for ATT&CK Navigator / Sigma mapping.

## Safety Design (this is the graded part)

| Control | Implementation | Where |
|---|---|---|
| **Lab-only guard** | `assert_lab_address(host)` — refuses any host resolving to public IP (loopback/private/link-local only) | `persist_lab.py:guard_host()` |
| **Scope guard** | `valid_domain(scope_domain)` — validates optional scope FQDN | `persist_lab.py:guard_scope_domain()` |
| **Authorized-use gate** | Must type `I AM AUTHORIZED` interactively **or** set `PERSIST_LAB_ATTESTED=HMAC(RTAI_ATTEST_KEY,"attested")[:16]` (legacy `=1` when no key) | `persist_lab.py:require_authorization()` |
| **HMAC verification** | `hmac.compare_digest` on both phrase and env bypass; fail-closed on HMAC mismatch | `persist_lab.py:_env_bypass_ok()` |
| **No host mutation** | Zero calls to `winreg`, `schtasks`, `systemctl`, `wmic`, or filesystem writes to persistence locations; all techniques emit `command_simulated` strings only | `persist_lab.py:_sim_*()` |
| **Read-only privesc** | `whoami /groups`, `whoami /priv`, `reg query ... /v EnableLUA`, `id`, `capsh --print` via `subprocess.run(..., shell=False)` with timeout | `persist_lab.py:simulate_privesc_checks()` |
| **No credential dumping** | `Path.exists()` only — never `open()`, never `read()`, no LSASS, no vault decryption (T1003/T1552/T1555) | `persist_lab.py:simulate_credential_access()` |
| **Tamper-evident audit** | Every simulated event also `audit_record()` via `rtai_core.audit.AuditChain` (hash-chained JSONL) | `persist_lab.py:simulate_*()` + `require_authorization()` |
| **Dry-run mode** | `--dry-run` suppresses JSONL writes and prints `[dry-run] would log ...` preview | `persist_lab.py:simulate_*()` |
| **Stdlib only** | No `pip install` — vendored `rtai_core` is stdlib-only | `requirements.txt` |

> **Never run persistence against a host you do not own.** This lab enforces that technically (lab-address guard) and procedurally (attestation gate + audit chain). For real engagements, obtain written authorization and scope in a Rules of Engagement.

## Output — JSONL (one event per line)

Each line is a self-contained JSON object:

```json
{"ts":"2026-05-13T12:00:00Z","event":"persistence_simulated","tactic":"TA0003","technique":"T1547.001","technique_name":"Registry Run Keys / Startup Folder — Run key","host":"127.0.0.1","artifact":"HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run","action":"SIMULATED — would create registry Run value","command_simulated":"reg add HKCU\\...","safety":"DRY-RUN — no registry write performed; event logged only","dry_run":false,"simulated":true,"lab_only":true}
{"ts":"2026-05-13T12:00:01Z","event":"privesc_check","tactic":"TA0004","technique":"T1134","technique_name":"Access Token Manipulation — group membership enumeration","host":"127.0.0.1","check":"whoami_groups","result":{"cmd":"whoami /groups","returncode":0,"stdout":"...","stderr":""},"safety":"READ-ONLY — whoami/groups enumeration only, no token manipulation","simulated":true,"lab_only":true}
{"ts":"2026-05-13T12:00:02Z","event":"credential_access_simulated","tactic":"TA0006","technique":"T1003","technique_name":"OS Credential Dumping — simulated existence check (no dump)","host":"127.0.0.1","check":"T1003_vault_existence","paths_checked":{"/etc/shadow":true,"/etc/passwd":true},"safety":"SIMULATED — existence check only (Path.exists), no file opened, no credential dumped (T1003)","simulated":true,"lab_only":true}
```

Verify the audit chain:

```powershell
python -c "from rtai_core.audit import AuditChain; ok,line=AuditChain().verify(); print('audit ok' if ok else f'audit broken at line {line}')"
```

## Verification

```powershell
python -m py_compile persist_lab.py && echo "py_compile: ok"
python persist_lab.py --help
PERSIST_LAB_ATTESTED=1 python persist_lab.py --host 127.0.0.1 --technique all --log persistence.jsonl --dry-run
PERSIST_LAB_ATTESTED=1 python persist_lab.py --host 127.0.0.1 --technique registry_run --log persistence.jsonl
type persistence.jsonl
```

## Talking Points (for your writeup / demo)

- **Why simulation matters:** Real persistence (registry, services, WMI) survives reboots and is the hardest to eradicate — this lab shows the *artifacts* without creating them, perfect for purple-team detection engineering.
- **T1547 vs T1543 vs T1546:** Compare Run keys (userland, easy to spot) vs services (SYSTEM, needs admin) vs WMI (fileless, hardest) — ask the LLM to write Sigma rules from the JSONL.
- **T1548 / T1134 read-only checks:** Explain why `whoami /priv` + UAC `EnableLUA` query is enough to assess escalation posture without attempting bypass.
- **T1003/T1552/T1555 existence-only pattern:** Demonstrate how to prove a vault *exists* for a finding without crossing the line into credential dumping — the same discipline required in real pentests.

## v2 Ideas

- Emit an ATT&CK Navigator layer JSON from the JSONL (see `rtai_core.military_stix.ATTACKNavigatorLayer`).
- Add Sigma rule skeletons per technique and an LLM prompt to turn JSONL into detections.
- Add `--emit-stix` (STIX 2.1 bundle) mirroring `05-pentest-report-copilot`'s military extensions.

## License & Ethics

Authorized lab use only. See `../../AUP.md` and `../../SECURITY.md`. All simulated events are marked `lab_only: true` and `simulated: true` — never replay `command_simulated` strings on a real host.
