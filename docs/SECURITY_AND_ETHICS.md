# Security, Ethics & Threat Model

## 1. Authorization Framework

| Control | Where | Enforcement |
|---|---|---|
| Typed attestation | P2 (`ATTACK`), P3 (`I AM AUTHORIZED`) | Interactive; env-var bypass for CI only |
| Named approver + scope | P3 `attested_by` field | Config validation refuses missing |
| Lab-only network guard | P4 `assert_lab_host()` | Refuses any non-private/loopback IP at runtime |
| Content blocklist | P3 `validate_draft()` | Rejects scripts/exec strings; regenerate→hard-fail |
| Simulation markers | P3 `X-PhishSim` header | Whitelisting by mail filters, non-repudiation |
| Send lock | P3 | Requires config `allow_send:true` AND `--send` flag |

## 2. Legal Context (course-level summary — not legal advice)

- **US CFAA / UK CMA / EU equivalents:** unauthorized access to computer systems is a
  criminal offense. Every tool here must target systems you own or have written
  authorization (ROE/scope document) to test.
- **Email & privacy law (GDPR/CCPA):** phishing simulations process employee personal
  data. Requirements: legitimate interest documented by the approver, minimal data
  (click events only — this toolkit stores no keystrokes/content), transparency to the
  works council where required.
- **Responsible disclosure:** findings produced against third-party assets during
  coursework must follow standard disclosure norms; do not publish raw scan artifacts.

## 3. STRIDE Threat Model of This Toolkit Itself

| Tool | Spoofing | Tampering | Repudiation | Info disclosure | DoS | Elevation |
|---|---|---|---|---|---|---|
| API service | bearer token required when configured; dev-open mode logs loudly | strict JSON parse + body size caps | access log per request w/ status codes | recon intel egress is token-gated; active recon needs explicit header | sliding-window limiter per IP | stateless, no accounts |
| P1 recon | forged UA (accepted risk) | tampered baseline diff → verify raw JSON | reports timestamped | leaks domain intel → keep reports internal | crt.sh hammering → per-collector caps | n/a (no auth) |
| P2 fuzzer | attacker LLM lies as judge → regex override wins | payload file injection → schema-validated | SARIF audit trail | system prompts in reports → redact before sharing | runaway fuzz → `--rps` limiter | n/a |
| P3 sim | lookalike sender (by design, marked) | draft tampering → blocklist+regen | manifest.csv + answer key | recipient list → gitignored campaign.json | recipient cap 50 | SMTP creds → secret manager in prod |
| P4 lab | fake nginx banner (lab-only) | log tampering → append-only JSONL | click/beacon logs w/ ts | exfil content hashed, never stored | loopback bind only | tasks never executed |
| P5 copilot | poisoned scanner banners → sanitize inputs | severity overrides logged in report | report disclaimer + date | client data → local-only rendering | batch size caps | n/a |

## 4. LLM-Specific Risks

1. **Hallucinated findings** → evidence-only prompts, cite-evidence requirement,
   deterministic scores displayed beside model output, human QA gate in template.
2. **Prompt injection via tool data** (banner strings, scanner output) → treat all
   external text as untrusted input; constrain output schemas; strip control chars.
3. **Judge manipulation** → deterministic detector hits override judge verdicts.
4. **Data egress** → Ollama mode keeps everything on-device for sensitive labs.

## 5. Acceptable Use Statement

This suite exists for education: your own labs, authorized engagements, and CTFs.
The authors disclaim liability for misuse. If you cannot explain the authorization
for a run out loud, you are not authorized.
