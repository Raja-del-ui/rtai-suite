# Royal-Sec — AI-Integrated Red Team Toolkit

**v4.1.0-military — Royal-Sec Tactical Operations Console.** Five standalone tools on one engineered core (`rtai_core`),
fronted by a hardened REST microservice (mTLS/SPIFFE, FIPS 140-3, OPA, HSM), a unified `rtai` CLI (`rtai mission` + 9 tools), **military-style GUI** (OD Green / Coyote / Black-Green HUD, classification banners, tactical map), containers, and STIX/TAXII + TLA+ + STIG.

> **AUTHORIZATION REQUIRED — Royal-Sec Authorized Use Only** — Every tool here is for
> **lab environments, CTFs, or engagements you are explicitly authorized to perform** (signed scope/ROE).
> Each project includes built-in authorization gates (`rtai_core/audit.py` hash-chained, lab-only IP guards
> `rtai_core/validation.py:38-43`, bearer auth `services/api/server.py:236-253`). Misuse is your responsibility, not the code's.
> See `EULA.md`, `AUP.md`, `PRIVACY.md`, `SECURITY.md`, and `docs/SECURITY_AND_ETHICS.md` for binding terms.
> Commercial use requires `legal@royal-sec.com` authorization and `RTAI_API_TOKEN` / `RTAI_ATTEST_KEY` configuration.

## Platform Capabilities — Military-Grade

| Capability | Entry point | Military |
|---|---|---|
| Unified CLI | `rtai --list`, then `rtai recon / fuzz / phish / c2-listen / c2-beacon / c2-analyze / report / mission ...` | `rtai mission --create --name "MANTICORE" --classification SECRET --targets example.com` |
| REST API | `python services/api/server.py --port 9000` → `/health` `/version` `/metrics` `/v1/recon` | `RTAI_FIPS=1` `RTAI_TLS_CERT` `RTAI_OPA_POLICY` `RTAI_TPM_ATTEST=1` `RTAI_HSM_REQUIRED=1` |
| Observability | Prometheus-format metrics at `/metrics`; structured JSON logs everywhere | `audit.log` **WORM** `chattr +a` + `RTAI_SIEM_URL` POST + `logrotate` `/var/log/royal-sec` |
| Containers | `docker build -t rtai-suite .` (non-root + healthcheck) · `docker compose up api` | `audit_log:/var/log/royal-sec` + `certs:/policies` + `read_only`/`cap_drop` |
| Schema contracts | `schemas/*.schema.json` enforced by contract tests | **STIX 2.1** `copilot --emit-stix bundle.json --classification CUI` + **ATT&CK Navigator** |
| Quality gates | pytest (91) · ruff · mypy(strict core) · compileall · CI matrix · release pipeline | **FIPS** `military_fips.py`, **TLA+** `tla_verify.py`, **STIG** `stig_enforce.py`, **SLSA L4** `cosign` |

## Standalone Mode & OS Support

Every project folder is **self-contained**: it vendors its own copy of `rtai_core`,
ships its `requirements.txt`, and runs on **Windows and Kali Linux** out of the box.

| Project | Windows | Kali / Debian | Runtime deps |
|---|---|---|---|
| 01-ai-recon-agent | ✅ | ✅ | dnspython |
| 02-llm-injection-fuzzer | ✅ | ✅ | stdlib only |
| 03-phishing-awareness-sim | ✅ | ✅ | stdlib only |
| 04-c2-detection-lab | ✅ (offline) | ✅ (offline) | stdlib only |
| 05-pentest-report-copilot | ✅ | ✅ | jinja2 |

- Zip any single project folder → it works elsewhere with nothing but Python ≥3.11.
- Missing optional deps produce actionable errors, not tracebacks.
- Repo-dev mode still uses the shared core at root (`pip install -e .`); per-project
  tests run via `pytest tests` inside each folder.
- Unified CLI remains available repo-wide: `rtai --list`.

## Military Operations Console (GUI) — OD Green / Tactical HUD

**Launch:** `rtai-gui` or `rtai gui` — Tactical Operations Console v4.1.0-military

- **Classification banners** top/bottom — `UNCLASS` (green `#007A33`) / `CUI` (purple `#502B85`) / `SECRET` (red `#C8102E`) / `TOP_SECRET` (orange `#FF6A00`) per `rtai_core/mission.py:14-22` `CLASS_BANNERS` + `CLASS_COLORS`, driven by `missions/*.json` or `RTAI_CLASSIFICATION`
- **Header:** `◆ RTAI // TACTICAL OPS` + encryption LEDs `FIPS/mTLS/TPM/WORM/HSM` (`rtai_core/gui/launcher.py:19-45` now OD Green `#1A261A` + `style.py:MILITARY_QSS`)
- **Tactical Dashboard** `◆ TACTICAL` tab: mission selector (`missions/index.json`), **tactical map** `TacticalMapWidget` (grid, crosshair, BFT: REAPER 06 / TARGET ALPHA / FOB HAMMER, MGRS `38TLL 1234 5678`, ZULU), **OPSEC** (`ROE signed/validated`), **ENCRYPTION** (`FIPS/mTLS/PQC`), **AUDIT** (`WORM/SIEM`), **STIX** (12 indicators), **TLA+/STIG** (3 specs verified) — `launcher.py:TacticalMapWidget` + `_tactical_dashboard_tab()`
- **Mission tab** `rtai_core/gui/mission_gui.py:1-100` — create `OP-XXXX` with classification/caveat/ROE/approver/grid, `MISSION PACKAGE` (STIX+SBOM+audit), `OPSEC CHECK`; CLI `rtai mission --create --name "MANTICORE SHIELD" --classification SECRET --caveat NOFORN --targets example.com`
- **STIX tab** `rtai_core/gui/stix_gui.py:1-100` — TAXII fetch + `STIXBuilder` indicator generation + ATT&CK Navigator `layer.json` (`military_stix.py:226-415`)
- **Reports:** `copilot --classification SECRET` embeds **classification banner** top/bottom (`report.md.j2:1-5` + `report.html.j2:1-5` `classification_banner`/`classification_color`) + handling `DESTROY BY ANY METHOD...`

## Quality Gates

| Gate | Status |
|---|---|
| Tests | 91 offline unit tests (`python -m pytest` or `python scripts/dev.py test`) + STIX Navigator + mission |
| Lint | ruff gate (`python scripts/dev.py lint`) — military modules `military_fips.py`/`military_hsm.py` |
| CI | GitHub Actions: lint + typecheck + SBOM enforce + FIPS + STIG + TLA + Ubuntu/Windows x 3.11/3.13 with coverage |
| Packaging | installable shared library: `pip install -e .[dev,recon,report,gui]` → `royal-sec-rtai-suite:4.1.0` |
| Docs | EULA/AUP/Privacy/DPA/Export/Trademark + TLA+ specs + STIG profiles + STIX bundles |

## Architecture: rtai_core Shared Library

All five projects sit on one engineered foundation instead of duplicated scripts:

```
rtai_core/
  exceptions.py    RTAIError hierarchy -> ExitCode mapping at the CLI boundary
  logging_utils.py console + JSON-lines structured logging (rtai.* namespace)
  cli.py           progress helpers, banner(), run_main() error funnel
  config.py        BaseConfig: defaults <- file <- env <- CLI layers, validators
  registry.py      generic plugin Registry (collectors, detector rules, templates)
  retry.py         RetryPolicy: exponential backoff + jitter, injectable clock
  storage.py       JsonlStore append/read + SqliteEventStore emit/query
  models.py        Severity enum, Finding dataclass, findings_to_sarif()
  providers/       ChatProvider ABC -> OpenAI-compat / Anthropic / Ollama
                   factory autodetects keys; ChatClient facade + ask_json()
```

Design rules: stdlib-only runtime core, typed public surface, deterministic
behavior first (LLMs reason *above* this layer, never inside it), every guard is
unit-tested. Install once with `pip install -e .`; per-project requirements files
remain for standalone use.

## Documentation (`docs/`)

| File | Purpose |
|---|---|
| `EULA.md` / `AUP.md` / `PRIVACY.md` / `DPA.md` / `EXPORT_CONTROL.md` / `TRADEMARK.md` | **Royal-Sec legal pack — binding for commercial use** |
| `SECURITY_AND_ETHICS.md` | Authorization controls, legal context, STRIDE per tool |
| `SECURITY.md` | Commercial security policy (report `security@royal-sec.com`, 24h ack, 90-day disclosure) |
| `NOTICE.md` | Third-party attributions (dnspython ISC, jinja2 BSD-2, PySide6 LGPL-3.0) |
| `PROJECT_PROPOSAL.md` *(archive)* | Formal proposal — see `docs/archive/` for academic deliverables |
| `STUDY_GUIDE.md` *(archive)* | Concept primers, viva Q&A — `docs/archive/` |
| `DEMO_RUNBOOK.md` *(archive)* | Timed live-demo — `docs/archive/` |
| `GRADING_RUBRIC.md` *(archive)* | 100-point rubric — `docs/archive/` |

> Academic docs are archived under `docs/archive/` post commercial transition; product docs live at top-level `docs/` + `mkdocs.yml:17-69` nav.

## The Suite — Full Cyber Kill Chain (7 phases) + MITRE ATT&CK

| # | Folder | Kill Chain / ATT&CK | How AI Is Integrated |
|---|--------|----------------|----------------------|
| 1 | `01-ai-recon-agent` | **Reconnaissance** `T1590/T1592/T1596` | LLM fuses passive OSINT (RDAP, DNS, CT logs, TLS, Wayback, HTTP posture) into prioritized attack-surface assessment |
| 2 | `02-llm-injection-fuzzer` | **Weaponization+Exploitation** `T1587/T1190` | Adaptive prompt-injection fuzzing with multi-turn chains, regex detectors + LLM-as-judge scoring, automated payload mutation; SARIF output for CI |
| 3 | `03-phishing-awareness-sim` | **Delivery** `T1566` | LLM generates realistic-but-benign awareness-training emails with tokenized click-tracking, education landing page, metrics dashboard |
| 4 | `04-c2-detection-lab` | **C2** `T1071` | Local C2 listener + timing-profile beacon simulator (jitter presets, office-hours, kill switch); LLM drafts Sigma/Suricata detections |
| 5 | `05-pentest-report-copilot` | **Actions on Objectives** | Parses nmap/nuclei/Nessus, cross-correlates, then LLM writes narratives, attack chain story, 30/60/90 roadmap + STIX/Navigator + classification |
| 6 | `06-weaponization-forge` | **Weaponization** `T1587` | Benign forge: EICAR + watermarked macro/LNK/HTA/ISO/shellcode-stub placeholders, FORBIDDEN_SNIPPETS inverted blocklist, lab-only, audit-chained |
| 7 | `07-persistence-privesc-lab` | **Installation / PrivEsc / CredAccess** `T1547/T1053/T1543/T1546/T1078/T1136/T1098` + `T1548/T1134` + `T1003/T1552/T1555` | Simulates registry Run, scheduled task, systemd service, WMI, Startup — logs only, never host write; safe privesc checks + cred existence scans |
| 8 | `08-discovery-lateral-exfil-lab` | **Discovery / Lateral / Collection / Exfil / Impact** `T1082/T1083/T1018/T1069`, `T1021/T1550`, `T1005/T1074`, `T1041/T1048`, `T1486/T1496` + `T1027/T1070/T1036` | Read-only discovery, simulated lateral to 127.0.0.1 + jitter, dummy staging + 7z placeholder, exfil POST to lab listener + DNS/cloud covert sim, impact report-only |
| 9 | `09-killchain-orchestrator` | **Orchestrator** | Runs `01→06→03→02→04→07→08→05` in order, mission-aware (`rtai mission`), `KILLCHAIN_ATTESTED` HMAC, `audit.log` hash chain, dry-run via `--help` for safe demos |

> **APT realism:** Modules `06-08` are **lab-only simulations** (never real shellcode/exploit/persistence/credential dump/lateral/exfil of user data) — they log `simulated:true lab_only:true` + hash `audit.log` for blue-team detection tuning, mirroring real APT `EternalBlue / Mimikatz / PsExec / rclone` tradecraft safely. Orchestrator `09` ties all 7 kill-chain phases into one `rtai killchain --target 127.0.0.1 --mission missions/OP-XXXX.json --dry-run --yes` command.

## v2 Feature Highlights

- **P1**: parallel collectors, TLS certificate inspection, Wayback history, live subdomain
  verification, deterministic exposure score (rule-based), `--baseline` diffing.
- **P2**: custom payload files (`--payloads`), multi-turn attack chains, request rate
  limiting (`--rps`), known-system-prompt fuzzy leak detection, SARIF 2.1.0 export.
- **P3**: click-tracking landing server with per-recipient tokens, `--template all`
  campaigns, click-metrics dashboard (`metrics.py`).
- **P4**: timing presets (`--preset regular|low_slow|bursty|office_hours`),
  schedule-aware beaconing, kill switch (`--kill-after`), base64 task encoding,
  CV/regularity/autocorrelation stats + `analyze.py --compare`.
- **P5**: Nessus parser, severity override maps, cross-tool service correlation,
  AI Attack Narrative chapter, AI 30/60/90 remediation roadmap.

## Common Setup

All projects share the same zero-dependency LLM client (`llm_client.py`) supporting:

| Provider | Env vars needed | Notes |
|----------|-----------------|-------|
| OpenAI   | `OPENAI_API_KEY` | default model `gpt-4o-mini` |
| Anthropic| `ANTHROPIC_API_KEY` | default model `claude-sonnet-4-20250514` |
| Ollama   | *(none)* | needs [Ollama](https://ollama.com) running locally, default model `llama3.1` |

Override per run: `--provider`, `--model`, `--base-url`, or env `LLM_PROVIDER` / `LLM_MODEL` / `LLM_BASE_URL`.

```powershell
# free option, no API keys
ollama pull llama3.1
$env:LLM_PROVIDER = "ollama"
```

Each project is self-contained: `pip install -r requirements.txt` inside its folder
(most have no dependencies beyond the standard library).

## Demo Without Any API Keys

- Project 4 runs 100% offline (`listener.py` + `beacon.py`), and `analyze.py --stats-only`
  skips the LLM.
- Projects 1/2/3/5 all support Ollama locally, or `--no-llm` / offline subcommands where noted.

## Royal-Sec Legal & Support

* **Licence:** `LICENSE` (MIT) + `EULA.md` (Royal-Sec commercial terms) — see `EULA.md:1-16` grant/supremacy.
* **Privacy/DPA:** `PRIVACY.md` / `DPA.md` (`privacy@royal-sec.com`).
* **Security:** `SECURITY.md` (report `security@royal-sec.com`, 24h ack, Critical 7d SLA).
* **Export:** `EXPORT_CONTROL.md` (`compliance@royal-sec.com`, ECCN 5D002 indication).
* **Trademark:** `TRADEMARK.md` (Royal-Sec navy/gold livery `rtai_core/gui/launcher.py:19-45`).
* **Install:** `install.sh` / `install.bat` / `requirements.txt` / `verify_installation.py` at repo root (`BOOK.md:77-88` quickstart).
* **API auth:** Set `RTAI_API_TOKEN` + `RTAI_REQUIRE_AUTH=1` for fail-closed commercial mode (`services/api/server.py:381-404`); add `RTAI_ATTEST_KEY` HMAC for `ATTACK`/`I AM AUTHORIZED` gates.

## Suggested Talking Points for Your Professor

1. **Threat modeling**: each README maps the tool to MITRE ATT&CK phases.
2. **Safety engineering**: authorization attestations (`inject_fuzzer.py:29`, `auth.py:31-34`), lab-only IP guards (`rtai_core/validation.py:38-43`), audit chain (`rtai_core/audit.py:17-69`), simulation markers.
3. **LLM ops**: one provider-agnostic client, structured JSON outputs with fence-stripping,
   retries/backoff, truncation-aware prompting.
4. **Detection value**: Projects 2 & 4 produce artifacts defenders can act on
   (hardening advice, Sigma rules) — offense informing defense.

