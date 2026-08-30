import pathlib

content = pathlib.Path('BOOK.md').read_text(encoding='utf-8')

old = """| Project | Path | Description |
|---------|------|-------------|
| 01-ai-recon-agent | `01-ai-recon-agent/` | Passive OSINT + LLM analysis |
| 02-llm-injection-fuzzer | `02-llm-injection-fuzzer/` | Adaptive prompt injection fuzzer |
| 03-phishing-awareness-sim | `03-phishing-awareness-sim/` | Authorized phishing simulator |
| 04-c2-detection-lab | `04-c2-detection-lab/` | C2 beacon sim + AI detection |
| 05-pentest-report-copilot | `05-pentest-report-copilot/` | AI-assisted report generator |

### Shared Library"""

new_gui = """## Appendix: Project Inventory

| Project | Path | Description |
|---------|------|-------------|
| 01-ai-recon-agent | `01-ai-recon-agent/` | Passive OSINT + LLM analysis |
| 02-llm-injection-fuzzer | `02-llm-injection-fuzzer/` | Adaptive prompt injection fuzzer |
| 03-phishing-awareness-sim | `03-phishing-awareness-sim/` | Authorized phishing simulator |
| 04-c2-detection-lab | `04-c2-detection-lab/` | C2 beacon sim + AI detection |
| 05-pentest-report-copilot | `05-pentest-report-copilot/` | AI-assisted report generator |
| **06-gui** | `rtai_core/gui/` | **Unified GUI launcher with tabbed interface** |

### Shared Library"""

content = content.replace(old_gui, new_gui)

pathlib.Path('BOOK.md').write_text(content, encoding='utf-8')
print('Updated Project Inventory with 06-gui')