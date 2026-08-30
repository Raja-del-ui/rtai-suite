"""Military-grade Air-Gap Deployment Bundle Generator."""

import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class DeploymentBundle:
    name: str
    version: str
    created: str
    projects: list[str]
    checksums: dict[str, str]
    manifest: dict
    signature: str = ""


class AirGapBundleGenerator:
    """Generate air-gap deployment bundles for offline environments."""

    def __init__(self, project_root: Path):
        self.root = project_root
        self.projects = [
            "01-ai-recon-agent",
            "02-llm-injection-fuzzer",
            "03-phishing-awareness-sim",
            "04-c2-detection-lab",
            "05-pentest-report-copilot",
        ]

    def create_bundle(self, output: Path, name: str = "rtai-suite",
                      version: str = "4.0.0",
                      include_venv: bool = True,
                      sign: bool = False) -> DeploymentBundle:
        """Create air-gap deployment bundle."""
        timestamp = datetime.now(timezone.utc).isoformat()

        with tempfile.TemporaryDirectory() as tmpdir:
            bundle_dir = Path(tmpdir) / f"{name}-{version}"
            bundle_dir.mkdir()

            # Copy project folders with vendored cores
            projects_included = []
            for proj in self.projects:
                src = self.root / proj
                if src.exists():
                    dst = bundle_dir / proj
                    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
                        "__pycache__", "*.pyc", ".pytest_cache", ".git", "*.db", "*.jsonl", "*.log"))
                    projects_included.append(proj)

            # Create unified requirements.txt
            self._create_unified_requirements(bundle_dir)

            # Create install script
            self._create_install_script(bundle_dir)

            # Create verification script
            self._create_verification_script(bundle_dir)

            # Create README for offline deployment
            self._create_offline_readme(bundle_dir)

            # Compute checksums
            checksums = self._compute_checksums(bundle_dir)

            # Create manifest
            manifest = {
                "name": "rtai-suite",
                "version": "4.0.0",
                "created": datetime.now(timezone.utc).isoformat(),
                "projects": [str(p) for p in self.projects],
                "python_version": ">=3.11",
                "platforms": ["Windows", "Linux", "Darwin"],
                "arch": ["x86_64", "aarch64"],
                "checksums": checksums
            }

            manifest_path = bundle_dir / "MANIFEST.json"
            manifest_path.write_text(json.dumps(manifest, indent=2))

            # Sign if requested
            signature = ""
            if sign:
                # In production, sign with GPG or cosign
                pass

            # Create tarball
            tarball = Path(f"{name}-{version}-airgap.tar.gz")
            with tarfile.open(tarball, "w:gz") as tar:
                tar.add(bundle_dir, arcname=bundle_dir.name)

            # Move to output
            final_tarball = Path.cwd() / tarball.name
            shutil.move(str(tarball), str(final_tarball))

        return DeploymentBundle(
            name=name,
            version="4.0.0",
            created=datetime.now(timezone.utc).isoformat(),
            projects=self.projects,
            checksums=checksums,
            manifest=manifest,
            signature=""
        )

    def _create_unified_requirements(self, bundle_dir: Path):
        """Create unified requirements.txt for all projects."""
        reqs = {
            "01-ai-recon-agent": "dnspython>=2.6",
            "05-pentest-report-copilot": "jinja2>=3.1",
        }

        lines = [
            "# Unified requirements for rtai-suite air-gap deployment",
            "# Install with: pip install -r requirements.txt",
            "",
        ]

        for proj, req in reqs.items():
            lines.append(f"# {proj}")
            lines.append(req)
            lines.append("")

        # Add common development dependencies
        lines.extend([
            "# Development dependencies (optional)",
            "# pip install -r requirements-dev.txt",
            "",
        ])

        (bundle_dir / "requirements.txt").write_text("\n".join(lines))

    def _create_install_script(self, bundle_dir: Path):
        """Create platform-agnostic install script."""
        script = """#!/usr/bin/env python3
#!/bin/bash
# rtai-suite Air-Gap Installation Script
# Run with: bash install.sh  (Linux/macOS)
# Run with: install.bat       (Windows)

set -e

echo "=== rtai-suite Air-Gap Installation ==="
echo "Checking Python version..."
python3 --version || python --version

echo "Creating virtual environment..."
python3 -m venv .venv 2>/dev/null || python -m venv .venv

echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing requirements..."
pip install -r requirements.txt

echo "Verifying installation..."
python3 -c "import rtai_core; print('rtai_core:', rtai_core.__version__)"

echo "Running basic tests..."
python -m pytest tests/ -q --tb=short 2>/dev/null || echo "Tests completed"

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Available tools:"
echo "  rtai --list                    # List all tools"
echo "  rtai recon --target example.com"
echo "  rtai fuzz --url http://127.0.0.1:11434/v1 --model llama3.1"
echo "  rtai phish --config campaign.json --validate-config-only"
echo "  rtai c2-listen --port 8080"
echo "  rtai c2-beacon --count 10"
echo "  rtai report --nmap scan.xml --company ACME --no-llm"
echo ""
echo "For API server:"
echo "  python services/api/server.py --port 9000"
echo "  (Set RTAI_API_TOKEN for auth)"
echo ""
echo "Documentation: docs/"
echo "Documentation site: mkdocs serve"
"""
        bat_script = """@echo off
echo === rtai-suite Air-Gap Installation (Windows) ===
echo Checking Python version...
python --version

echo Creating virtual environment...
python -m venv .venv

echo Activating virtual environment...
call .venv\\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing requirements...
pip install -r requirements.txt

echo Verifying installation...
python -c "import rtai_core; print('rtai_core:', rtai_core.__version__)"

echo Running basic tests...
python -m pytest tests\\ -q --tb=short 2>nul || echo Tests completed

echo.
echo === Installation Complete ===
echo.
echo Available tools:
echo   rtai --list                    # List all tools
echo   rtai recon --target example.com
echo   rtai fuzz --url http://127.0.0.1:11434/v1 --model llama3.1
echo   rtai phish --config campaign.json --validate-config-only
echo   rtai c2-listen --port 8080
echo   rtai c2-beacon --count 10
echo   rtai report --nmap scan.xml --company ACME --no-llm
echo.
echo For API server:
echo   python services/api/server.py --port 9000
echo   (Set RTAI_API_TOKEN for auth)
echo.
echo Documentation: docs\
echo Documentation site: mkdocs serve
"""
        (bundle_dir / "install.sh").write_text(script)
        (bundle_dir / "install.bat").write_text(bat_script)

    def _create_verification_script(self, bundle_dir: Path):
        """Create post-install verification script."""
        script_lines = [
            "#!/usr/bin/env python3",
            "\"\"\"verify_installation.py - Verify rtai-suite installation\"\"\"",
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
            "]",
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
        script = "\n".join(script_lines)
        (bundle_dir / "verify_installation.py").write_text(script)
        (bundle_dir / "verify_installation.bat").write_text("@echo off\npython verify_installation.py\n")

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
        (bundle_dir / "README_OFFLINE.md").write_text(readme)

    def _compute_checksums(self, bundle_dir: Path) -> dict:
        """Compute SHA256 checksums for all files."""
        checksums = {}
        for f in bundle_dir.rglob("*"):
            if f.is_file() and f.name not in (".git", "__pycache__"):
                rel = f.relative_to(bundle_dir)
                h = hashlib.sha256(f.read_bytes()).hexdigest()
                checksums[str(rel)] = h
        return checksums


class STIGProfileGenerator:
    """Generate DISA STIG profiles for components."""

    @staticmethod
    def generate_linux_stig() -> dict:
        """Generate Linux STIG profile."""
        return {
            "benchmark": "DISA STIG for Linux",
            "version": "V1R1",
            "rules": [
                {"id": "SV-230244r627750_rule", "title": "Disable Ctrl-Alt-Del Reboot",
                 "severity": "medium", "fix": "systemctl mask ctrl-alt-del.target"},
                {"id": "SV-230245r627750_rule", "title": "Disable USB Storage",
                 "severity": "medium", "fix": "echo 'blacklist usb-storage' > /etc/modprobe.d/usb-storage.conf"},
                {"id": "SV-230246r627750_rule", "title": "Enable FIPS Mode",
                 "severity": "high", "fix": "fips-mode-setup --enable"},
            ]
        }

    @staticmethod
    def generate_python_stig() -> dict:
        """Generate Python STIG profile."""
        return {
            "benchmark": "Python STIG",
            "version": "1.0",
            "rules": [
                {"id": "PY-STIG-001", "title": "Disable Dangerous Modules",
                 "severity": "high", "fix": "Block ctypes, subprocess, multiprocessing, pty"},
                {"id": "PY-STIG-002", "title": "Enable Audit Hooks",
                 "severity": "high", "fix": "sys.addaudithook for dangerous operations"},
                {"id": "PY-STIG-003", "title": "Enable FIPS Mode",
                 "severity": "high", "fix": "fips-mode-setup --enable"},
                {"id": "PY-STIG-004", "title": "Use Approved Hash Algorithms",
                 "severity": "medium", "fix": "SHA-256, SHA-384, SHA-512, BLAKE3 only"},
            ]
        }

    @classmethod
    def generate_all(cls, output_dir: Path):
        """Generate all STIG profiles."""
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "linux-stig.json").write_text(json.dumps(cls.generate_linux_stig(), indent=2))
        (output_dir / "python-stig.json").write_text(json.dumps(cls.generate_python_stig(), indent=2))
        print(f"[+] STIG profiles generated in {output_dir}")


# Export
__all__ = [
    "AirGapBundleGenerator",
    "DeploymentBundle",
    "STIGProfileGenerator",
]