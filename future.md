# Future Roadmap — Royal-Sec rtai-suite

> **Current: v4.0.0 Military-Grade Platform** — 91 tests, 5 tools, unified `rtai` CLI, Royal-Sec GUI, REST API, SBOM/SLSA, hash-chained audit.  
> This document is the single backlog for every future upgrade. Priorities use **P0 (next release) / P1 (next quarter) / P2 (next year)**. Each item has *Effort*, *Depends*, and *Done when*.

---

## How to propose a future feature

1. Open an issue using `feature_request.md` template.
2. Reference an `F-###` ID below and attach an ADR under `docs/adr/`.
3. Every feature lands with: code + test + doc + schema/contract update if it changes I/O.

---

## Release Train

| Release | Theme | Target | Flagship Deliverable |
|---|---|---|---|
| **v4.1** | Operator Experience | 4 weeks | Web dashboard + RBAC (P0) |
| **v4.2** | Detection Fabric | 8 weeks | Live purple-team loop (P0) |
| **v5.0** | Scale & Air-Gap Enterprise | 12 weeks | Kubernetes, offline LLM, multi-tenant (P1) |
| **v6.0** | Autonomy & Formal Assurance | 6 months | Agentic red-team + TLA+ verified core (P2) |

---

## 1. Platform — Core & Distribution

| ID | Feature | Priority | Effort | Depends | Done when |
|---|---|---|---|---|---|
| **F-C01** | **Plugin marketplace** — `rtai plugin install <git-url>` installs a new collector/detector/parser as a `Registry` entry without core edits | P1 | M | Registry | `rtai recon --list-collectors` shows third-party plugin, test installs in isolation |
| **F-C02** | **Offline LLM bundle** — embed `llama.cpp` + quantized `llama3.1:8b` inside air-gap tarball; `rtai llm pull` works offline | P1 | L | AirGapBundleGenerator | Air-gap install runs `rtai recon --provider ollama` with zero outbound |
| **F-C03** | **Multi-tenant workspaces** — `rtai workspace create acme` isolates SQLite DB, audit log, and artifact dirs; `RTAI_WORKSPACE` env | P1 | M | storage.py | Two concurrent workspaces produce isolated `findings.db` files |
| **F-C04** | **Kubernetes Helm chart** — `helm install rtai-suite ./charts` deploys API + Ollama + Postgres (replacing SQLite at scale) | P1 | L | SBOM, storage abstraction | `helm test` + `kubectl port-forward svc/rtai-api 9000` → `curl /health` 200 |
| **F-C05** | **SLSA Level 4** — Sigstore/cosign keyless signing in `release.yml` + Rekor transparency log + `cosign verify` in install script | P0 | M | SLSA L3 (done) | `cosign verify` passes on `dist/*.whl` in CI |
| **F-C06** | **Nix flake** — `nix develop` gives pinned Python 3.11/3.13 + all native deps (liboqs optional) reproducibly | P2 | M | — | `nix flake check` green on Linux/macOS |

---

## 2. Tool Improvements — Per Project

### 2.1 Recon Agent (P1)

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-R01** | **Shodan/Censys collector (opt-in, key-gated)** + `exposure_score` weighting for exposed services | P1 | S | `--shodan-key` adds `shodan` source; test mocks API |
| **F-R02** | **Graph output** — emit `attack_surface.graph.json` (nodes: hosts, edges: shared certs/NS) for Gephi/Cytoscape | P1 | S | Graph file validates against `schemas/graph.schema.json` |
| **F-R03** | **Continuous watch** — `rtai recon watch --every 24h --baseline` daemon + webhook on new subdomain | P2 | M | Daemon + webhook test with stub server |

### 2.2 Injection Fuzzer (P2)

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-F01** | **Indirect injection corpus** — retrieve-augmented attacks: payload hidden in fake tool output the target LLM ingests | P0 | M | New `indirect` category; judge scores indirect vs direct separately |
| **F-F02** | **Defense advisor** — after fuzzing, emit `hardened_system_prompt.txt` auto-rewritten by LLM from successful bypasses | P1 | S | Output file contains stricter delimiters; resilience % improves on re-run |
| **F-F03** | **Live target adapter** — plug for LangChain/LLM app under test (wrap any Python callable as `TargetClient`) | P1 | M | Example `examples/langchain_target.py` passes fuzzer |

### 2.3 Phishing Simulator (P3)

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-P01** | **MFA-fatigue template + QR-phishing** — new `mfa_push_bomb` and `qr_invoice` templates with distinct red-flag taxonomies | P0 | S | Templates appear in `rtai phish --template all` + answer_key covers them |
| **F-P02** | **Analytics dashboard v2** — `metrics.py --serve` live HTML with Chart.js time-series (clicks over hours) | P1 | M | `metrics.html` renders bar + line chart offline |
| **F-P03** | **LMS integration** — SCORM/xAPI export of campaign results for Moodle/Canvas | P2 | M | Generated SCORM zip imports into Moodle sandbox |

### 2.4 C2 Detection Lab (P4)

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-C2-01** | **JA3/TLS fingerprint telemetry** — listener records JA3 hashes; `analyze.py` clusters beacons by JA3 | P1 | M | `detection_report.md` lists JA3 IOCs |
| **F-C2-02** | **Sigma rule validation CI** — `sigma` CLI lints generated rules; `analyze --validate` fails build on invalid YAML | P0 | S | `make validate` runs sigma lint |
| **F-C2-03** | **PCAP replay** — `beacon.py --pcap out.pcap` writes pcap for Wireshark/Suricata offline testing | P1 | M | Wireshark opens pcap; Suricata alerts fire |

### 2.5 Report Copilot (P5)

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-RP01** | **Signed PDF export** — `copilot.py --format pdf` via headless Chromium (Playwright) with Royal-Sec watermark | P1 | M | `report.pdf` is text-selectable + signed |
| **F-RP02** | **Jira/ServiceNow bridge** — `copilot.py --push-jira https://...` creates tickets per finding | P2 | M | Dry-run creates no ticket; real run creates 1 ticket per high/critical |
| **F-RP03** | **Executive slide deck** — auto-generate `report.pptx` (executive summary + risk matrix chart) | P1 | S | `tools/make_slides.py` re-used; deck has 5 slides + chart |

---

## 3. GUI — Royal-Sec Console

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-G01** | **Dark/light theme toggle** (persisted via `QSettings`) + Royal-Sec brand switcher | P0 | S | Theme survives restart; screenshots in `docs/screenshots/` |
| **F-G02** | **Live log tail with search/filter** — regex filter, follow-tail toggle, export to file | P0 | S | Typing `error` filters output live |
| **F-G03** | **Settings page** — provider keys, default models, audit log path, API token — persisted securely (OS keyring when available) | P1 | M | Keys never appear in `QLineEdit` after save; stored in keyring |
| **F-G04** | **Result viewers** — Recon: sortable host table; Fuzzer: resilience gauge + per-payload drill-down; Report: HTML preview pane | P1 | L | Clicking a finding row opens detail pane |
| **F-G05** | **Packaged installers** — `pyinstaller` one-file exe (Windows) + `.deb` (Kali) via `make installer` | P2 | L | `dist/Royal-Sec-rtai-suite-Setup.exe` launches offline |

---

## 4. API & Platform — Enterprise Hardening

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-A01** | **RBAC + OPA bundles** — `RTAI_API_TOKEN` → JWT with `recon:read`, `fuzz:execute` scopes; `policies/*.rego` hot-reloaded | P0 | M | Request without scope → 403 + `auth_failure` audit entry |
| **F-A02** | **mTLS + SPIFFE** — `server.py --cert --key --ca`; SPIRE workload attestation path tested in `docker-compose.spiffe.yml` | P1 | L | `curl --cert client.pem --key client-key.pem https://.../v1/recon` 200; without cert → 401 |
| **F-A03** | **Async job webhooks** — `POST /v1/recon/async {"webhook": "https://..."}` POSTs result on completion with HMAC signature | P1 | S | Webhook receives signed JSON within 5s of job done |
| **F-A04** | **Event streaming** — `GET /v1/events` SSE stream of `audit` + `job` events for SIEM forwarding | P1 | M | `curl -N /v1/events` receives `data: {...}\n\n` per event |
| **F-A05** | **Rate-limit by token bucket + Redis backend** (optional, falls back to in-memory) | P2 | M | `RTAI_REDIS_URL` set → limiter survives API restarts |

---

## 5. Military-Grade Depth

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-M01** | **FIPS 140-3 mode** — `cryptography` with `backend` forced to FIPS provider; self-test on startup | P1 | M | `python -c "import rtai_core.military_pqc; assert fips_self_test()"` |
| **F-M02** | **TPM remote attestation flow end-to-end** — `tpm2-tools` → quote → verifier service → `/attest` endpoint returns `pcr_match: true` | P1 | L | `rtai attest --pcrs 0,1,7` green on real TPM, mocked in CI |
| **F-M03** | **STIG auto-remediation scripts** — `military_stig.py apply --profile python` actually toggles `sys.addaudithook` + blocks `ctypes` at runtime (not just generates JSON) | P0 | S | `python -c "import ctypes"` raises `ImportError` after STIG apply |
| **F-M04** | **NIST 800-53 rev5 control matrix page** — `docs/compliance/nist800-53.md` auto-generated from `military_stig` + audit events | P1 | S | Matrix has 20 controls × implementation + evidence columns |
| **F-M05** | **Air-gap bundle signing + offline updater** — `cosign sign-blob` for bundle + `rtai update --bundle rtai-suite-4.1.0-airgap.tar.gz` with hash-chain verification | P1 | M | Tampered bundle fails `verify()` at line N |

---

## 6. AI — Next Generation

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-AI01** | **Agentic recon** — LLM plans its own collector sequence (ReAct loop) with tool-use, cost-capped at N LLM calls | P2 | L | Agent achieves same coverage in fewer calls vs static parallel run |
| **F-AI02** | **Local small-model judge** — distill judge to 1B model (e.g., `llama3.2:1b`) for fully air-gapped fuzzing without cloud | P1 | M | `--judge-model tiny-judge` runs offline <2s per verdict |
| **F-AI03** | **Purple-team closed loop** — fuzzer → detection-lab: successful bypass auto-generates beacon profile that evades current Sigma rule → new rule proposed | P2 | L | One command demonstrates bypass → new rule → re-test passes |

---

## 7. Quality & Scale

| ID | Feature | Priority | Effort | Done when |
|---|---|---|---|---|
| **F-Q01** | **Fuzz the fuzzers** — property-based tests (Hypothesis) for detectors/parsers against random payloads | P1 | S | `hypothesis` in `dev` extra; CI runs 200 examples |
| **F-Q02** | **Benchmark regression gate** — `scripts/bench.py --check` fails CI if ops/s drops >15% vs baseline file | P0 | S | `bench-baseline.json` committed; CI diff fails build |
| **F-Q03** | **E2E Playwright tests for GUI** — headless `pytest-qt` drives each tab through a full run | P2 | L | `pytest tests/gui -q` green in CI (xvfb) |
| **F-Q04** | **Docs as tests** — `mkdocs build --strict` in CI; every CLI `--help` output is snapshot-tested | P1 | S | `test_docs.py` fails if `--help` drifts from README |

---

## 8. Suggested Contribution Order (for a single contributor)

**Week 1:** F-C05 (SLSA sig) → F-G01 (theme) → F-G02 (log filter) → F-Q02 (bench gate) — *visible wins, low risk*  
**Week 2:** F-P01 (MFA template) → F-F01 (indirect corpus) → F-C2-02 (Sigma lint) — *tool depth*  
**Week 3:** F-A01 (RBAC) → F-A03 (webhooks) → F-C04 (Helm) — *platform enterprise*  
**Week 4:** F-M03 (STIG enforce) → F-M05 (bundle updater) → ADR + docs — *military depth*

---

## Out of Scope (explicitly not planned)

- Autonomous exploitation of live targets — toolkit stays **authorized-use only**; no auto-exploit beyond lab beacons.
- Cloud-hosted SaaS — on-prem/air-gap remains the primary deployment model.
- Proprietary LLM training — we compose existing providers (Ollama/OpenAI/Anthropic), not train.

---

*Last updated: v4.0.0 — Royal-Sec. Edit this file via PR; every row should link to an issue + ADR when it moves to P0.*
