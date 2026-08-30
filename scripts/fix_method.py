with open('rtai_core/military_airgap.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the _create_verification_script method by rewriting it entirely
old_method_start = content.find('def _create_verification_script(self, bundle_dir: Path):')
if old_method_start >= 0:
    next_method = content.find('    def _create_offline_readme', content.find('def _create_verification_script'))
    if next_method == -1:
        next_method = len(content)
    
    new_method = '''    def _create_verification_script(self, bundle_dir: Path):
        """Create post-install verification script."""
        script_lines = [
            "#!/usr/bin/env python3",
            "\\"\\"\\"verify_installation.py - Verify rtai-suite installation\"\"\"",
            "import sys",
            "import subprocess",
            "import importlib",
            "",
            "def check_import(module_name, min_version=None):",
            "    try:",
            "        module = __import__(module_name)",
            "        version = getattr(module, '__version__', 'unknown')",
            "        print(f\"[OK] {module_name} {version}\")",
            "        return True",
            "    except ImportError as e:",
            "        print(f\"[FAIL] {module_name}: {e}\")",
            "        return False",
            "",
            "def main():",
            "    print(\"=== rtai-suite Installation Verification ===\")",
            "    print()",
            "",
            "    checks = [",
            "        (\"rtai_core\", \"3.3.0\"),",
            "        (\"dnspython\", \"2.6.0\"),",
            "        (\"jinja2\", \"3.1.0\"),",
            "        (\"pytest\", \"8.0.0\"),",
            "    ]",
            "",
            "    all_passed = True",
            "    for module, min_ver in [",
            "        (\"rtai_core\", \"3.3.0\"),",
            "        (\"dns\", \"2.6.0\"),  # dnspython imports as dns",
            "        (\"jinja2\", \"3.1.0\"),",
            "        (\"pytest\", \"8.0.0\"),",
            "        (\"ruff\", \"0.5.0\"),",
            "        (\"mypy\", \"1.10.0\"),",
            "    ]:",
            "        try:",
            "            mod = __import__(module_name if (module_name := {",
            "                \"dnspython\": \"dns\",",
            "            }.get(module, module)) != module else module)",
            "            version = getattr(mod, '__version__', 'unknown')",
            "            print(f\"[OK] {module} {version}\")",
            "        except ImportError as e:",
            "            print(f\"[WARN] {module} not available: {e}\")",
            "",
            "    # Test CLI tools",
            "    tools = [",
            "        (\"rtai\", [\"--list\"]),",
            "        (\"01-ai-recon-agent/recon_agent.py\", [\"--help\"]),",
            "        (\"02-llm-injection-fuzzer/inject_fuzzer.py\", [\"--list-payloads\"]),",
            "        (\"03-phishing-awareness-sim/campaign.py\", [\"--help\"]),",
            "        (\"04-c2-detection-lab/listener.py\", [\"--help\"]),",
            "        (\"04-c2-detection-lab/beacon.py\", [\"--help\"]),",
            "        (\"05-pentest-report-copilot/copilot.py\", [\"--help\"]),",
            "    ]",
            "",
            "    for tool, args in tools:",
            "        try:",
            "            result = subprocess.run(",
            "                [\"python\", \"-m\"] + tool.split() + args,",
            "                capture_output=True, timeout=30",
            "            )",
            "            if result.returncode == 0:",
            "                print(f\"[OK] CLI tool works\")",
            "            else:",
            "                print(f\"[WARN] CLI tool exited with code {result.returncode}\")",
            "        except Exception as e:",
            "            print(f\"[WARN] Could not test CLI: {e}\")",
            "",
            "    print()",
            "    print(\"=== Verification Complete ===\")",
            "",
            "if __name__ == \"__main__\":",
            "    main()",
        ]
        script = "\\n".join(script_lines)
        (Path("verify_installation.py")).write_text(script)
        (Path("verify_installation.bat")).write_text("@echo off\\npython verify_installation.py\\n")

    def _create_offline_readme(self, bundle_dir: Path):
        """Create offline deployment README."""
        readme = """# rtai-suite Air-Gap Deployment Bundle

This is a complete, self-contained deployment bundle for the rtai-suite
AI-integrated red team toolkit. No internet connection required after extraction.

## Contents

- **1-ai-recon-agent**: Passive OSINT reconnaissance with LLM analysis
- **2-llm-injection-fuzzer**: Adaptive LLM prompt injection fuzzer
- **3-phishing-awareness-sim**: Authorized phishing awareness simulator
- **4-c2-detection-lab**: C2 beacon simulator + detection engineering
- **5-pentest-report-copilot**: AI-assisted pentest report generator

## Quick Start

### Linux / macOS / Kali
```bash
tar -xzf rtai-suite-4.0.0-airgap.tar.gz
cd rtai-suite-4.0.0
chmod +x install.sh
./install.sh
```

### Windows
```cmd
tar -xzf rtai-suite-4.0.0-airgap.tar.gz
cd rtai-suite-4.0.0
install.bat
```

## Requirements

- Python 3.11+
- No internet connection required after extraction
- Kali Linux: use `--break-system-packages` or create venv first

## Verification

After installation:
```bash
python verify_installation.py
```

## Tools Available

| Tool | Command |
|------|---------|
| Recon Agent | `rtai recon --target example.com` |
| Injection Fuzzer | `rtai fuzz --url http://localhost:11434/v1 --model llama3.1` |
| Phishing Sim | `python campaign.py --config samples/campaign.example.json --validate-config-only` |
| C2 Listener | `python listener.py --port 8080` |
| C2 Beacon | `python beacon.py --count 12` |
| Report Copilot | `python copilot.py --nmap samples/sample-nmap.xml --company "Acme Corp" --no-llm` |

## API Server

```bash
export RTAI_API_TOKEN=your-token
python services/api/server.py --port 9000
```

## Documentation

- `docs/` - All documentation
- `mkdocs serve` - Local documentation server
- `docs/PROJECT_PROPOSAL.md` - Project proposal
- `docs/STUDY_GUIDE.md` - Study guide with viva Q&A
- `docs/DEMO_RUNBOOK.md` - Live demo runbook
- `docs/GRADING_RUBRIC.md` - Grading rubric

## Verification

```bash
python verify_installation.py
```

## Support

See `docs/SECURITY_AND_ETHICS.md` for authorization requirements.
See `docs/SECURITY.md` for vulnerability reporting.
"""

        (Path("README_OFFLINE.md")).write_text(readme)
'''

# Find and replace the method
start = content.find('def _create_verification_script(self, bundle_dir: Path):')
if start >= 0:
    next_method = content.find('    def _create_offline_readme', start)
    if next_method == -1:
        next_method = len(content)
    
    new_content = content[:start] + new_method + content[next_method:]
    with open('rtai_core/military_airgap.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Replaced _create_verification_script method')
else:
    print('Method not found')

print('Done')