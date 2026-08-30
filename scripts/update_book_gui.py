import pathlib

content = pathlib.Path('BOOK.md').read_text(encoding='utf-8')

old_gui = """## Appendix: Project Inventory

| Project | Path | Description |
|---------|------|-------------|
| 01-ai-recon-agent | `01-ai-recon-agent/` | Passive OSINT + LLM analysis |
| 02-llm-injection-fuzzer | `02-llm-injection-fuzzer/` | Adaptive prompt injection fuzzer |
| 03-phishing-awareness-sim | `03-phishing-awareness-sim/` | Authorized phishing simulator |
| 04-c2-detection-lab | `04-c2-detection-lab/` | C2 beacon sim + AI detection |
| 05-pentest-report-copilot | `05-pentest-report-copilot/` | AI-assisted report generator |

### Shared Library

| Module | Purpose |
|--------|---------|
| `rtai_core.providers` | LLM provider abstraction |
| `rtai_core.config` | Layered configuration |
| `rtai_core.registry` | Plugin registry |
| `rtai_core.storage` | JSONL + SQLite storage |
| `rtai_core.audit` | Hash-chained audit log |
| `rtai_core.metrics` | Prometheus metrics |
| `rtai_core.validation` | Input validation |
| `rtai_core.providers` | LLM providers |"""

new_gui = """## Appendix: Project Inventory

| Project | Path | Description |
|---------|------|-------------|
| 01-ai-recon-agent | `01-ai-recon-agent/` | Passive OSINT + LLM analysis |
| 02-llm-injection-fuzzer | `02-llm-injection-fuzzer/` | Adaptive prompt injection fuzzer |
| 03-phishing-awareness-sim | `03-phishing-awareness-sim/` | Authorized phishing simulator |
| 04-c2-detection-lab | `04-c2-detection-lab/` | C2 beacon sim + AI detection |
| 05-pentest-report-copilot | `05-pentest-report-copilot/` | AI-assisted report generator |
| **06-gui** | `rtai_core/gui/` | **Unified GUI launcher with tabbed interface** |

### Shared Library

| Module | Purpose |
|--------|---------|
| `rtai_core.providers` | LLM provider abstraction |
| `rtai_core.config` | Layered configuration |
| `rtai_core.registry` | Plugin registry |
| `rtai_core.storage` | JSONL + SQLite storage |
| `rtai_core.audit` | Hash-chained audit log |
| `rtai_core.metrics` | Prometheus metrics |
| `rtai_core.validation` | Input validation |
| `rtai_core.providers` | LLM providers |
| `rtai_core.gui` | **GUI modules for all 5 tools** |"""

content = pathlib.Path('BOOK.md').read_text(encoding='utf-8')
content = content.replace(old_gui, new_gui)

# Update Quick Start section
old_quick = """## Quick Start

### Prerequisites

- **Python 3.11+**
- **No internet required** after initial setup (fully offline capable)
- **Windows 10/11** or **Linux** (Kali, Ubuntu, Debian)
- **Ollama** (optional, for local LLM) or API keys for OpenAI/Anthropic

### One-Line Install (Repo Mode)

```bash
git clone https://github.com/yourorg/rtai-suite.git
cd rtai-suite
pip install -e .[dev,recon,report]
```

### Air-Gap Deployment (Offline)

```bash
# Download the bundle
tar -xzf rtai-suite-4.0.0-airgap.tar.gz
cd rtai-suite-4.0.0

# Linux/macOS/Kali
chmod +x install.sh
./install.sh

# Windows
install.bat
```

### Verify Installation

```bash
# Run verification
python verify_installation.py

# Quick test
rtai --list
rtai recon --target example.com
```"""

new_quick = """## Quick Start

### Prerequisites

- **Python 3.11+**
- **No internet required** after initial setup (fully offline capable)
- **Windows 10/11** or **Linux** (Kali, Ubuntu, Debian)
- **Ollama** (optional, for local LLM) or API keys for OpenAI/Anthropic

### One-Line Install (Repo Mode)

```bash
git clone https://github.com/yourorg/rtai-suite.git
cd rtai-suite
pip install -e .[dev,recon,report,gui]
```

### Air-Gap Deployment (Offline)

```bash
# Download the bundle
tar -xzf rtai-suite-4.0.0-airgap.tar.gz
cd rtai-suite-4.0.0

# Linux/macOS/Kali
chmod +x install.sh
./install.sh

# Windows
install.bat
```

### Verify Installation

```bash
# Run verification
python verify_installation.py

# Quick test
rtai --list
rtai gui
rtai recon --target example.com
```

### Launch GUI

```bash
# Launch the unified GUI
rtai gui

# Or directly
python -m rtai_core.gui
```"""

import pathlib
content = pathlib.Path('BOOK.md').read_text(encoding='utf-8')
content = content.replace(old_quick, new_quick)
pathlib.Path('BOOK.md').write_text(content, encoding='utf-8')
print('Updated Quick Start section')