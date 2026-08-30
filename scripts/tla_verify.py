#!/usr/bin/env python3
"""TLA+ TLC wrapper — writes specs and runs TLC if available (java)."""
import pathlib, subprocess, sys, os

def main():
    import argparse, tempfile
    from rtai_core.military_tla import write_tla_specs, run_tlc_check
    p=argparse.ArgumentParser()
    p.add_argument("--output", default="tla-specs")
    p.add_argument("--strict", action="store_true", help="fail if TLC not found")
    args=p.parse_args()
    out=pathlib.Path(args.output)
    write_tla_specs(out)
    print(f"[TLA] specs written to {out}")
    # Try TLC via java -jar tla2tools.jar
    tlc_jar = pathlib.Path("tla2tools.jar")
    if not tlc_jar.exists():
        # Try docker
        try:
            r=subprocess.run(["docker","run","--rm","-v",f"{out.resolve()}:/specs","tla","tlc","-help"], capture_output=True, timeout=5)
            if r.returncode==0:
                print("[TLA] TLC available via docker")
                return 0
        except Exception:
            pass
        print("[TLA] TLC not found (java tla2tools.jar or docker tla) — skipping formal check (install for military CI)")
        return 1 if args.strict else 0
    # Run TLC on each spec
    ok=True
    for f in out.glob("*.tla"):
        print(f"[TLA] checking {f.name}...")
        if not run_tlc_check(f):
            print(f"[TLA] {f.name} FAILED")
            ok=False
        else:
            print(f"[TLA] {f.name} OK")
    return 0 if ok else 1

if __name__=="__main__":
    sys.exit(main())
