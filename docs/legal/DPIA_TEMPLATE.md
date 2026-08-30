# DPIA Template — Phishing Awareness Simulation (P3)

**Use with:** `03-phishing-awareness-sim/campaign.py`, `landing.py`, `metrics.py`  
**Owners:** DPO + CISO + HR/Works Council  
**Attach to:** `DPA.md` where Royal-Sec is processor

## 1. Description

* Purpose of simulation (e.g., reduce click-through, train reporting):
* Categories of data subjects (employees, contractors):
* Data (recipients[], token→recipient map, clicks.jsonl fields: token, timestamp, IP, user-agent):
* Retention: see `PRIVACY.md:4` (links 3 months, audit 12 months):

## 2. Necessity & Proportionality

* Why simulation is necessary vs alternative (classroom only):
* Minimization (pseudonymized display names?):
* Cap justification (≤50 `auth.py:13`):

## 3. Legal Basis

* Employment contract / legitimate interest assessment / consent / collective agreement — describe:

## 4. Risks

* Harm to data subject (embarrassment, workplace detriment):
* Confidentiality (token enumeration `landing.py:65-78`):
* Mitigations (`X-PhishSim` header `generator.py:116`, blocklist `generator.py:14-29`, link locale `landing_base_url` control):

## 5. Transparency

* Where/how subjects are informed pre-simulation (intranet notice, works agreement reference):
* Opt-out / alternative offered:

## 6. Security (Art. 32)

* Env-only secrets, bearer auth (`services/api/server.py:236-253`), TOML/PII redaction, `.gitignore:26` audit.log exclusion:

## 7. Consultation

* DPO sign-off date:
* Works-council/union involvement date (`docs/SECURITY_AND_ETHICS.md:21-22`):

## 8. Residual Risk & Approval

* Residual risk (low/medium/high):
* Approver (`attested_by` = ) — signature/date:

---

Attach completed DPIA to engagement SOW before first `campaign.py --send`.
