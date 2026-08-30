# Security Policy — Royal-Sec rtai-suite

## Supported versions

| Version | Supported | Notes |
|---|---|---|
| `4.0.x` (`4.0.0` current) | **yes** — active LTS | Commercial support via `security@royal-sec.com` |
| `4.1.x` (next) | planned | Will supersede 4.0.x; migration guide at release |
| `< 4.0` (`3.2.1`, `3.1.x`) | **no** — upgrade required | Legacy academic tags; no backports |

Patch SLAs for supported versions: **Critical 7 calendar days, High 30 days, Medium 90 days** from acknowledgement. Fix is delivered as signed wheel / air-gap bundle.

## Reporting a vulnerability

**Do not open a public issue for security flaws.**

1. Email `security@royal-sec.com` with subject `[rtai-suite] <short title>` and include:
   * affected version (`rtai --version` / `rtai_core/version.py:1-3` `__version__`),
   * module + file:line (e.g., `rtai_core/validation.py:38` `assert_lab_address` bypass),
   * reproduction steps (redacted — no real target data),
   * impact (CWE/CVSS if known).

2. Optionally encrypt with the PGP key published at `https://royal-sec.com/.well-known/pgp.txt` (fingerprint published in `docs/SECURITY_AND_ETHICS.md` on release — until then, TLS-only email is accepted).

3. You will receive **acknowledgement within 24 hours** and a **triage update within 3 business days**. Royal-Sec follows **90-day coordinated disclosure** (earlier by mutual agreement) and requests CVE assignment where applicable.

4. For misuse/abuse reports (e.g., observed unauthorized testing with a Royal-Sec build), email `abuse@royal-sec.com` with the same SLA.

## Hard-coding guarantees this suite makes

* No subprocess execution of LLM output anywhere.
* `04-c2-detection-lab/beacon.py:134-136` never executes received task strings (`[sim]` print only).
* `03-phishing-awareness-sim/generator.py:14-29` emails cannot contain `script`/`iframe`/`javascript:` payloads (blocklist + regenerate, tested).
* Network egress targets validated: lab-only guards (`rtai_core/validation.py:38-43` `assert_lab_address` on beacon + listener/landing) and domain-format validation (`rtai_core/validation.py:12` `valid_domain`) on P1.
* Secrets read from environment only (`RTAI_API_TOKEN`, `ANTHROPIC_API_KEY`, etc — `.env.example:4,11`) — never logged (`rtai_core/logging_utils.py:11-25` `JsonLinesFormatter` redacts).
* API bearer auth is **fail-closed** from v4.1 (`services/api/server.py:236-245`, `381-383` warning removed for branded builds) — no open fallback in commercial distribution.

## Audit & Operational Controls

* Hash-chained tamper-evident log `rtai_core/audit.py:17-69` (`GENESIS` + `sha256(canonical)`) — `verify()` pinpoints first broken line.
* Every authorization, auth failure, rate-limit, and recon success/failure is recorded with `prev` hash — see `rtai_core/audit.py:33-45` `record()` and `services/api/server.py:243-244,252,322`.
* Rate limiting per-IP sliding window (`services/api/server.py:60-75`) and body caps (`MAX_BODY 512KB:46`).

## Scope & Out-of-Scope

* **In scope:** bypass of any gate in `01-ai-recon-agent/recon_agent.py`, `02-llm-injection-fuzzer/inject_fuzzer.py:26-31`, `03-phishing-awareness-sim/auth.py:27-35`/`campaign.py:73-77`, `04-c2-detection-lab/*`, or `services/api/server.py:236-253`; tampering with `audit.py` chain; injection via LLM prompts.
* **Out-of-scope:** social engineering of the reporter, DoS of lab hosts outside `RTAI_RATE_LIMIT`, or findings requiring physical access.

## Past Advisories

Published at `https://royal-sec.com/security/advisories` and as GitHub Security Advisories.

---

*For the ethics and legal framework, see `docs/SECURITY_AND_ETHICS.md:3-50`, `AUP.md`, `EULA.md`, and `PRIVACY.md`.*

