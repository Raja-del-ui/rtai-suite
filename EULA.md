# Royal-Sec End-User License Agreement (EULA)

**Version:** 1.0 — 2026-08-30  
**Licensor:** Royal-Sec Ltd (“Royal-Sec”, “Licensor”) — contact: `legal@royal-sec.com`  
**Product:** `royal-sec-rtai-suite` v4.x (“Software”) — five tools (`recon`, `fuzz`, `phish`, `c2-lab`, `report`) + `rtai_core` + `services/api` + GUI  
**Governing law:** England & Wales; exclusive jurisdiction of the courts of England & Wales.  
**This document supplements the MIT license at `LICENSE` for Royal-Sec branded builds.** Where there is conflict, this EULA controls for branded distribution. Source redistributions under plain MIT remain permitted provided this EULA is removed and `Royal-Sec` branding stripped.

> **IMPORTANT — READ CAREFULLY.** This is a binding contract. By installing, copying, or using the Software you accept these terms. If you do not accept, do not install or use it. If you are acting on behalf of an organisation, you represent you have authority to bind it.

## 1. Grant & Scope

1.1 Royal-Sec grants you a **non-exclusive, non-transferable, revocable** license to install and use the Software **solely for authorized security-testing, research, education, and defensive operations** in accordance with the Acceptable Use Policy (`AUP.md`) and `docs/SECURITY_AND_ETHICS.md`.

1.2 You may create one air-gap bundle per `rtai_core/military_airgap.py` for offline deployment within your organisation. You may not redistribute the branded build externally without Royal-Sec written consent.

## 2. Authorized Use — Customer Obligations

2.1 You must hold **prior written authorization** (signed statement of work, rules of engagement, or scope letter) identifying scope, targets/domains, date range, and approver (`attested_by`) for **every** target tested with `recon --include-http`, `fuzz`, `phish --send`, and `c2-beacon`.

2.2 You must be able to **produce that authorization on demand** within 24 hours to Royal-Sec or a regulator. Failure to produce is deemed unauthorized use.

2.3 All authorizations must be recorded via the built-in gates (`Type ATTACK` / `I AM AUTHORIZED`, `RTAI_ATTEST_KEY` HMAC where enabled) and are written to the hash-chained `RTAI_AUDIT_LOG` (`rtai_core/audit.py`). **Tampering with or discarding audit logs is a material breach.**

2.4 You must nominate a **Responsible Operator** who has completed the Royal-Sec ethics briefing and will brief every user.

## 3. Restrictions

You must not:

* (a) use the Software against any system you do not own or lack explicit written permission to test (breach of CFAA/CMA/EU equivalents);
* (b) weaponize outputs, sell access to facilitate crime, or enable sanctioned jurisdictions (see `EXPORT_CONTROL.md`);
* (c) remove copyright, Royal-Sec branding, `X-PhishSim` headers (`03-phishing-awareness-sim/generator.py:116`), audit instrumentation, or lab-only network guards (`rtai_core/validation.py:38-43`);
* (d) reverse-engineer to bypass authorization gates or rate limits (`services/api/server.py:236-253`);
* (e) process personal data without complying with `PRIVACY.md` and applicable data-protection law;
* (f) rely on AI-generated findings without human QA (see §5).

## 4. AI Disclosure

4.1 The Software uses deterministic scorers and optional LLM providers (`rtai_core/providers/`) for analysis and report drafting. LLM output may be incomplete, hallucinated, or stale. **It is not legal, compliance, or penetration-test evidence until reviewed by a qualified human.**

4.2 Royal-Sec disclaims any warranty as to LLM correctness, availability, or non-infringement. Provider terms (OpenAI/Anthropic/Ollama) apply to data you send; you are the data controller for prompts containing customer data.

4.3 For P5 `copilot.py` reports you must keep the `AI-draft — human QA required` footer and apply a qualified reviewer signature before delivery to a client.

## 5. Human QA Gate (P5 / Reporting)

Any report produced with `05-pentest-report-copilot` that is delivered externally must be reviewed and signed by a human tester holding the engagement scope. **Unreviewed export is at your sole risk** and you indemnify Royal-Sec for reliance losses.

## 6. Support & Updates

Support tiers, patch SLAs (Critical 7 d / High 30 d), and LTS versions are defined in `SECURITY.md`. No SLA is implied for community (no-contract) use. Updates may be delivered as signed air-gap bundles (`cosign` per `future.md:F-C05`) or via PyPI `royal-sec-rtai-suite`.

## 7. Fees & Term

Where purchased under an Order Form/MSA, fees, term, and termination follow that Order Form. Otherwise this licence is granted gratis and continues until terminated. Royal-Sec may terminate immediately for breach of §2/§3.

## 8. Audit

Royal-Sec may, on 14 days’ notice and no more than annually, request a written attestation or sampled audit-log excerpt proving authorized use for any engagement where the Software was used. Personal data in excerpts must be redacted except as required by law.

## 9. Export Control

Use is subject to `EXPORT_CONTROL.md`. By using the Software you certify you are not located in, nor acting for, a sanctioned destination or prohibited end-use.

## 10. Warranty Disclaimer

To the fullest extent permitted by law, the Software is provided **“AS IS” without warranty** — see `LICENSE:15-21` MIT AS-IS clause, which is incorporated by reference. Royal-Sec does not warrant uninterrupted operation, fitness for a particular offensive purpose, or that the Software will detect all vulnerabilities.

## 11. Limitation of Liability

11.1 Nothing limits liability that cannot be limited by law (e.g., fraud, death/personal injury from negligence).

11.2 Subject to §11.1, Royal-Sec’s aggregate liability for any 12-month period is capped at the **greater of £5,000 or the fees paid by you to Royal-Sec in that period** (or £500 for gratis use). Royal-Sec is not liable for indirect, consequential, loss-of-profit, loss-of-data, or reliance damages.

## 12. Indemnification

You indemnify, defend, and hold harmless Royal-Sec, its officers and suppliers against any claim, fine, or loss arising from **your unauthorized testing, data-processing breach, unlawful content generation, or delivery of unreviewed P5 reports**.

## 13. Data Protection

Each party complies with applicable data-protection law. Role mapping, retention (audit chain 12 months, see `PRIVACY.md`), and processor terms are defined in `DPA.md` where Royal-Sec acts as processor.

## 14. Termination

Termination for breach: Royal-Sec may disable licensed updates and require you to delete branded builds. Sections 3, 5, 10–16 survive termination. You must cease use and, where ordered, certify deletion within 14 days.

## 15. Trademark

“Royal-Sec” and the navy/gold livery (`rtai_core/gui/launcher.py:19-45`) are trade marks of Royal-Sec — see `TRADEMARK.md`. No trade-mark license is granted except to refer truthfully to the Software.

## 16. General

* **Entire agreement:** This EULA + `AUP.md` + `PRIVACY.md` + Order/MSA is the entire agreement for the Software.
* **Severability:** If any term is unenforceable, the remainder continues.
* **Changes:** Royal-Sec may update this EULA for new versions; your continued use of a new version constitutes acceptance. Prior versions remain governed by the EULA you accepted.
* **Notices:** `legal@royal-sec.com`, `security@royal-sec.com`.

---

**Acceptance record:** Your acceptance is captured as an `audit_record("eula_accepted", actor=…, version="4.0.0")` at install time (`military_airgap.py` / `verify_installation.py`) and via CLI `--accept-eula` where present.

*This draft is template language and does not constitute legal advice. Have Royal-Sec counsel approve before first commercial invoice.*
