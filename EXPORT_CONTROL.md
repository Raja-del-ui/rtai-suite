# Export Control & Dual-Use Notice

**Product:** `royal-sec-rtai-suite` v4.x — penetration-testing toolkit (recon, injection fuzzer, phishing sim, C2 lab, report copilot)  
**Issuer:** Royal-Sec Ltd, `legal@royal-sec.com`, `compliance@royal-sec.com`  
**Effective:** 2026-08-30 — referenced by `EULA.md` §9  
**Classification status:** Self-classified pending formal determination — seek counsel before cross-border distribution.

> This is template information, not legal advice. Engage export counsel for formal CCATS/ECCN + UK SPIRE determinations.

## 1. Why This Matters

Offensive security software and certain cryptographic components are **dual-use** items. Even though the suite is defensive/educational in intent (`LICENSE:23-25`, `AUP.md:1`, `docs/SECURITY_AND_ETHICS.md:14`), regulators may treat its capabilities (network recon, payload generation, phishing simulation, C2 simulation) as dual-use.

## 2. Indicative Classification (to be confirmed)

| Component | Technology | Indicative ECCN (US EAR) | UK Control List | Notes |
|---|---|---|---|---|
| `rtai_core/military_pqc.py:77` — ML-KEM/ML-DSA hybrid | Post-quantum cryptography | **5D002** / 5E002 (ENC) | ML? / Category 5 Part 2 | ENC exception may apply for open-source; confirm |
| `01-ai-recon-agent` | OSINT/recon tooling | 5D002? / EAR99? | Dual-use | Wassenaar DS, but publicly available software exemption (501) may apply |
| `02-llm-injection-fuzzer` | Security testing tooling | EAR99 / 5D002 | Dual-use | Classification depends on payload arsenal scope |
| `03-phishing-awareness-sim` | Simulation software | EAR99 | Not controlled | Not controlled if no intrusion s/w |
| `04-c2-detection-lab` | Network exploitation simulation (lab-only) | Careful — may be **intrusion software** under Wassenaar | Take advice | Lab guard `rtai_core/validation.py:38-43` mitigates but not dispositive |
| `05-pentest-report-copilot` | Document generator | EAR99 | Not controlled |  |

**Action:** Instruct counsel to confirm whether each component qualifies for **TSU / publicly available (740.13)** or **ENC unrestricted** treatment and whether CCATS is required.

## 3. Prohibited Destinations & End-Uses

You must not export, re-export, or provide access to sanctioned destinations or prohibited end-uses without a licence:

* **Sanctioned regions** (indicative; check current OFSI/OFAC/EU lists): Russia, Belarus, Iran, North Korea, Syria, Cuba, Crimea/Donetsk/Luhansk, and restricted dealings with China/Macau for advanced computing where applicable.
* **Prohibited end-uses:** Military weapons systems development, military transport, maritime nuclear propulsion, or surveillance repression where restricted.

Royal-Sec may require an **End-User Certificate (EUC)** before delivering an air-gap bundle.

## 4. Customer Obligations

Before cross-border transfer you must:

1. Confirm the recipient is not a denied party (UK Sanctions List, US Entity List/Denied Persons, EU Consolidated List);
2. Provide an EUC stating civil/commercial end-use, authorized lab scope (`AUP.md:1`), and that you will not re-export to sanctioned destinations;
3. Retain classification + EUC records for 6 years;
4. Notify Royal-Sec of any suspected diversion within 5 business days.

## 5. Cloud & Deemed Exports

Granting a foreign national access to controlled technology in the UK (e.g., remote API `services/api/server.py` access) can be a **deemed export**. Use `RTAI_API_TOKEN` scoping, IP allowlists (`assert_lab_address` pattern), and need-to-know.

## 6. How to Request a Licence Determination

Contact `compliance@royal-sec.com` with:

* Recipient country, end-user name, and ownership;
* Which suite components are transferred (full suite vs P3/P5 only);
* Evidence of publicly-available status (source published, no charge for technology);
* Intended use and SOW excerpt (redacted).

Royal-Sec will seek formal classification where advised by counsel.

## 7. Record-Keeping

Keep `MANIFEST.json` + `checksums` (`rtai_core/military_airgap.py:77-89`), EUC, and transfer logs for 6 years. Audit chain (`RTAI_AUDIT_LOG`) is not an export log — keep separate transfer register.

## 8. Non-Compliance

Breach of this notice is a material breach of `EULA.md` §9 and may constitute a criminal offence. Royal-Sec will cooperate with licensing authorities where compelled.

---

*Have counsel replace indicative ECCNs with formal determinations before first controlled export.*
