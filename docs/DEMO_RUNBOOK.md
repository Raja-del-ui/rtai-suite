# Live Demo Runbook

Total: ~20 min presentation + 14 min demos. Rehearse twice. Every segment has an
offline fallback so no network/API failure can sink the demo.

## Pre-flight checklist (T-30 min)

```
[ ] python scripts/dev.py ci          # lint + compile + 91 tests green
[ ] Ollama running?                   curl http://127.0.0.1:11434/v1/models (if used)
[ ] rtai --list shows 9 subcommands
[ ] Terminal font size 16+, dark theme
[ ] Close Slack/email (opsec flex)
[ ] docs/PRESENTATION_SLIDES.pptx open at slide 1
```

## Segment P — Platform Tour (2 min) ★ new

```powershell
rtai --list
Start-Process python services/api/server.py --port 9000   # separate window
curl http://127.0.0.1:9000/health
curl http://127.0.0.1:9000/metrics
```
Narrate: one product CLI over five engines; Prometheus counters live already.
Fallback: screenshot appendix slide of the endpoints.


## Segment A — Recon Agent (3 min)

```powershell
cd 01-ai-recon-agent
python recon_agent.py --target <YOUR-LAB-DOMAIN>
```
Narrate: parallel collectors → deterministic score prints first → AI cites evidence.
Fallback: show pre-generated `recon_report.md` + raw JSON.

## Segment B — Injection Fuzzer (4 min) ★ highlight

Terminal 1:
```powershell
ollama serve   # if not already
cd 02-llm-injection-fuzzer
python inject_fuzzer.py --url http://127.0.0.1:11434/v1 --model llama3.1 --list-payloads
python inject_fuzzer.py --url http://127.0.0.1:11434/v1 --model llama3.1 --judge --adaptive 1 --rps 5
```
Type ATTACK when attested. Show resilience % drop vs hardened `--system` prompt.
Fallback: `injection_report.md` screenshots in appendix slides.

## Segment C — Phishing Sim (2 min, dry-run only)

```powershell
cd 03-phishing-awareness-sim
$env:PHISHSIM_ATTESTED = "1"
python campaign.py --config samples/campaign.example.json --template password_expiry
notepad out\<run>\sim_001_password_expiry.eml
```
Emphasize X-PhishSim header + blocklist gate. Fallback: answer_key.md walkthrough.

## Segment D — C2 Detection Lab (3 min, fully offline)

```powershell
cd 04-c2-detection-lab
# terminal 1: python listener.py
# terminal 2:
python beacon.py --preset regular --count 8
python analyze.py --log beacons.jsonl --stats-only
```
Show histogram + regularity index. If time: `--compare` two preset logs.
Fallback: saved detection_report.md Sigma rule.

## Segment E — Report Copilot (2 min)

```powershell
cd 05-pentest-report-copilot
python copilot.py --nmap samples/sample-nmap.xml --nuclei samples/sample-nuclei.jsonl `
    --nessus samples/sample-scan.nessus --severity-map samples/severity-overrides.json `
    --company "Acme Corp" --no-llm --out report.md
```
Point at correlation lines + override markers; mention AI narrative/roadmap chapters.

## Q&A ammunition

- "Is this safe?" → docs/SECURITY_AND_ETHICS.md table.
- "What if the model hallucinates?" → deterministic scores shown alongside; evidence-only prompting; human QA gate.
- "Cost?" → Ollama = $0; OpenAI gpt-4o-mini ≈ cents per full suite run.

