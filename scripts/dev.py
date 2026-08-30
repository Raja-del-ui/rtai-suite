#!/usr/bin/env python3
"""Developer task runner - the single entry point for repo workflows.

Usage:
    python scripts/dev.py test      # full pytest suite
    python scripts/dev.py lint      # ruff check
    python scripts/dev.py compile   # byte-compile every source file
    python scripts/dev.py slides    # regenerate docs/PRESENTATION_SLIDES.pptx
    python scripts/dev.py ci        # lint + compile + test (local CI simulation)
"""

import argparse
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def run(cmd):
    print(f":: {' '.join(str(part) for part in cmd)}")
    return subprocess.run(cmd, cwd=str(ROOT)).returncode


def cmd_test(_args):
    return run([sys.executable, "-m", "pytest"])


def cmd_compile(_args):
    return run([sys.executable, "-m", "compileall", "-q", "rtai_core", "services", "tools", "tests",
                "01-ai-recon-agent", "02-llm-injection-fuzzer", "03-phishing-awareness-sim",
                "04-c2-detection-lab", "05-pentest-report-copilot"])


def cmd_lint(_args):
    if run([sys.executable, "-m", "ruff", "--version"]) != 0:
        print("[!] ruff not installed: pip install ruff")
        return 1
    return run([sys.executable, "-m", "ruff", "check", "."])


def cmd_slides(_args):
    return run([sys.executable, str(ROOT / "tools" / "make_slides.py")])


def cmd_ci(_args):
    codes = [cmd_lint(None), cmd_compile(None), cmd_test(None)]
    return max(codes)


HANDLERS = {
    "test": cmd_test,
    "lint": cmd_lint,
    "compile": cmd_compile,
    "slides": cmd_slides,
    "ci": cmd_ci,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=sorted(HANDLERS))
    args = parser.parse_args()
    return HANDLERS[args.command](None) or 0


if __name__ == "__main__":
    raise SystemExit(main())
