# Slide Deck Outline (v4.0 — Royal-Sec — source of truth mirrored in tools/make_slides.py)

> Regenerate the deck after editing `tools/make_slides.py`:
> `python tools/make_slides.py` (22 slides)

## S1 — Title
**Royal-Sec — AI-Integrated Red Team Toolkit**
Military-Grade Platform • Authorized Use Only
*Royal-Sec Ltd · 2026-08-30 · v4.0.0 Commercial*

## S2 — Agenda
Problem & objectives · architecture · five projects · platform layer · quality gates · demo plan

## S3 — Problem Statement
Manual tradecraft doesn't scale · LLM01 attack surface · awareness training gap · no safe C2 telemetry

## S4 — Objectives
5 ATT&CK-phase tools · substantive AI contracts · safety-by-construction · **91 tests, ruff+mypy, multi-OS CI, release pipeline**

## S5 — Scope & Ethics
Authorized-only scope; typed attestations; STRIDE threat model incl. API service

## S6 — Suite Architecture: One Core, Five Tools
rtai_core layers (providers/config/registry/storage/models) · deterministic-first split · front doors: `rtai` CLI + REST

## S7 — Platform Layer: CLI + REST API ★
9 unified subcommands · bearer auth + sliding-window rate limiting · /health /version /metrics /v1/recon · active recon needs X-RTAI-Authorized

## S8 — Observability & Data Contracts
Console+JSONL structured logging · Prometheus exposition · JSON Schema contracts enforced by contract tests · JSONL + SQLite persistence

## S9 — P1 Recon Agent
Parallel collector registry · deterministic exposure score vs AI opinion · baseline diffing

## S10 — P2 Injection Fuzzer ★
20 payloads + chains + custom arsenals · detector/judge ensemble · adaptive mutation · SARIF + SQLite run log · resilience %

## S11 — P3 Phishing Awareness Sim
Tokenized click tracking + education landing page · safety chain · metrics dashboard

## S12 — P4 C2 Detection Lab ★ offline
Timing presets + schedule evasion + kill switch + encoded tasks · interval statistics · JSONL+SQLite telemetry → AI Sigma/Suricata

## S13 — P5 Report Copilot
Three scanner formats · correlation to service banners · AI narratives/roadmap · severity overrides

## S14 — Cross-Cutting Engineering
Zero-dep runtime core · Registry extension pattern · RetryPolicy · layered config · typed error→exit-code funnel

## S15 — Quality Gates & CI/CD
91 tests (incl. negative safety tests) · ruff caught a real NameError pre-release · mypy strict core · lint job + OS×Python matrix w/ coverage · tag-triggered sdist/wheel + Dependabot

## S16 — Evaluation Highlights
Resilience % delta · regularity index contrast · schema-validated bundles · verification battery caught 4 defects pre-submission

## S17 — Demo Plan (12 min)
Platform tour first (`rtai --list`, live curl) → fuzzer → C2 lab → copilot → fallbacks everywhere

## S18 — Limitations
Hallucination mitigations · passive-first recon · judge override policy · single-node API (no RBAC yet)

## S19 — Future Work
Agent orchestration · async queue + dashboard · JA3/TLS telemetry · Sigma CI validation · signed PDF export · plugin packaging

## S20 — Conclusion
One engineered platform · tested safety · reproducible ($0 Ollama path, containers, 91-test gate)

## S21 — References
OWASP LLM Top 10 · MITRE ATT&CK/ATLAS · NIST SP 800-115 · PTES · Sigma HQ · Greshake et al. 2023

## S22 — Q&A
Backup: architecture diagram · grading rubric · STRIDE threat model

