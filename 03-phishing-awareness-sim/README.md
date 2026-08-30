# Project 03 — Phishing Awareness Simulator

**MITRE ATT&CK:** Initial Access — Phishing (T1566) · **Framework:** ISO 27001 A.6.3 awareness

## Runs Natively on Windows & Kali Linux

Fully standalone: vendored `rtai_core` ships inside this folder; stdlib-only runtime.

| OS | One-time setup | Run |
|---|---|---|
| Windows | *(nothing to install)* | `python campaign.py --config samples/campaign.example.json --validate-config-only` |
| Kali / Debian | *(nothing to install; venv optional)* | `python3 campaign.py --config samples/campaign.example.json --validate-config-only` |

Generates **realistic-but-benign** phishing simulation emails for authorized security
awareness programs. The LLM personalizes a governed template per recipient; every draft
is validated against a content-safety blocklist, stamped with an `X-PhishSim` header,
and shipped with a **trainer answer key** explaining each planted red flag.

```
campaign.json ──▶ auth.py (attestation + validation)
                    │
templates.py ──▶ generator.py ──▶ LLM draft (JSON)
                    │                  │
                    │          validate_draft()  ← blocklist gate
                    ▼                  ▼
              out/<run>/ sim_NN.eml · manifest.csv · answer_key.md
```

## Setup

No third-party packages. Configure the LLM via env or flags.

## Usage

```powershell
copy samples\campaign.example.json campaign.json   # edit company + recipients
python campaign.py --config campaign.json --validate-config-only
python campaign.py --config campaign.json --template password_expiry
python campaign.py --config campaign.json --template invoice_attachment --send
```

Templates: `password_expiry`, `hr_bonus_letter`, `invoice_attachment`, `package_delivery`.

## Safety Design (this is the graded part)

| Control | Implementation |
|---|---|
| Human attestation | must type `I AM AUTHORIZED` (or `PHISHSIM_ATTESTED=1`) |
| Config validation | named approver (`attested_by`), recipient allowlist format, ≤50 recipients |
| Content blocklist | no scripts/iframes/exec strings; regenerate-on-violation then hard fail |
| Simulation marker | every email carries `X-PhishSim: awareness-training` |
| Send lock | SMTP requires config `allow_send: true` **and** CLI `--send` |

## Extension Ideas

- Track simulated clicks with the landing page and produce a metrics dashboard.
- Add an MFA-fatigue template (push-bombing awareness).
- A/B test two templates and let the LLM summarize click-rate differences.

## v2 Features

- **Click tracking** - every recipient gets a unique tokenized link
  (`/l/<token>`); the new `landing.py` server logs clicks to `clicks.jsonl` and
  serves an education page that names the red flags they just fell for.
- **Multi-template campaigns** - `--template all` runs all four templates against
  every recipient in one pass.
- **Metrics dashboard** (`metrics.py`) - overall + per-template click rates and a
  clicker list for the debrief session.
- `landing_base_url` config key points emails at wherever the landing server runs.
