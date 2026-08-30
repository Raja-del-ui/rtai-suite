#!/usr/bin/env python3
"""STIG enforcement — check host against DISA STIG profiles (Linux + Python)."""
import json, sys, pathlib, subprocess, os

def check_linux_stig():
    failures = []
    # Check non-root container (Dockerfile USER rtai)
    if os.geteuid() == 0 if hasattr(os, "geteuid") else False:
        # In container, check if running as rtai
        import pwd
        try:
            if pwd.getpwuid(os.getuid()).pw_name == "root":
                failures.append("SV-230244: running as root, expected rtai (Dockerfile USER rtai)")
        except Exception:
            pass
    # Check FIPS
    if os.environ.get("RTAI_FIPS") != "1":
        failures.append("SV-230246: FIPS not enabled (RTAI_FIPS=1)")
    # Check audit WORM
    if os.environ.get("RTAI_AUDIT_WORM") != "1":
        failures.append("AUDIT: WORM not enabled (RTAI_AUDIT_WORM=1)")
    # Check mTLS in prod
    if os.environ.get("RTAI_MTLS") != "1" and not os.environ.get("RTAI_TLS_CERT"):
        failures.append("NET: mTLS not enabled (RTAI_TLS_CERT)")
    return failures

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--enforce", action="store_true", help="exit 1 on failures (CI gate)")
    args=p.parse_args()
    fails=check_linux_stig()
    if fails:
        print("[STIG] FAILURES:")
        for f in fails:
            print(f"  - {f}")
        if args.enforce:
            print("[STIG] enforcement failed (would block ATO)")
            return 1
        else:
            print("[STIG] dry-run (not enforcing)")
            return 0
    print("[STIG] all checks passed")
    return 0

if __name__=="__main__":
    sys.exit(main())
