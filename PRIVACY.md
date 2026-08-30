# Royal-Sec Privacy Notice — rtai-suite

**Controller:** Royal-Sec Ltd, `privacy@royal-sec.com`, `security@royal-sec.com`  
**Effective:** 2026-08-30 — supplements `EULA.md` and `docs/SECURITY_AND_ETHICS.md:19-22`  
**Scope:** Processing of personal data when you operate `royal-sec-rtai-suite` v4.x (recon OSINT, phishing simulation recipients, report inputs, audit logs, API jobs).

> This is template language — have counsel tailor to UK GDPR/EU GDPR and any local regime before first customer deployment. It is not legal advice.

## 1. Data We Process

| Category | Example fields | Tool | Basis example |
|---|---|---|---|
| **Engagement contacts** | `attested_by`, `RTAI_ACTOR`, `USERNAME`/`USER` (`rtai_core/audit.py:86-90`) | P2/P3 gate, audit chain | Contract / legitimate interest |
| **Recipient personal data** | `recipients[]` emails, `token`→`recipient` map (`03-phishing-awareness-sim/campaign.py:98-112`, `landing.py:65-78`) | P3 phish sim | Legitimate interest (security awareness) + organizational consent / employment contract |
| **OSINT about third parties** | RDAP registrant, CT subdomains, email security posture | P1 `01-ai-recon-agent/sources.py` | Legitimate interest — only against authorized target org |
| **Click/interaction data** | `clicks.jsonl` (token, timestamp, IP) | `03-phishing-awareness-sim/landing.py` | Same as recipients |
| **Beacon telemetry** | `beacons.jsonl` (host, interval, jitter) | `04-c2-detection-lab/beacon.py` | Lab-only synthetic, no real user data |
| **Evidence files** | `nmap.xml`, `nuclei.jsonl`, Nessus inputs you supply to `05-pentest-report-copilot/copilot.py` | P5 | Controller-supplied — you warrant you are authorized to share |

We **do not** sell data, use it for advertising, or use it to train foundation models.

## 2. Roles

* **You (customer/operator)** are the **controller** for recipient lists and target selection. You must have a lawful basis, provide transparency to data subjects, and respect objections/opt-out.
* **Royal-Sec Ltd** is **processor/sub-processor** only where you use Royal-Sec-hosted API or support. Otherwise Royal-Sec is not a processor — the Software runs locally/air-gapped and data never leaves your host unless you configure an LLM provider.

## 3. Transparency to Data Subjects (P3)

Before a phishing simulation you must:

* Inform employees/stakeholders that periodic security-awareness simulations occur (works-council/union involvement where required — `docs/SECURITY_AND_ETHICS.md:21-22`);
* State purpose, legal basis, categories of data (email, click time), retention, and that `X-PhishSim` (`generator.py:116`) marks simulation mail;
* Provide an opt-out or alternative training path if local law requires.

A **DPIA template** is in `docs/legal/DPIA_TEMPLATE.md` and `DPA.md`. Complete it with your DPO before processing >50 employees or any special-category data.

## 4. Retention

| Record | Default location | Retention | Deletion |
|---|---|---|---|
| `RTAI_AUDIT_LOG` hash chain (`rtai_core/audit.py:31` → `audit.log`) | `RTAI_AUDIT_LOG` env or CWD `audit.log` | 12 months from engagement close | Secure overwrite + chain-verify before deletion; keep `verify()` proof |
| `campaign_links.csv` + `clicks.jsonl` | `03-phishing-awareness-sim/out/<stamp>/` | 3 months after metrics delivery (or per works agreement) | Shred, then purge from backups on next cycle |
| `raw_findings.json` / `recon_report.md` | `01-ai-recon-agent/` | Per engagement SOW | Delete after report sign-off + retention window |
| `beacons.jsonl`/`detection_report.md` | `04-c2-detection-lab/` | Lab lifetime only | Delete when lab torn down |
| API job store (`--db api.db`) | `services/api/server.py:349-364` | 30 days sliding | `DELETE FROM events WHERE ts < now-30d` |

Do not commit `audit.log` to git (`.gitignore:26`).

## 5. LLM Provider Data Egress

When you set `--provider openai|anthropic|ollama`, prompts are sent to that provider per `rtai_core/providers/factory.py:28-29` (`api_key` or env). **Minimize personal data in prompts** — pseudonymize company names where possible, rely on deterministic `P1 scoring` and `P4 analyze` offline modes for sensitive engagements. Review provider DPA.

## 6. Security

* Secrets via `RTAI_API_TOKEN`, `ANTHROPIC_API_KEY` etc env only (`.env.example:4,11`, `rtai_core/logging_utils.py:11-25` never logs them).
* Bearer token required on API (`services/api/server.py:236-245` fail-closed from v4.1), security headers `X-Content-Type-Options: nosniff` etc `48-53`.
* Local encryption at rest is your responsibility for air-gap bundles; consider TPM sealing (`rtai_core/military_tpm.py`).

## 7. Rights

Data subjects may exercise rights (access, rectification, erasure, objection) against **you** as controller. For simulations, erasure means removing the address from future `recipients[]` and suppressing that token’s analytics. Forward DSARs relating to Royal-Sec processing to `privacy@royal-sec.com` within 72h.

## 8. International Transfers

Air-gap deployments involve no transfer. Cloud LLM/API use may transfer prompts outside the UK/EEA — apply SCCs/UK IDTA via provider.

## 9. Contact & Complaints

* Privacy/DPA: `privacy@royal-sec.com`
* Security incidents: `security@royal-sec.com` (see `SECURITY.md`)
* UK ICO / EU supervisory authority complaints process applies.

---

*Keep this notice with `EULA.md` and `AUP.md` in every branded distribution (`NOTICE.md` references it).*
