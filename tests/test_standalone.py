"""Standalone guarantee: every project main() must launch from its own folder
using only its vendored rtai_core + requirements.txt - no repo-wide install.

Runs each tool with --help via subprocess (argparse exits 0 before any heavy
work), which proves the full import graph of that project resolves standalone.
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

LAUNCH_CHECKS = [
    ("01-ai-recon-agent", "recon_agent.py", ["--help"]),
    ("02-llm-injection-fuzzer", "inject_fuzzer.py", ["--help"]),
    ("03-phishing-awareness-sim", "campaign.py", ["--help"]),
    ("03-phishing-awareness-sim", "landing.py", ["--help"]),
    ("04-c2-detection-lab", "listener.py", ["--help"]),
    ("04-c2-detection-lab", "beacon.py", ["--help"]),
    ("05-pentest-report-copilot", "copilot.py", ["--help"]),
]


def _launch(project: str, script: str, args: list) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, script, *args],
        cwd=str(ROOT / project),
        capture_output=True,
        text=True,
        timeout=90,
    )


@pytest.mark.parametrize("project,script,args", LAUNCH_CHECKS,
                         ids=[f"{p}/{s}" for p, s, _ in LAUNCH_CHECKS])
def test_project_launches_standalone(project, script, args):
    result = _launch(project, script, args)
    combined = (result.stdout + result.stderr).lower()
    assert result.returncode == 0, (
        f"{project}/{script} failed standalone launch:\n"
        f"{result.stdout[-800:]}\n{result.stderr[-800:]}")
    assert "usage" in combined or "options" in combined


def test_p1_reports_missing_dnspython_friendly():
    """Without dnspython, collection must fail with an actionable message."""
    import os

    env_copy = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    code = "\n".join([
        "import sys",
        "sys.path.insert(0, '.')",
        "import sources",
        "sources._DNS_OK = False",
        "try:",
        "    sources.dns_records('lab.example')",
        "except RuntimeError as exc:",
        "    print('FRIENDLY:', exc)",
        "    raise SystemExit(7)",
        "raise SystemExit(8)",
    ])
    result = subprocess.run([sys.executable, "-c", code],
                            cwd=str(ROOT / "01-ai-recon-agent"),
                            capture_output=True, text=True, timeout=60, env=env_copy)
    assert result.returncode == 7
    assert "pip install dnspython" in result.stdout
