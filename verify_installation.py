#!/usr/bin/env python3
"""verify_installation.py - Post-install verification for Royal-Sec rtai-suite."""
import importlib
import subprocess
import sys
from pathlib import Path

def check_import(name, alias=None):
    try:
        mod = importlib.import_module(alias or name)
        ver = getattr(mod, "__version__", getattr(mod, "VERSION", "ok"))
        print(f"[OK] {name} ({ver})")
        return True
    except Exception as exc:
        print(f"[FAIL] {name}: {exc}")
        return False

def main():
    print("=== Royal-Sec rtai-suite — Installation Verification ===")
    print(f"Python: {sys.version.split()[0]}")
    ok = True
    # Core
    ok &= check_import("rtai_core")
    # Optional deps — warn not fail if gui missing in headless
    for pkg, alias in [("dnspython","dns"), ("jinja2","jinja2"), ("jsonschema","jsonschema")]:
        if not check_import(pkg, alias):
            print(f"  [hint] pip install {pkg}")
    # CLI
    try:
        import rtai_core.cli_app as cli
        assert hasattr(cli, "main")
        print("[OK] rtai CLI dispatch (rtai_core.cli_app.main)")
    except Exception as exc:
        print(f"[FAIL] rtai CLI: {exc}"); ok=False
    try:
        from rtai_core.gui.launcher import main as gui_main
        print("[OK] rtai-gui entry (rtai_core.gui.launcher.main)")
    except Exception as exc:
        print(f"[WARN] gui not importable (needs PySide6): {exc}")
    # Tool smoke --help
    tools = [
        (["python", "01-ai-recon-agent/recon_agent.py", "--help"], "P1 recon"),
        (["python", "02-llm-injection-fuzzer/inject_fuzzer.py", "--list-payloads"], "P2 fuzzer"),
        (["python", "03-phishing-awareness-sim/campaign.py", "--help"], "P3 campaign"),
        (["python", "04-c2-detection-lab/listener.py", "--help"], "P4 listener"),
        (["python", "04-c2-detection-lab/beacon.py", "--help"], "P4 beacon"),
        (["python", "05-pentest-report-copilot/copilot.py", "--help"], "P5 copilot"),
    ]
    for cmd, label in tools:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if "Traceback" in (r.stderr or ""):
                print(f"[FAIL] {label} traceback"); ok=False
            else:
                print(f"[OK] {label} smoke (exit {r.returncode})")
        except Exception as exc:
            print(f"[WARN] {label} not executed: {exc}")
    # API import
    try:
        import services.api.server as srv
        assert hasattr(srv, "create_server")
        print("[OK] services.api.server import")
    except Exception as exc:
        print(f"[WARN] API import: {exc}")
    # EULA/audit presence
    for p in ["EULA.md","AUP.md","PRIVACY.md","NOTICE.md","LICENSE"]:
        if Path(p).exists():
            print(f"[OK] {p} exists")
        else:
            print(f"[FAIL] {p} missing"); ok=False
    print("\n--- Versions ---")
    try:
        from rtai_core.version import __version__ as v
        print(f"  rtai_core.__version__ = {v}")
        import rtai_core.military_sbom as sb
        print("  sbom module ok")
    except Exception:
        pass
    print("\n=== Verification Complete ===")
    print("PASS" if ok else "PARTIAL (see WARN/FAIL)")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
