# Project Proposal

**Title:** An AI-Integrated Red Team Toolkit: Automating Reconnaissance, LLM Attack
Simulation, Social-Engineering Training, C2 Detection Engineering, and Penetration-Test
Reporting

**Candidate:** *Royal-Sec Ltd — Authorized Commercial Toolkit*  
**Course:** *Royal-Sec Red Team Operations — Industrial Platform*  
**Supervisor:** *Royal-Sec Core Team (legal@royal-sec.com)* · **Version:** 4.0.0 · **Date:** *2026-08-30*  
> **Note:** This document is archived academic proposal retained for provenance. For current product docs see `README.md`, `BOOK.md`, `EULA.md`, `AUP.md`.

---

## 1. Executive Summary

Modern offensive-security work is constrained by two pressures: manual tradecraft does
not scale, and a brand-new attack surface — LLM-integrated applications — demands
tooling that most curricula have not yet covered. This project delivers five
production-quality, AI-integrated tools spanning the full red-team kill chain
(reconnaissance → application attack → social engineering → command-and-control →
reporting). Every tool couples deterministic security engineering with LLM reasoning
where it adds value (evidence-fused analysis, adversarial payload generation,
detection-authoring, narrative writing) and enforces authorization gates so it can be
safely demonstrated in an academic setting.

## 2. Background & Problem Statement

1. **Reconnaissance is data-heavy.** A domain's attack surface is scattered across DNS,
   certificate transparency logs, archives and mail controls; analysts need fusion, not
   collection.
2. **LLM applications are the new attack surface.** OWASP ranks prompt injection as
   LLM01; defenders lack accessible, reproducible fuzzing harnesses.
3. **Awareness training is hard to localize.** Generic phishing examples fail to teach;
   realistic-but-safe simulations require per-recipient drafting plus measurable outcomes.
4. **Detection engineering needs telemetry.** Blue teams tune against realistic beacon
   patterns (jitter, schedules, dwell time), which are rarely available safely.
5. **Reporting consumes ~30–50% of engagement effort**, yet is the client's primary
   deliverable.

## 3. Aims & Objectives

**Aim:** Build and evaluate an industrial-grade toolkit demonstrating how LLMs augment
each phase of offensive security operations.

| # | Objective (SMART) | Success Criterion |
|---|-------------------|-------------------|
| O1 | Ship five working tools across ATT&CK phases | All demos pass offline runbook |
| O2 | Integrate LLMs substantively, not cosmetically | Each tool has structured evidence→prompt contracts + JSON outputs |
| O3 | Enforce safety engineering | Authorization gates, lab-only guards, content blocklists verified by unit tests |
| O4 | Industrial software practice | 91 unit tests + ruff + strict mypy clean; CI matrix (Linux/Windows x Py3.11/3.13) incl. coverage and release builds |
| O5 | Communicate for academic + industry audiences | Proposal, slides, study guide, runbook, rubric delivered |

## 4. Scope

**In scope:** passive OSINT automation; prompt-injection fuzzing of endpoints you own;
authorized phishing-awareness simulation with click metrics; lab-only C2 telemetry +
AI detection authoring; scanner-output report generation.

**Out of scope:** exploitation of third-party systems; malware development; evasion of
real EDR; autonomous agent execution of attacks; sending email without dual attestation.

## 5. Methodology

Iterative build-evaluate loop per tool: **Design → Implement → Unit-test (offline) →
Adversarial review (red-team your own tool) → Document → Demo**. Architecture decisions:

- **Shared provider-agnostic LLM client** (OpenAI / Anthropic / Ollama) using only the
  standard library — no vendor lock-in, free local demo path.
- **Deterministic-first design:** rules compute scores/rankings; LLMs narrate, mutate,
  and judge on top of structured JSON evidence (mitigates hallucination and keeps
  severity math auditable).
- **Safety-by-construction:** typed attestations (`I AM AUTHORIZED`, `ATTACK`),
  private-IP guards, `X-PhishSim` headers, content blocklists, send locks.

## 6. System Overview

```
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚ Front doors:  unified `rtai` CLI (9 subcommands)            â”‚
        â”‚               REST microservice (authn, rate limit, /metrics)â”‚
        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                    â”‚
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚                rtai_core shared library                     â”‚
        â”‚ providers(OpenAI|Anthropic|Ollama) - config - registry      â”‚
        â”‚ storage(JSONL+SQLite) - models - logging - metrics - retry  â”‚
        â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
               â”‚         â”‚         â”‚         â”‚              â”‚
          P1 recon   P2 fuzzer  P3 phish  P4 c2-lab    P5 copilot
          RDAP/DNS   payloads→  templates→ listener⇄beacon nmap/nuclei/
          CT/TLS/WB  target     landing+   presets/sched  nessus→corr
          →score→diff ↖judge ↗  metrics    →analyze→Sigma →narrate→md
```

## 7. Deliverables

| Deliverable | Location |
|---|---|
| Five tools + READMEs | `01-* … 05-*` |
| Shared library (`rtai_core`) | `rtai_core/` |
| Unified product CLI (`rtai`) | console script via pyproject entry point |
| REST API microservice | `services/api/server.py` |
| Container stack | `Dockerfile`, `docker-compose.yml`, `.dockerignore` |
| Schema contracts + contract tests | `schemas/*.json`, `tests/test_contracts.py` |
| Test suite (91 tests) + CI (lint/type/test/release) | `tests/`, `.github/workflows/` |
| This proposal | `docs/PROJECT_PROPOSAL.md` |
| Presentation deck (+ generator) | `docs/PRESENTATION_SLIDES.pptx`, `tools/make_slides.py` |
| Study guide incl. viva Q&A | `docs/STUDY_GUIDE.md` |
| Live-demo runbook | `docs/DEMO_RUNBOOK.md` |
| Grading rubric (self-assessment) | `docs/GRADING_RUBRIC.md` |
| Security, ethics & threat model | `docs/SECURITY_AND_ETHICS.md` |
| Governance & ADRs | `CONTRIBUTING`, `CODEOWNERS`, `docs/adr/` |

## 8. Project Plan (8 weeks)

| Week | Milestone |
|---|---|
| 1 | Literature review (OWASP LLM Top 10, ATT&CK, PTES); proposal approval |
| 2 | Shared LLM client; Project 1 recon MVP |
| 3 | Project 2 fuzzer core + detectors; peer review of prompts |
| 4 | Project 3 campaign builder + safety gates; ethics sign-off |
| 5 | Project 4 detection lab; first Sigma outputs reviewed |
| 6 | Project 5 copilot; cross-tool correlation; v2 feature wave |
| 7 | Hardening: test suite, CI, docs, threat model |
| 8 | Evaluation runs, slides, rehearsal, submission |

## 9. Risks & Mitigations

| Risk | L | I | Mitigation |
|---|---|---|---|
| LLM API cost/availability | M | M | Ollama local fallback; `--no-llm` modes; retries/backoff |
| Model hallucinates findings | M | H | Evidence-only prompting; deterministic scoring shown alongside |
| Tool misuse outside scope | L | H | Attestation gates, IP guards, marker headers, documented ROE |
| crt.sh / rdap rate limits | M | L | Per-collector error isolation; warnings surfaced in reports |
| Time overrun | M | M | Weekly milestones; v1 scope frozen before v2 features |

## 10. Evaluation Plan

- **Functional:** offline demo runbook executes end-to-end (P4 fully offline).
- **Security quality:** fuzzing resilience % tracked across hardened vs default targets;
  detection reports reviewed against Sigma grammar.
- **Code quality:** CI matrix green; unit coverage of all deterministic cores.
- **Communication:** rubric-scored presentation + live demo with fallback plan.

## 11. References

1. OWASP Top 10 for LLM Applications (2025). — owasp.org/www-project-top-10-for-large-language-model-applications
2. MITRE ATT&CK Enterprise Matrix. — attack.mitre.org
3. MITRE ATLAS: Adversarial Threat Landscape for AI Systems. — atlas.mitre.org
4. NIST SP 800-115, Technical Guide to Information Security Testing and Assessment.
5. PTES — Penetration Testing Execution Standard. — pentest-standard.org
6. Greshake et al. (2023), *Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection*.
7. Sigma — Generic Signature Format for SIEM Systems. — sigmahq.io
8. Crothers et al. (2023), *Machine-Generated Text Detection* (context for judge reliability).


