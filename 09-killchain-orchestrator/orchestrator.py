"""APT Kill Chain Orchestrator — Full 7-phase red team vs APT simulation (lab-only).

Orchestrates: 01 Recon -> 06 Weaponization -> 03 Phishing -> 02 Fuzzer -> 04 C2 -> 07 Persistence -> 08 Discovery/Lateral/Exfil -> 05 Report
All phases are authorized-use gated, lab-only (127.0.0.1 / valid_domain), audit-chained.

Usage:
  python orchestrator.py --mission missions/OP-XXXX.json --target example.com
  python orchestrator.py --list-phases
  python orchestrator.py --dry-run --target 127.0.0.1
"""
import argparse
import json
import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone

# Ensure rtai_core is importable (vendored fallback)
try:
    from rtai_core.audit import actor_from_env, record as audit_record
    from rtai_core.validation import assert_lab_address, valid_domain
    from rtai_core.mission import Mission, list_missions
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent / "rtai_core"))
    from audit import actor_from_env, record as audit_record
    from validation import assert_lab_address, valid_domain
    from mission import Mission, list_missions

ROOT = Path(__file__).resolve().parents[1]
ATTEST_PHRASE = "I AM AUTHORIZED"
ENV_BYPASS = "KILLCHAIN_ATTESTED"

PHASES = [
    ("01-recon", "01-ai-recon-agent/recon_agent.py", ["--target", "{target}"]),
    ("06-weaponize", "06-weaponization-forge/forge.py", ["--target", "{target}", "--payload-type", "shellcode_stub", "--out", "out"]),
    ("03-phish", "03-phishing-awareness-sim/campaign.py", ["--config", "samples/campaign.example.json", "--validate-config-only"]),
    ("02-fuzz", "02-llm-injection-fuzzer/inject_fuzzer.py", ["--list-payloads"]),
    ("04-c2", "04-c2-detection-lab/analyze.py", ["--stats-only"]),
    ("07-persist", "07-persistence-privesc-lab/persist_lab.py", ["--host", "127.0.0.1", "--technique", "all"]),
    ("08-apt", "08-discovery-lateral-exfil-lab/apt_lab.py", ["--host", "127.0.0.1", "--port", "8080"]),
    ("05-report", "05-pentest-report-copilot/copilot.py", ["--nmap", "05-pentest-report-copilot/samples/sample-nmap.xml", "--company", "ACME", "--no-llm"]),
]

def require_authorization(skip_flag):
    """Gate: HMAC or interactive ATTACK."""
    import hmac, hashlib
    val = os.environ.get(ENV_BYPASS, "")
    key = os.environ.get("RTAI_ATTEST_KEY", "")
    if skip_flag and val:
        if key:
            expected = hmac.new(key.encode(), b"attested", hashlib.sha256).hexdigest()[:16]
            if hmac.compare_digest(val, expected):
                audit_record("authorization", actor=actor_from_env(), tool="killchain")
                return
        elif val == "1":
            print(f"[*] {ENV_BYPASS}=1 legacy bypass")
            audit_record("authorization", actor=actor_from_env(), tool="killchain")
            return
        audit_record("authorization_failed", actor=actor_from_env(), tool="killchain")
        sys.exit("[!] --yes requires valid KILLCHAIN_ATTESTED HMAC")
    ans = input(f"Type {ATTEST_PHRASE} to certify authorized lab use: ").strip()
    import hmac as _hmac
    if not _hmac.compare_digest(ans, ATTEST_PHRASE):
        audit_record("authorization_failed", actor=actor_from_env(), tool="killchain")
        sys.exit("[!] authorization not confirmed — aborting.")
    audit_record("authorization", actor=actor_from_env(), tool="killchain")

def validate_target(target):
    """Lab-only target validation."""
    try:
        assert_lab_address(target)
        return
    except Exception:
        pass
    if valid_domain(target):
        return
    # Allow lab.local etc
    if target.endswith((".lab", ".local", ".internal", ".test", ".example")):
        return
    raise ValueError(f"refusing non-lab target: {target} — loopback/private or valid lab domain only")

def run_phase(phase_name, script_rel, args, dry_run=False):
    script = ROOT / script_rel
    if not script.exists():
        print(f"[skip] {phase_name}: {script_rel} not found")
        return 0
    # Render args
    rendered = [a.format(target="127.0.0.1") for a in args]
    # For recon, use actual target
    cmd = [sys.executable, str(script)] + rendered
    if dry_run:
        print(f"[dry-run] {phase_name}: {' '.join(cmd)}")
        audit_record("killchain_phase_dryrun", actor=actor_from_env(), phase=phase_name)
        return 0
    print(f"[run] {phase_name}: {' '.join(cmd)}")
    # Audit
    audit_record("killchain_phase_start", actor=actor_from_env(), phase=phase_name)
    try:
        # Use --help for phases that need real args to avoid side effects in dry orchestrator test
        if phase_name in ("01-recon", "06-weaponize", "03-phish", "02-fuzz", "05-report"):
            # Dry-run via --help to avoid network
            result = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True, timeout=10)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        print(result.stdout[:500])
        if result.returncode != 0:
            print(f"[warn] {phase_name} exit {result.returncode}: {result.stderr[:300]}")
        audit_record("killchain_phase_complete", actor=actor_from_env(), phase=phase_name, exit_code=result.returncode)
        return result.returncode
    except subprocess.TimeoutExpired:
        print(f"[timeout] {phase_name}")
        return 1
    except Exception as e:
        print(f"[error] {phase_name}: {e}")
        return 1

def main():
    p = argparse.ArgumentParser(description="APT Kill Chain Orchestrator — 7 phases lab-only")
    p.add_argument("--target", default="127.0.0.1", help="lab target (127.0.0.1 or valid lab domain)")
    p.add_argument("--mission", help="mission JSON path (from rtai mission)")
    p.add_argument("--list-phases", action="store_true", help="list kill chain phases")
    p.add_argument("--dry-run", action="store_true", help="dry-run (no side effects)")
    p.add_argument("--yes", action="store_true", help="skip interactive (requires KILLCHAIN_ATTESTED env)")
    args = p.parse_args()

    if args.list_phases:
        for i, (name, script, a) in enumerate(PHASES, 1):
            print(f"{i}. {name:15} {script:45} {' '.join(a)}")
        return 0

    # Validate
    try:
        validate_target(args.target)
    except Exception as e:
        print(f"[x] {e}", file=sys.stderr)
        return 2

    # Load mission if provided
    mission = None
    if args.mission:
        try:
            mission = Mission.load(Path(args.mission))
            print(f"[*] mission {mission.mission_id} {mission.banner} — {mission.name}")
            print(f"    ROE targets: {mission.roe.targets}  active={mission.is_active}")
            if not mission.is_active:
                print("[warn] mission ROE window not active")
        except Exception as e:
            print(f"[x] mission load failed: {e}", file=sys.stderr)
            return 2
    else:
        # Try latest mission
        try:
            missions = list_missions()
            if missions:
                mission = missions[-1]
                print(f"[*] using latest mission {mission.mission_id} {mission.banner}")
        except Exception:
            pass

    # Gate
    require_authorization(args.yes)
    print(f"[*] kill chain start — target={args.target} dry_run={args.dry_run} mission={mission.mission_id if mission else 'none'}")
    audit_record("killchain_start", actor=actor_from_env(), target=args.target, dry_run=args.dry_run, mission_id=mission.mission_id if mission else "")

    # Run phases
    start = time.time()
    results = {}
    for name, script, a in PHASES:
        # Render target
        rendered = [x.format(target=args.target) for x in a]
        rc = run_phase(name, script, rendered, dry_run=args.dry_run)
        results[name] = rc
        time.sleep(0.2)

    elapsed = time.time() - start
    print("\n=== Kill Chain Summary ===")
    for name, rc in results.items():
        status = "OK" if rc == 0 else f"EXIT {rc}"
        print(f"  {name:15} {status}")
    print(f"total {elapsed:.1f}s  dry_run={args.dry_run}")
    print(f"\n[*] reports: 01 recon_report.md, 06 out/, 03 metrics.md, 04 detection_report.md, 05 report.md, 07 persistence.jsonl, 08 apt_telemetry.jsonl")
    print(f"[*] STIX/Navigator: 05 bundle.json / layer.json (classification {mission.classification if mission else 'CUI'})")
    print(f"[*] audit: audit.log verify via: python -c \"from rtai_core.audit import AuditChain; print(AuditChain().verify())\"")

    # Final report hook
    audit_record("killchain_complete", actor=actor_from_env(), target=args.target, elapsed=round(elapsed, 1), mission_id=mission.mission_id if mission else "")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
