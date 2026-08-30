# Study Guide — AI-Integrated Red Team Toolkit

Everything you need to defend this project in class: concept primers, framework
mappings, per-project viva questions **with model answers**, and hands-on labs.

---

## 1. Core Vocabulary (learn these cold)

| Term | One-line definition |
|---|---|
| OSINT | Intelligence from publicly available sources; passive recon touches no target systems |
| RDAP | Registration Data Access Protocol — WHOIS replacement for domain registration data |
| CT logs | Certificate Transparency — public append-only logs of every TLS cert issued |
| SPF / DMARC / CAA | DNS controls: who may send mail for a domain / policy+reporting on spoofing / which CAs may issue certs |
| Prompt injection | Overriding an LLM's instructions via crafted input (OWASP LLM01) |
| Direct vs indirect injection | Attacker types at the model vs payload arrives via retrieved content |
| LLM-as-judge | Using a second model to score outputs; fast but needs deterministic corroboration |
| SARIF | Static Analysis Results Interchange Format — standard findings exchange for CI |
| Beaconing | Periodic compromised-host→C2 check-ins; jitter randomizes timing to defeat alerts |
| Dwell time | Time attacker stays undetected; schedule-aware beaconing maximizes it |
| Sigma | YAML signature format for log detections, portable across SIEMs |
| Suricata | Network IDS/IPS with rule-based alerting |
| CVSS / CWE / CVE | Severity scoring system / weakness taxonomy / vulnerability identifiers |
| Kill date | Hardcoded time after which malware self-terminates |

## 2. Framework Mappings

| Project | MITRE ATT&CK | Other frameworks |
|---|---|---|
| P1 recon-agent | T1595 (active scan), T1592 (host info), T1589 (identity info), T1597 (registration) | PTES: Intelligence Gathering |
| P2 fuzzer | ATLAS: LLM Prompt Injection | OWASP LLM01, OWASP ASVS-style fuzzing loop |
| P3 phish-sim | T1566 (Phishing) | ISO 27001 A.6.3 awareness; NIST CSF PR.AT |
| P4 c2-lab | T1071.001 (Web C2), T1090 (proxy), TA0011 C2 | MITRE CTID detection engineering practice |
| P5 copilot | — (post-engagement) | NIST SP 800-115 §reporting; PTES: Reporting |

## 3. Project 1 — AI Recon Agent

**Learning objectives:** explain passive vs active recon; read SPF/DMARC records;
justify why evidence-grounded LLM prompting reduces hallucination.

**How the AI works:** collectors emit JSON → prompt includes *only* that JSON → system
prompt forbids unsupported claims → rule-based exposure score is shown alongside so the
model must agree or disagree.

**Viva Q&A**

1. *Why is the score deterministic if we have an LLM?*
   Severity math must be auditable and repeatable; the model narrates and reasons over
   evidence but cannot silently change numbers. Showing both invites critique — good
   security practice.
2. *Which collector gives the most subdomains and why?* crt.sh — every TLS cert ever
   issued for the domain lists SAN hostnames.
3. *What does `p=none` in DMARC mean?* Monitor-only policy; spoofed mail is not rejected.
4. *Is fetching the web root active?* Yes — hence `--include-http` default-off.
5. *What breaks first when crt.sh rate-limits?* That collector returns ok:false; the
   warning list shows it and analysis continues — graceful degradation by design.

**Lab:** run against your own lab domain twice, then `--baseline` diff and explain each
change line.

## 4. Project 2 — LLM Injection Fuzzer

**Objectives:** classify injection techniques; argue regex-vs-judge tradeoffs; describe
closed-loop adaptive attack automation.

**Key design:** detectors are high-recall/low-cost regexes; judge adds precision for
paraphrased compliance; mutator closes the loop on near-misses (score ≥ 3).

**Viva Q&A**

1. *Difference between jailbreak and prompt injection?* Jailbreak = bypassing the
   model's safety alignment; injection = overriding application-level instructions,
   often via data channel. Same primitive, different trust boundary.
2. *Why multi-turn chains succeed where one-shots fail?* Trust/context ramp: each turn
   normalizes the next; filters evaluate single messages.
3. *Can the judge be fooled?* Yes — prompt-inject-the-judge; mitigated by deterministic
   detector override (regex hit forces compromise verdict).
4. *What does resilience % measure?* Share of attempts not compromised — a regression
   KPI across defense-prompt versions.
5. *Why SARIF?* Standardizes results so CI platforms treat LLM findings like SAST ones.

**Lab:** point at Ollama with a weak system prompt, note resilience %; add explicit
output constraints + input delimiter discipline; re-run; present delta.

## 5. Project 3 — Phishing Awareness Simulator

**Objectives:** enumerate red-flag taxonomy; explain dual-attestation safety design;
interpret click metrics ethically.

**Safety chain:** config validation → typed attestation → content blocklist →
regenerate-on-violation → `X-PhishSim` header → send lock (`allow_send` + `--send`).

**Viva Q&A**

1. *Why unique tokens per recipient?* Attribution without tracking pixels; privacy-
   friendlier than pixel beacons; enables per-template metrics.
2. *Legal/ethical difference vs real phishing?* Authorization, benign payloads,
   marked headers, education landing page, no credential capture.
3. *What makes a good red flag set?* Observable without clicking (sender mismatch),
   psychological (urgency), technical (link/label mismatch).
4. *How do you prevent trainer abuse?* Recipient cap, allowlist-format emails, named
   approver in config, blocklist validation.
5. *Metric pitfalls?* Small samples; click ≠ compromise; never shame clickers publicly.

**Lab:** generate a dry-run campaign, serve landing.py, click your own link, produce
metrics.md.

## 6. Project 4 — C2 Detection Lab

**Objectives:** quantify jitter's effect on detection; write/read Sigma + Suricata;
explain regularity index & autocorrelation.

**Viva Q&A**

1. *Why does jitter defeat naive alerts?* Fixed-interval thresholds trip on variance;
   stdev grows with jitter %, widening the distribution beyond alert windows.
2. *Interpret regularity index.* 1/(1+cv): ~1 metronomic (easy to detect), →0 chaotic.
3. *What does lag-1 autocorrelation near 0 tell you?* Intervals independent — pure
   jitter, no hidden schedule.
4. *Why base64 task encoding matters for blue teams?* Content obfuscation shifts
   detections from strings to metadata (timing, sizes, TLS/JA3-style features).
5. *Why is office-hours beaconing effective?* Blends into human traffic diurnal cycle;
   nightly batch alerts ignore daytime noise.
6. *Ethical boundary of this lab?* Loopback/private IP guard, simulated execution only,
   telemetry hashing instead of storage.

**Lab:** run `regular` vs `bursty` presets, `analyze --compare`, draft your own Sigma
rule before revealing the AI's.

## 7. Project 5 — Pentest Report Copilot

**Objectives:** anatomy of professional reports; severity governance; safe LLM use in
client deliverables.

**Viva Q&A**

1. *Where must the LLM NOT decide things?* Severity math, dedupe keys, rankings — all
   deterministic pre-LLM.
2. *What is cross-tool correlation adding?* Service context (banner/version) so impact
   narrative reflects the actual stack, e.g. traversal against nginx 1.18.
3. *Prompt-injection risk from scanner data?* Banner strings could carry hostile text;
   mitigation: sanitize/escape inputs, constrain output schema, human QA gate.
4. *Why batch enrichment (6/batch)?* Cost + context control; failed batches degrade to
   `_pending_` placeholders instead of corrupting the report.
5. *Executive summary rules?* Business risk first; no tool/CVE names unless essential.

**Lab:** run `--no-llm` skeleton, then full pipeline; diff and annotate what the model
added vs invented (if anything).

## 8. Cross-Cutting Questions (any project)

1. *Defend zero-dependency llm_client choice.* Portability, auditability (you can read
   the whole HTTP path), no supply-chain surface; SDKs add convenience not capability.
2. *How do you stop an LLM from fabricating?* Feed structured evidence, forbid
   unsupported claims in system prompt, cite-evidence requirement, keep math outside.
3. *Your threat model for this repo itself?* See `docs/SECURITY_AND_ETHICS.md`.
4. *What would production-hardening add?* Auth on endpoints, secrets manager, async
   queues, RBAC, signed reports, observability.

## 9. Platform Engineering Primer (v3.2)

The suite is now a *platform*, not scripts. Know these terms cold:

| Term | One-line definition |
|---|---|
| Bearer auth | `Authorization: Bearer <token>` header scheme guarding API routes |
| Rate limiting (sliding window) | Per-client request cap over a rolling 60s window |
| Prometheus exposition | Plain-text metric format (`# HELP/# TYPE`, `name value`) scraped by monitors |
| Schema contract | Published JSON Schema that machine outputs must validate against |
| Contract test | CI test proving an emitter still satisfies its published schema |
| ADR | Architecture Decision Record — immutable rationale for a design choice |
| Non-root container | Docker runtime user without root; limits blast radius |
| Health check | Liveness endpoint/container probe distinguishing "up" from "working" |
| Hash chain (audit) | Each log record embeds sha256(prev+payload); edits break the chain at that line |
| Job orchestration | Async submit/poll pattern with worker pool and status lifecycle |
| JUnit XML | CI-standard test results format; here: compromised=failure gates pipelines |
| OpenAPI | Machine-readable HTTP contract served by the API itself |

**Platform Q&A**

1. *Why enforce auth only when a token is configured?* Zero-friction local dev,
   fail-closed in deployment via env; the open mode is loud, not silent.
2. *Why publish schemas instead of trusting code?* Consumers (CI, dashboards) break
   silently when outputs drift; contract tests fail loudly at build time.
3. *What does mypy on the core buy that tests don't?* Tests prove behavior of covered
   paths; types prove shape everywhere, catching defects before any test runs
   (it caught two pre-release).

**Lab:** start `services/api/server.py` with a token set; observe 401 → authorized;
write one custom counter and read it back at `/metrics`.

## 10. Further Reading

- OWASP Top 10 for LLM Apps · MITRE ATLAS case studies
- Sigma HQ rule repositories (find C2 beacon examples)
- NIST SP 800-115 ch. on reporting
- "Prompt Injection" chapter, *Securing AI Systems* (recent survey literature)
