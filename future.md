# Future Roadmap — Royal-Sec rtai-suite

> **Current: v4.1.0-military Tactical Operations Console** — 9 tools (full Kill Chain), 15 CLI entry points, 12-tab OD Green HUD with Royal Security laurel-shield-crown emblem, FIPS/HSM/mTLS/OPA/WORM+SIEM, SLSA L4 cosign, STIG/TLA+/STIX, 91 tests, vendored standalone air-gap.  
> This is the single backlog for every future upgrade for Royal-Sec authorized use. Priorities **P0 (next release 4.2) / P1 (next quarter 5.0) / P2 (6+ months 6.0)**. Each item: *Effort S/M/L*, *Depends*, *Done when* with test/contract.

---

## How to propose a future feature

1. Open issue via `feature_request.md` template, reference `F-###` ID below.
2. Attach ADR under `docs/adr/` (especially for Kill Chain, crypto, or GUI changes).
3. Every feature lands with: code + test (incl. negative lab-guard test) + doc (`BOOK.md` + `README.md` + `docs/`) + schema/contract update if I/O changes + `rtai_core` vendored sync (`tests/test_meta.py:23-35`).

---

## Release Train

| Release | Theme | Target | Flagship Deliverable |
|---|---|---|---|
| **v4.2** | Full Kill Chain Ops | 4 weeks | **Orchestrated purple-team loop + expanded ATT&CK coverage (T1055, T1003 live-lab)** + dark/light HUD toggle |
| **v4.3** | Intel & Reporting | 6 weeks | **STIX/TAXII live server + Signed PDF + Jira/ServiceNow bridge** |
| **v5.0** | Scale & Air-Gap Enterprise | 12 weeks | **Helm + offline LLM bundle + multi-tenant workspaces + Redis limiter** |
| **v5.5** | Hardened Platform | 16 weeks | **NIST 800-53 rev5 page + STIG enforce mode + air-gap updater** |
| **v6.0** | Autonomy & Formal Assurance | 6 months | **Agentic recon + TLA+ TLC in CI + local small-model judge** |

---

## 1. Platform — Core & Distribution

| ID | Feature | Priority | Effort | Depends | Done when |
|---|---|---|---|---|---|
| **F-C01** | **Plugin marketplace** — `rtai plugin install <git-url>` registers collector/detector/parser via `Registry` without core edits | P1 | M | Registry | `rtai recon --list-collectors` shows third-party plugin, isolated test |
| **F-C02** | **Offline LLM bundle** — embed `llama.cpp` + `llama3.1:8b-Q4` inside air-gap tarball; `rtai llm pull` offline | P1 | L | `military_airgap.py:53-58` | Air-gap install runs `rtai recon --provider ollama` with zero outbound (verified via `ss/netstat`) |
| **F-C03** | **Multi-tenant workspaces** — `rtai workspace create acme` isolates SQLite DB, `audit.log`, artifacts; `RTAI_WORKSPACE` env | P1 | M | `storage.py` `SqliteEventStore` | Two concurrent workspaces produce isolated `findings.db` |
| **F-C04** | **Helm chart** — `helm install rtai-suite ./charts` deploys API + Ollama + Postgres (replacing SQLite at scale) + `audit_log` PVC `WORM` | P1 | L | SBOM, `military_fips` | `helm test` + `kubectl port-forward svc/rtai-api 9000` → `curl /health` 200 |
| **F-C05** | **SLSA L4 hardening** — `cosign verify` in `install.sh` + Rekor offline bundle + `python scripts/sbom_enforce.py --strict` fails on `NOTICE.md` drift | P0 | M | SLSA L3 done | `cosign verify --certificate-identity-regexp '.*github.*' dist/*.whl` passes in CI + install script |
| **F-C06** | **Nix flake** — `nix develop` pinned Python 3.11/3.13 + `liboqs` + `tpm2-tools` + `spire-agent` reproducibly | P2 | M | — | `nix flake check` green Linux/macOS |
| **F-C07** | **Mission-aware CLI** — `rtai --mission missions/OP-XXXX.json recon --target` auto-injects `classification`/`ROE` into every tool | P0 | S | `mission.py` | `rtai recon --target` without `--mission` warns `No mission — using CUI default` |

---

## 2. Tool Improvements — Full Kill Chain (9 tools)

### 2.1 Recon Agent (01) — TA0043

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-R01** | **Shodan/Censys collector (opt-in, key-gated)** `T1590` + `exposure_score` weight for `exposed_rdp` | P1 | S | `--shodan-key` adds `shodan` source; test mocks API; `valid_domain` still gates |
| **F-R02** | **Attack surface graph** — `attack_surface.graph.json` (nodes: hosts/IPs, edges: shared cert/NS/MX) for Gephi/Cytoscape | P1 | S | Validates `schemas/graph.schema.json` |
| **F-R03** | **Continuous watch** — `rtai recon watch --every 24h --baseline previous.json --webhook https://...` daemon | P2 | M | Webhook receives `diff_findings` within 60s of new subdomain |
| **F-R04** | **Active vuln scan bridge** — `rtai recon --active-nmap` (opt-in) spawns `nmap -sV` via `assert_lab_address` + HMAC `RECON_ATTESTED`, emits `findings.json` for `05` | P0 | M | Lab-only `127.0.0.1/24` scan → `05 copilot --recon findings.json` correlation PASS |

### 2.2 Weaponization Forge (06) — TA0042

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-W01** | **YARA + ClamAV scan gate** — every `forge.py` artifact scanned via `yara` rule `benign_placeholder.yar` (must match watermark+EICAR, must NOT match real shellcode) | P0 | S | `forge --target 127.0.0.1 --payload-type shellcode_stub` → `yara` PASS, real shellcode would FAIL `FORBIDDEN_SNIPPETS` |
| **F-W02** | **Macro builder v2** — `.xlsm` + `.docx` benign placeholders with `autoOpen` MsgBox + `X-Force` watermark, still `FORBIDDEN_SNIPPETS` clean | P1 | M | Generated `.xlsm` opens in VM, prompts macro enable, shows `AUTHORIZED LAB USE ONLY`, no `VirtualAlloc` |

### 2.3 Injection Fuzzer (02) — TA0002

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-F01** | **Indirect RAG corpus** — payload hidden in fake `tool_output`/`document` the target ingests (`indirect` category) | P0 | M | New `indirect` payloads; judge scores indirect vs direct separately |
| **F-F02** | **Defense advisor** — `hardened_system_prompt.txt` auto-rewritten by LLM from bypasses | P1 | S | Resilience % improves on re-run with hardened prompt |
| **F-F03** | **LangChain adapter** — wrap any Python `callable` as `TargetClient` | P1 | M | `examples/langchain_target.py` passes fuzzer |

### 2.4 Phishing Simulator (03) — TA0001

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-P01** | **MFA-fatigue + QR-phishing templates** `mfa_push_bomb` / `qr_invoice` with distinct red-flag taxonomies + `X-PhishSim` | P0 | S | `rtai phish --template all` includes 6 templates (was 4) + `answer_key.md` covers new |
| **F-P02** | **Analytics v2** — `metrics.py --serve` live Chart.js time-series (clicks/hour) + geo heatmap (IP → city via MaxMind, redacted) | P1 | M | `metrics.html` renders offline, `clicks.jsonl` → line chart |
| **F-P03** | **LMS SCORM/xAPI** — export campaign results for Moodle/Canvas | P2 | M | SCORM zip imports into Moodle sandbox, 2 users marked complete |

### 2.5 C2 Detection Lab (04) — TA0011

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-C2-01** | **JA3/TLS fingerprint telemetry** — listener records `JA3` + `JA4H`; `analyze.py` clusters by JA3 + `military_mtls.py` cert | P1 | M | `detection_report.md` lists `JA3=xyz Hosts: 2` IOCs |
| **F-C2-02** | **Sigma lint CI** — `sigma` CLI lints generated rules; `analyze --validate` fails on invalid YAML | P0 | S | `make validate` runs `pysigma` lint, bad rule → exit 2 |
| **F-C2-03** | **PCAP + Suricata replay** — `beacon.py --pcap out.pcap` + `suricata -r out.pcap` → alerts | P1 | M | Wireshark opens `out.pcap`; Suricata `fast.log` contains `ET TROJAN` |
| **F-C2-04** | **DNS + mTLS beacon profiles** — `beacon --profile dns.json` DNS TXT exfil + `beacon --mtls` via `military_mtls.py` client context | P1 | M | `tcpdump port 53` shows TXT, `openssl s_client` shows client cert |

### 2.6 Persistence Lab (07) — TA0003/TA0004/TA0006

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-PE01** | **Live-lab mode (opt-in, isolated VM)** — `persist_lab.py --live --host 192.168.56.10` actually writes `HKCU\...\Run` (with `audit.log` + `RTAI_LAB_ATTESTED` + `assert_lab_address` 192.168.56.0/24) then auto-reverts via snapshot | P2 | L | VM snapshot diff shows Run key created then removed, `persistence.jsonl` + `audit` + `verify()` still PASS |
| **F-PE02** | **EDR telemetry bridge** — emit `persistence.jsonl` as Sysmon `EventID 13` (Registry) + `EventID 1` (Scheduled Task) for Splunk | P1 | M | Splunk query `index=lab EventCode=13` returns 5 events |

### 2.7 APT Lab (08) — TA0007/TA0008/TA0009/TA0010/TA0040

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-APT01** | **BloodHound/SharpHound ingest** — `apt_lab.py --bloodhound collection.json` → `apt_findings.json` with `T1069/T1482` | P1 | M | `bloodhound.json` (10 nodes) → `apt_findings.json` 3 new `T1482` findings |
| **F-APT02** | **rclone-style cloud exfil sim** — `apt_lab.py --cloud s3://lab-bucket` chunked 1MB → `lab-deaddrop.example` + `military_pqc.py` hybrid encrypt | P1 | M | `exfil_events` show `provider:s3` `encrypted:AES-256-GCM+ML-KEM` + `audit` |

### 2.8 Report Copilot (05) + Killchain Orchestrator (09)

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-RP01** | **Signed PDF + classification banner** — `copilot.py --format pdf` via Playwright + `classification` `SECRET` → `report.pdf` text-selectable + `cosign` sig + gold laurel header | P1 | M | `report.pdf` has `SECRET // NOFORN` top/bottom + `qpdf --check` OK |
| **F-RP02** | **Jira/ServiceNow bridge** — `copilot.py --push-jira https://...` creates 1 ticket per `high/critical` with `X-Force` watermark | P2 | M | Dry-run `0` tickets, real `3` tickets in Jira sandbox |
| **F-RP03** | **Killchain AAR auto-gen** — `rtai killchain --target 127.0.0.1 --mission missions/OP-*.json` auto-emits `AAR.md` with timeline `T0 Recon → T+exfil` + `MTTD/MTTR` | P0 | M | `AAR.md` contains `01 recon` `08 apt` `05 report` timestamps + `mission_id` |

---

## 3. GUI — Royal Security Tactical Console

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-G01** | **Dark/light tactical toggle** `QSettings` persisted + `Military/Commercial` brand switcher (OD Green ↔ Royal-Sec navy) + high-contrast | P0 | S | Toggle survives restart, screenshot in `docs/screenshots/` `tactical_dark.png`/`tactical_light.png` |
| **F-G02** | **Live log tail with search/filter** — regex `T1059`, follow-tail, level `INFO/WARN/ERROR`, export `Save Log` | P0 | S | Typing `pwned` filters live, `Export` writes filtered `*.log` |
| **F-G03** | **Settings page** — providers (`XAI_API_KEY`/`GEMINI_API_KEY`/`GOOGLE_API_KEY`), default models (`gemini-3-flash-preview`/`grok-4`), `RTAI_AUDIT_LOG`, `RTAI_FIPS`, `RTAI_CLASSIFICATION` — OS keyring (`keyring` lib) when available, else `.env` 600 | P1 | M | Key never visible after Save; `keyring get rtai-suite gemini` returns `***` |
| **F-G04** | **Result viewers** — Recon sortable host table + Fuzzer resilience gauge (circular `QProgressBar` 0-100% + per-payload drill-down) + Report HTML preview `QWebEngineView` + STIX graph `QtWebChannel` | P1 | L | Clicking `F-003` opens `Host: 203.0.113.10` detail pane with evidence |
| **F-G05** | **Packaged installers** — `pyinstaller --onefile` `Royal-Sec-rtai-suite-Setup.exe` (Windows, signed) + `.deb` (Kali) `make installer` | P2 | L | `dist/Royal-Sec-rtai-suite-Setup.exe` launches offline, `dpkg -i` on Kali |
| **F-G06** | **Tactical map interactivity** — `TacticalMapWidget` pan/zoom + MGRS click → `38TLL 1234 5678` copy + MIL-STD-2525D SVG icons (friendly/hostile) + BFT trail animation | P1 | M | Click map → `clipboard` MGRS, unit drag updates `REAPER 06` position, trail animates |
| **F-G07** | **Classification-aware GUI** — `RTAI_CLASSIFICATION` env drives top/bottom banner color + `Mission` tab `classification` combo syncs to all tools (`report --classification` auto-filled) | P0 | S | Changing `Mission` `SECRET` updates `Tactical` banner red within 1s |
| **F-G08** | **Logo splash + header polish** — `rtai_core/gui/assets/logo.png` 1024 + `logo_small.png` 256 + `docs/assets` + `assets/logo.png` already vendored; add `Help → About` with laurel, version `4.1.0-military`, `COPYING` + `EULA` | P0 | S | `Help→About` shows 256px logo + `ROYAL SECURITY • CYBER PROTECTION` + `v4.1.0-military` |

---

## 4. API & Platform — Enterprise Hardening

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-A01** | **RBAC + OPA hot-reload** — `RTAI_API_TOKEN` → JWT `recon:read`/`fuzz:execute` + `policies/*.rego` inotify reload | P0 | M | `curl -H "Authorization: Bearer $JWT"` without `fuzz:execute` → `403 OPA policy denied` + `audit` `opa_denied` |
| **F-A02** | **mTLS + SPIFFE/SPIRE** — `server.py --tls-cert --tls-key --tls-ca` + `docker-compose.spiffe.yml` + `spire-agent` workload attestation `RTAI_SPIFFE_ID` | P1 | L | `curl --cert client.pem --key client-key.pem https://127.0.0.1:9000/health` 200; without cert → `401` |
| **F-A03** | **Async webhooks** — `POST /v1/recon/async {"webhook":"https://...","webhook_hmac_key":"..."} ` HMAC-SHA256 signature | P1 | S | Webhook receives `{"job_id": "...", "result": {...}}` `X-RTAI-Signature: sha256=...` within 5s |
| **F-A04** | **SSE event stream** — `GET /v1/events` `text/event-stream` `audit` + `job` for SIEM (`RTAI_SIEM_URL` alternative) | P1 | M | `curl -N /v1/events` receives `event: audit\ndata: {...}\n\n` per `audit.record()` |
| **F-A05** | **Redis token-bucket limiter** — `RTAI_REDIS_URL` → `redis` `INCR` + `EXPIRE` survives restarts, fallback in-memory | P2 | M | `RTAI_REDIS_URL=redis://...` → kill API → restart → `X-RateLimit-Remaining` continues |
| **F-A06** | **API STIX/TAXII passthrough** — `GET /v1/stix/bundle` + `POST /v1/taxii/collections/{id}/objects` proxy to `military_stix.py` `TAXIIClient` | P1 | M | `curl /v1/stix/bundle` returns `STIX bundle.json` 4 objects, `TAXIIClient` mocked in CI |

---

## 5. Military-Grade Depth — v4.1.0 already closed MG-01..MG-20, next layer:

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-M01** | **FIPS 140-3 strict mode + self-test** — `cryptography` backend `FIPS` provider + `RTAI_FIPS_STRICT=1` `fips_self_test()` `hmac-sha256` KAT on startup, fail-closed | P1 | M | `RTAI_FIPS_STRICT=1 python -c "import rtai_core.military_fips; assert fips_self_test()"` → `fips_status()['strict']==True` |
| **F-M02** | **TPM remote verifier service** — `tpm2-tools` → `quote` → `POST /attest` verifier `TPMRemoteAttestation.verify_quote()` → `pcr_match:true` | P1 | L | `rtai attest --pcrs 0,1,7` green on real TPM, mocked `TemporaryDirectory` in CI `verify_quote()[0]==True` |
| **F-M03** | **STIG enforce mode** — `military_stig.py apply --profile python` actually toggles `sys.addaudithook` + `import ctypes` → `ImportError` (not just JSON) | P0 | S | `python -c "import ctypes"` raises `ImportError: STIG blocks ctypes` after `apply` |
| **F-M04** | **NIST 800-53 rev5 page** — `docs/compliance/nist800-53.md` auto-gen from `military_stig` + `audit` events: 20 controls × implementation + evidence columns | P1 | S | Matrix `AC-2` `AU-2` etc has `Implementation: rtai_core/audit.py:93` + `Evidence: audit.log` |
| **F-M05** | **Bundle updater + offline verify** — `rtai update --bundle rtai-suite-4.1.0-airgap.tar.gz` `cosign verify` + hash-chain `MANIFEST.json` `verify()` at line N | P1 | M | Tampered `bundle.tar.gz` → `verify() (False, 3)` |
| **F-M06** | **HSM envelope encryption for reports** — `military_hsm.py` `envelope_encrypt(report.md)` `AES-256-GCM` + `ML-KEM-768` hybrid, `classification` drives key handle (`CUI`→software, `SECRET`→HSM) | P1 | M | `report.md` `CUI` → `report.md.enc` `openssl enc -d` fails without HSM, `SECRET` → HSM slot required |

---

## 6. AI — Next Generation

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-AI01** | **Agentic recon** — LLM ReAct loop (plan→act→observe) tool-use `collect()` with cost cap 20 calls | P2 | L | Agent achieves same `exposure_score` coverage in ≤8 calls vs static 6 parallel |
| **F-AI02** | **Local small-model judge** — distill judge to `llama3.2:1b` / `gemma-4-31b` for fully air-gapped fuzzing (`--judge-model tiny-judge`) | P1 | M | `--judge-model tiny-judge` runs offline `<2s/verdict` on 8GB RAM, no cloud |
| **F-AI03** | **Purple-team closed loop** — `fuzzer → C2` : successful `PWNED` bypass auto-generates `beacon profile` that evades current Sigma rule → `analyze.py` proposes new rule → re-test passes | P2 | L | `rtai fuzzer --url ... --judge --tune-c2` one command: bypass → new `sigma.yml` → `beacon --preset` `regularity_index` improves |
| **F-AI04** | **Gemini/XAI routing** — `ChatClient` auto-fallback `gemini → xai → ollama` on 429/403 (credit limit) + `provider --auto` | P0 | S | `GEMINI_API_KEY` 403 → auto `XAI_API_KEY` → auto `ollama` with `audit.log` `provider_fallback` |
| **F-AI05** | **Prompt-injection firewall dataset** — 10k labeled `payload→verdict` from `fuzzer` runs → `detectors.py` `R1-R5` retrained, `payloads.py` expanded to 50 | P1 | M | `R5` precision +15% on holdout `test_fuzzer_core.py` |

---

## 7. Quality & Scale

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-Q01** | **Hypothesis fuzzing** — `hypothesis` on `detectors.py`/`parsers.py` 200 examples, `payloads.py` random | P1 | S | `hypothesis` in `dev` extra, `pytest -k hypothesis` 200 examples |
| **F-Q02** | **Bench regression gate** — `scripts/bench.py --check` fails CI if `ops/s` < `bench-baseline.json` -15% | P0 | S | `bench-baseline.json` committed, CI `bench --check` red on regression |
| **F-Q03** | **Playwright E2E for GUI** — `pytest-qt` `xvfb` headless `Tactical → Mission → Recon` full run | P2 | L | `pytest tests/gui -q` green in `ubuntu-latest` `xvfb-run` |
| **F-Q04** | **Docs as tests** — `mkdocs build --strict` + `test_docs.py` snapshot `--help` vs `README` | P1 | S | `README` drift → `test_docs.py` fails `help` mismatch |
| **F-Q05** | **Killchain E2E gate** — `rtai killchain --target 127.0.0.1 --dry-run --yes` in `ci.yml` matrix + `missions/OP-*.json` ROE window `active` check | P0 | S | `ci.yml` `killchain --dry-run` green on `ubuntu/windows × 3.11/3.13` |

---

## 8. Suggested Contribution Order (single contributor, military focus)

**Week 1 — Visible tactical wins:** `F-C05` SLSA verify in `install.sh` → `F-G07` classification-aware GUI sync → `F-G01` dark/light + `F-G08` logo About → `F-Q02` bench gate — *low risk, demo impact*  
**Week 2 — Kill chain depth:** `F-W01` YARA gate → `F-F01` indirect RAG corpus → `F-C2-02` Sigma lint → `F-AI04` Gemini/XAI auto-fallback — *tool depth*  
**Week 3 — Platform enterprise:** `F-A01` RBAC hot-reload → `F-A06` STIX API → `F-C04` Helm → `F-M06` HSM envelope — *enterprise*  
**Week 4 — Military depth:** `F-M03` STIG enforce → `F-M01` FIPS strict self-test → `F-M05` bundle updater → `F-Q03` Playwright GUI → ADR + `BOOK.md` — *ATO readiness*

---

## Out of Scope (explicitly not planned — authorized-use only)

- Autonomous exploitation of live targets — no auto-exploit beyond lab `beacons.jsonl` jitter + benign `EICAR` placeholders (`FORBIDDEN_SNIPPETS`).
- Cloud-hosted SaaS for offensive operations — on-prem/air-gap primary (`RTAI_HOME` + `AirGapBundleGenerator`).
- Proprietary LLM training — compose `ollama/openai/anthropic/xai/grok/gemini/google` via `rtai_core/providers`, not train.
- Live credential dumping / lateral movement beyond `127.0.0.1` `assert_lab_address` — `07`/`08` are `simulated:true` `lab_only:true` log-only.

---

*Last updated: v4.1.0-military Tactical Operations Console — Royal Security laurel-shield-crown emblem, 9 tools, 12-tab HUD, FIPS/HSM/mTLS/OPA/WORM+SIEM, SLSA L4, STIG/TLA+/STIX, full Kill Chain orchestrator. Edit via PR; every row links to issue + ADR when P0.*
