# Royal-Sec Data Processing Addendum (Template)

**Controller:** Customer (“Controller”)  
**Processor:** Royal-Sec Ltd (“Processor”) — `privacy@royal-sec.com`  
**Subject matter:** Processing of personal data via `royal-sec-rtai-suite` v4.x where Royal-Sec hosts the API (`services/api/server.py`) or provides support with access to `RTAI_AUDIT_LOG`/`clicks.jsonl` excerpts.  
**Effective:** Annexed to `EULA.md` / MSA — have counsel execute.

## 1. Definitions & Roles

GDPR/UK GDPR definitions apply. For P3 phish awareness, Controller is the employer; data subjects are employees/recipients. For P1 OSINT, Controller determines lawful basis for targeting. Processor follows Controller instructions documented in the engagement SOW + `AUP.md`.

## 2. Nature & Purpose

Process recipient emails, tokens, click timestamps, audit actors, and evidence you supply **solely to deliver the contracted simulation/report/API operation**, per `PRIVACY.md:1-3` categories.

## 3. Duration

For the engagement term + 30 days for job store (`--db`) and 12 months for audit chain unless otherwise agreed. See `PRIVACY.md:4` retention table.

## 4. Instructions

Processor processes only on Controller documented instructions, unless required by law (notifying Controller unless prohibited). Any LLM provider sub-processor call (`rtai_core/providers/factory.py:28-29`) is an instruction to transmit the prompt you approved.

## 5. Confidentiality

Processor personnel bound by confidentiality, least-privilege access to `audit.log`/`api.db`, annual training on authorized-use. Royal-Sec audits access.

## 6. Security (Art. 32)

* Bearer auth + rate limit + security headers (`services/api/server.py:48-53,60-75,236-253`);
* Hash-chained audit integrity (`rtai_core/audit.py:17-69`, `verify()` per line);
* Encryption in transit (TLS termination before `ThreadingHTTPServer` where deployed; `rtai_core/military_mtls.py:56` mTLS option);
* Pseudonymisation where possible; secrets via env only (`rtai_core/logging_utils.py:11-25`);
* Regular bandit/SAST and pen-test (see `SECURITY.md`).

## 7. Sub-processors

| Sub-processor | Purpose | Location | Safeguard |
|---|---|---|---|
| LLM provider you configure (OpenAI/Anthropic/Ollama) | P1/P2/P3/P5 analysis | Provider region (US/EU) | SCCs/IDTA via provider terms |
| Hosting provider (if Royal-Sec hosted) | API hosting | UK/EU (or as per Order) | SCCs if transfer |

Controller is notified 14 days before any new sub-processor; may object on reasonable grounds.

## 8. Data Subject Rights

Processor assists Controller within 5 business days (access, rectification, erasure, restriction, portability, objection) by providing tooling to redact `recipients[]` and `clicks.jsonl`. No direct response to data subject without Controller approval.

## 9. Breach Notification

Processor notifies Controller of a personal-data breach **without undue delay and within 24 hours of awareness** via `security@royal-sec.com` → Controller contact, with nature, categories, mitigation, and `audit.log` integrity status (`verify()`).

## 10. Audit

Once per 12 months, Controller may request evidence: SOC2 Type II (roadmap), pen-test summary, or `verify_project.py` run excerpt, under NDA. No on-site audit without cause; alternative is remote evidence review.

## 11. Return & Deletion

At termination, Processor deletes or returns `api.db`, `audit.log` excerpts, and support tickets containing personal data within 30 days, except where retention required by law (e.g., audit chain per statute). Certification of deletion on request.

## 12. International Transfers

Transfers outside UK/EEA use UK IDTA or EU SCCs Module One/Two as appropriate, completed by the Order Form.

## 13. Order of Precedence

`MSA > DPA > EULA.md > PRIVACY.md`.

---

**Signatures:**

| Party | Name / Title | Date | Signature |
|---|---|---|---|
| Controller |  |  |  |
| Royal-Sec Ltd |  |  |  |

*Template — have counsel finalize before customer signature. Attach completed `docs/legal/DPIA_TEMPLATE.md` for P3 where required.*
