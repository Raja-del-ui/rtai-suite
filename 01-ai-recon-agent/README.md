# Project 01 — AI Recon Agent

**MITRE ATT&CK:** Reconnaissance (T1595, T1592, T1597, T1589)

## Runs Natively on Windows & Kali Linux

This folder is **fully standalone** — it carries its own vendored `rtai_core`; no
repo-wide installation is required.

| OS | One-time setup | Run |
|---|---|---|
| Windows | `py -m pip install -r requirements.txt` | `python recon_agent.py --target example.com` |
| Kali / Debian | `python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt` | `python3 recon_agent.py --target example.com` |

Kali's PEP 668 protects system Python — the venv above is the clean path.
Missing optional deps produce actionable errors (`pip install dnspython>=2.6`).

An agent that runs a battery of **passive** OSINT collectors against one domain —
RDAP registration data, DNS (A/AAAA/MX/NS/TXT/SOA), email-security posture
(SPF/DMARC/CAA), Certificate Transparency subdomains — then hands the merged JSON
evidence to an LLM that produces a prioritized attack-surface assessment with an
exposure rating.

```
            +-----------+     +----------------+     +--------------+
 target --> | sources.py| --> | raw_findings   | --> | analyst.py   |
            | RDAP DNS  |     | .json          |     | LLM prompt   |
            | CT crt.sh |     +----------------+     | (structured) |
            | RDAP HTTP |                            +------+-------+
            +-----------+                                   |
                                                                  v
                                                    recon_report.md (Markdown)
```

## Why It Is "AI-Integrated"

The LLM is not bolted on at the end: it receives *structured evidence* and must cite it.
The system prompt forbids fabricated findings and demands evidence-backed claims — a
core pattern for trustworthy AI security tooling.

## Setup

```powershell
pip install -r requirements.txt      # dnspython only
$env:OPENAI_API_KEY = "sk-..."       # or ANTHROPIC_API_KEY, or nothing for Ollama
```

## Usage

```powershell
python recon_agent.py --target example.com
python recon_agent.py --target scanme.lab.local --provider ollama
python recon_agent.py --target example.com --include-http   # adds light web-root fetch
```

Outputs `raw_findings.json` (evidence) + `recon_report.md` (assessment).

## Safety Design

- Domain-format validation; no IP/URL targets (prevents pivoting to internal hosts).
- Active contact limited to ONE GET of the web root, and only behind `--include-http`.
- Report footer reminds the operator to verify AI claims against raw evidence.

## Extension Ideas

- Add Shodan/Censys collectors behind API keys.
- Chain output into Project 5 to auto-draft a scoping memo.
- Streaming progress + per-collector retry policy.

## v2 Features

- **Parallel collectors** (`ThreadPoolExecutor`) - full sweep runs ~6x faster.
- **TLS certificate inspection** - issuer, SANs, expiry countdown, chain validation.
- **Wayback Machine history** - archived URL paths reveal forgotten endpoints.
- **Live subdomain verification** - CT-log names are DNS-resolved to drop dead entries.
- **Deterministic exposure score** - transparent rule-based scoring shown alongside the
  LLM's opinion (great class discussion: rules vs model).
- **`--baseline raw_findings.json`** - diffs a new scan against a previous one:
  new subdomains, TXT/A record changes, certificate validity drift.
