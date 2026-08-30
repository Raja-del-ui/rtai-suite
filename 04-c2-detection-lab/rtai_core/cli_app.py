"""Unified product CLI: one entry point that dispatches into every tool.

    rtai --list
    rtai recon --target example.com
    rtai fuzz --url http://127.0.0.1:11434/v1 --model llama3.1
    rtai phish --config campaign.json --validate-config-only
    rtai c2-listen --port 8080          rtai c2-beacon --count 5
    rtai report --nmap scan.xml --company "Acme"

Locates the repository by scanning upward from the current directory for the
project folders (0*-*), or honors the RTAI_HOME environment variable.
"""

import os
import runpy
import sys
from pathlib import Path

TOOLS = {
    "recon": "01-ai-recon-agent/recon_agent.py",
    "fuzz": "02-llm-injection-fuzzer/inject_fuzzer.py",
    "phish": "03-phishing-awareness-sim/campaign.py",
    "phish-landing": "03-phishing-awareness-sim/landing.py",
    "phish-metrics": "03-phishing-awareness-sim/metrics.py",
    "c2-listen": "04-c2-detection-lab/listener.py",
    "c2-beacon": "04-c2-detection-lab/beacon.py",
    "c2-analyze": "04-c2-detection-lab/analyze.py",
    "report": "05-pentest-report-copilot/copilot.py",
    "mission": "rtai_core/mission_cli.py",
    "gui": "rtai_core/gui/launcher.py",
}


def find_repo_root(start: Path, tool: str | None = None) -> Path:
    override = os.environ.get("RTAI_HOME")
    if override:
        candidate = Path(override)
        # G4.3 fix: validate per-tool, not all TOOLS.values(), so trimmed bundles work
        if tool:
            if (candidate / TOOLS[tool]).exists():
                try:
                    from rtai_core.audit import record as _audit
                    from rtai_core.audit import actor_from_env as _actor
                    _audit("rtai_home_override", actor=_actor(), tool=tool, home=str(candidate))
                except Exception:
                    pass
                return candidate
            raise SystemExit(f"[x] RTAI_HOME={override} does not contain tool '{tool}' ({TOOLS[tool]} missing)")
        # No tool specified: require at least core markers, not every tool
        if (candidate / "rtai_core" / "version.py").exists() and (candidate / "pyproject.toml").exists():
            try:
                from rtai_core.audit import record as _audit
                from rtai_core.audit import actor_from_env as _actor
                _audit("rtai_home_override", actor=_actor(), tool="unknown", home=str(candidate))
            except Exception:
                pass
            return candidate
        if all((candidate / rel).exists() for rel in TOOLS.values()):
            return candidate
        raise SystemExit(f"[x] RTAI_HOME={override} does not contain the suite")
    current = start.resolve()
    for candidate in [current, *current.parents]:
        # Prefer full suite detection, but allow trimmed bundle with requested tool
        if tool and (candidate / TOOLS[tool]).exists():
            return candidate
        if all((candidate / rel).exists() for rel in TOOLS.values()):
            return candidate
        if (candidate / "rtai_core" / "version.py").exists() and (candidate / "pyproject.toml").exists():
            # Fallback for trimmed but valid root — ensure at least the requested tool if any
            if tool is None or (candidate / TOOLS[tool]).exists():
                return candidate
    raise SystemExit("[x] suite root not found from "
                     f"{start} (set RTAI_HOME to the repo checkout)")


def dispatch(tool: str, argv: list) -> int:
    if tool not in TOOLS:
        print(f"[x] unknown tool '{tool}' (see: rtai --list)")
        return 2
    # G10: audit every dispatch (including --help passthrough) — inventory enumeration is logged
    try:
        from rtai_core.audit import record as _audit
        from rtai_core.audit import actor_from_env as _actor
        _audit("rtai_dispatch", actor=_actor(), tool=tool, argv=" ".join(argv[:5]))
    except Exception:
        pass
    root = find_repo_root(Path.cwd(), tool=tool)
    script = root / TOOLS[tool]
    if not script.exists():
        print(f"[x] tool '{tool}' not found at {script} (trimmed bundle?)", file=sys.stderr)
        return 66
    sys.argv = [tool, *argv]

    # Project scripts import siblings (llm_client, sources, ...) relative to
    # their own folder; runpy does not add it, so we do - temporarily.
    script_dir = str(script.parent)
    added = script_dir not in sys.path
    if added:
        sys.path.insert(0, script_dir)
    try:
        runpy.run_path(str(script), run_name="__main__")
    except SystemExit as exc:
        code = exc.code
        if code is None or code is True:
            return 0
        if isinstance(code, str):
            print(f"[x] {code}", file=sys.stderr)
            return 70
        return int(code)
    finally:
        if added:
            sys.path.remove(script_dir)
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        try:
            from rtai_core.audit import record as _audit
            from rtai_core.audit import actor_from_env as _actor
            _audit("rtai_inventory", actor=_actor(), action="help")
        except Exception:
            pass
        width = max(len(k) for k in TOOLS)
        print("rtai - unified AI red-team toolkit (Royal-Sec authorized use only)\n")
        print("usage: rtai <tool> [tool-args...]\n")
        for name in sorted(TOOLS):
            print(f"  {name:<{width}}  {TOOLS[name]}")
        return 0
    if argv[0] == "--list":
        try:
            from rtai_core.audit import record as _audit
            from rtai_core.audit import actor_from_env as _actor
            _audit("rtai_inventory", actor=_actor(), action="list")
        except Exception:
            pass
        print("\n".join(sorted(TOOLS)))
        return 0
    return dispatch(argv[0], argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
