# Royal-Sec Acceptable Use Policy (AUP)

**Applies to:** `royal-sec-rtai-suite` v4.x and any air-gap bundle produced by `rtai_core/military_airgap.py`  
**Effective:** 2026-08-30 — supplements `EULA.md` §2-3 and `docs/SECURITY_AND_ETHICS.md:3-12`  
**Contact:** `abuse@royal-sec.com`, `security@royal-sec.com`

## 1. Core Principle — Authorization Before Action

> **If you cannot produce a signed scope/ROE naming the target, you are NOT authorized.** (`docs/SECURITY_AND_ETHICS.md:49-50`)

Every active operation must have **prior written authorization** that states:

* **Who** authorized it (`attested_by` — name + title + date),
* **What** is in scope (domains/IPs/APIs, explicitly listed; wildcard only with justification),
* **When** (date/time window + timezone),
* **How** (permitted techniques: passive recon, `include_http`, injection payload classes, phishing templates),
* **Data handling** (where findings stored, encryption, retention, deletion deadline),
* **Rollback/cleanup** (how you will retract phish, rotate tokens, purge logs after engagement).

Keep this document for **at least 12 months** after the engagement. Produce it within 24h on Royal-Sec or regulator request.

## 2. Tool-Specific Rules

| Tool | Entry point | Authorized use rule |
|---|---|---|
| **P1 Recon** | `01-ai-recon-agent/recon_agent.py:90-107` | **Passive only** (`collect(include_http=False)`) is allowed on any domain you are researching defensively. **`--include-http` (active GET)** requires written scope naming the domain and time window; it is audited and requires attestation. Never set `--include-http` against infrastructure you do not own/operate or are not hired to test. |
| **P2 Fuzzer** | `02-llm-injection-fuzzer/inject_fuzzer.py:26-31` (`ATTACK` gate, `INJECTION_FUZZER_ATTESTED`) | Test **only endpoints you own/control**. Staging/dev clones preferred. Rate-limit with `--rps` so you do not DoS a shared service. Do not exfiltrate or publish model system prompts you extract from third-party services. |
| **P3 Phish Sim** | `03-phishing-awareness-sim/campaign.py:73-77` (`I AM AUTHORIZED` + `attested_by` + dual `allow_send`+`--send`) | Human-subjects rules apply. **You must have** org-level approval (CISO/DPA officer + HR/works-council where required — see `PRIVACY.md` and `docs/SECURITY_AND_ETHICS.md:19-22`), a **clear educational purpose**, ≤50 recipients per run (`auth.py:13`), `X-PhishSim` header preserved (`generator.py:116`), and an opt-out/unsubscribe path. Never use `allow_send:true` for real deception outside a documented awareness programme. Retain recipient consent basis. |
| **P4 C2 Lab** | `04-c2-detection-lab/beacon.py:183-188` `assert_lab_address`, `listener.py:95-101` | **Lab-only** — `127.0.0.1/::1/10/8/192.168/16/172.16/12` and link-local only (`rtai_core/validation.py:27-35` loopback/private/link-local; `is_reserved` excluded from v4.1). Beacon `run()` refuses non-lab hosts. Never point beacon at a public IP or deploy listener on `0.0.0.0` without `--allow-public` plus written lab-network exception. |
| **P5 Copilot** | `05-pentest-report-copilot/copilot.py:51-69` | AI draft — **human QA gate mandatory** before delivering any report externally (`EULA.md` §5). Embed the `AI-draft` watermark, have the lead tester countersign, and keep evidence (`raw_findings.json`, `nmap.xml`) for audit. Hallucinated findings are your responsibility after signature. |

## 3. Prohibited Uses

* Testing without written authorization; “implied” scope is not scope.
* Using phish templates to harvest real credentials outside the simulation store (`clicks.jsonl` local only).
* Removing lab guards, audit logging, or `X-PhishSim` headers to evade controls.
* Weaponizing or re-selling findings to facilitate crime, extortion, or harassment.
* Bombing a target with payloads at a rate that degrades service (`fuzzer --rps 0` unlimited is only for your own lab).
* Processing employee/consumer personal data without a lawful basis (see `PRIVACY.md`).

## 4. Technical Controls that Enforce This Policy

* Typed attestations `ATTACK` / `I AM AUTHORIZED` (`inject_fuzzer.py:29`, `auth.py:31-34`) — CI bypass via `RTAI_ATTEST_KEY` HMAC only, not `=1` in production (`docs/SECURITY_AND_ETHICS.md:7` upgraded).
* `RTAI_AUDIT_LOG` hash chain (`rtai_core/audit.py:17-69`) — every authorization, `auth_failure`, and `recon_failed`/`recon_success` is recorded with `prev` hash; `verify()` detects tampering at exact line.
* `assert_lab_address(host)` (`rtai_core/validation.py:38-43`) — client and server side.
* Bearer token + sliding-window rate limit + security headers (`services/api/server.py:48-53,60-75,236-253`).
* Content blocklist + regen (`generator.py:14-29`) and `X-PhishSim` (`generator.py:116`).

**Bypassing or disabling any of the above is a breach of this AUP and of `EULA.md` §3.**

## 5. Enforcement

* First breach: written warning + required re-attestation.
* Material breach (unauthorized active testing, breach of data law, tampering with audit): suspension of licensed updates + termination per `EULA.md` §14.
* Illegal conduct will be referred to law enforcement where required.

## 6. Reporting Misuse

If you observe misuse of a Royal-Sec build, report to `abuse@royal-sec.com` with target, time, `audit.log` excerpt (redacted), and scope document. Royal-Sec will acknowledge within 24h.

## 7. Updates

This AUP may be updated with versioned `EULA.md` releases. Check `mkdocs` Compliance section for current version.

---

*Template — have counsel confirm jurisdiction-specific wording before publishing.*
