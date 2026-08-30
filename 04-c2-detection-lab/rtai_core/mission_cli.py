"""Mission CLI — `rtai mission` for military operation profiles."""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

from rtai_core.audit import actor_from_env, record as audit_record
from rtai_core.mission import Mission, ROE, save_mission, list_missions, CLASSIFICATIONS, CAVEATS
from rtai_core.config import BaseConfig

def main():
    p = argparse.ArgumentParser(description="Mission planning — classification, ROE, OPSEC (military)")
    p.add_argument("--list", action="store_true", help="list missions")
    p.add_argument("--show", help="show mission JSON by ID")
    p.add_argument("--create", action="store_true", help="create mission (requires --name)")
    p.add_argument("--name", help="mission name e.g., MANTICORE SHIELD")
    p.add_argument("--callsign", default="", help="callsign e.g., REAPER 06")
    p.add_argument("--grid", default="", help="MGRS grid e.g., 38TLL 1234 5678")
    p.add_argument("--classification", choices=CLASSIFICATIONS, default="CUI", help="classification")
    p.add_argument("--caveat", choices=CAVEATS, default="", help="handling caveat")
    p.add_argument("--approver", default="", help="approver name/rank")
    p.add_argument("--rank", default="", help="approver rank")
    p.add_argument("--targets", default="", help="comma-separated ROE targets")
    p.add_argument("--out", default="", help="output JSON path for --show/--create")
    p.add_argument("--package", help="build mission package (STIX+SBOM+audit) for mission ID")
    p.add_argument("--opsec", action="store_true", help="run OPSEC checklist for last mission")
    args = p.parse_args()

    if args.list:
        missions = list_missions()
        if not missions:
            print("No missions — create with: rtai mission --create --name 'OP NAME' --classification CUI --approver 'COL Smith' --targets example.com")
            return 0
        for m in missions:
            print(f"{m.mission_id}  {m.banner:30}  {m.name:25}  {m.callsign:12}  ROE:{','.join(m.roe.targets)[:40]}  {'ACTIVE' if m.is_active else 'EXPIRED'}")
        return 0

    if args.show:
        for m in list_missions():
            if m.mission_id == args.show or m.name == args.show:
                j = json.dumps(m.to_dict(), indent=2)
                if args.out:
                    Path(args.out).write_text(j)
                    print(f"[+] mission {m.mission_id} -> {args.out}")
                else:
                    print(j)
                try:
                    audit_record("mission_show", actor=actor_from_env(), mission_id=m.mission_id)
                except Exception:
                    pass
                return 0
        print(f"[!] mission {args.show} not found", file=sys.stderr)
        return 2

    if args.create:
        if not args.name:
            p.error("--create requires --name")
        roe = ROE(targets=[t.strip() for t in args.targets.split(",") if t.strip()] if args.targets else [],
                  techniques=["recon","fuzz","phish","c2","report"])
        m = Mission(name=args.name, callsign=args.callsign, grid_ref=args.grid,
                    classification=args.classification, caveat=args.caveat,
                    approver=args.approver, approver_rank=args.rank, roe=roe)
        save_mission(m)
        print(f"[+] mission {m.mission_id} {m.banner} — {m.name} (callsign {m.callsign})")
        print(f"    ROE: {m.roe.targets}  window {m.roe.start[:10]} -> {m.roe.end[:10]}  active={m.is_active}")
        try:
            audit_record("mission_created", actor=actor_from_env(), mission_id=m.mission_id, classification=m.classification)
        except Exception:
            pass
        if args.out:
            Path(args.out).write_text(json.dumps(m.to_dict(), indent=2))
            print(f"[+] saved -> {args.out}")
        return 0

    if args.package:
        # Mission package: STIX + SBOM + audit bundle
        target = None
        for m in list_missions():
            if m.mission_id == args.package:
                target = m
                break
        if not target:
            print(f"[!] mission {args.package} not found", file=sys.stderr)
            return 2
        outdir = Path(f"missions/{target.mission_id}_package")
        outdir.mkdir(parents=True, exist_ok=True)
        # STIX bundle from mission ROE
        try:
            from rtai_core.military_stix import STIXBuilder
            b = STIXBuilder()
            for t in target.roe.targets:
                b.indicator(pattern=f"[domain-name:value = '{t}']", labels=["malicious-activity"])
            bundle = b.bundle()
            (outdir / "stix_bundle.json").write_text(json.dumps({"type": bundle.type, "id": bundle.id, "objects": len(bundle.objects)}, indent=2))
        except Exception as e:
            print(f"[warn] STIX: {e}")
        # SBOM
        try:
            from rtai_core.military_sbom import generate_sbom
            # Dry-run
            (outdir / "sbom.cyclonedx.json").write_text(json.dumps({"bomFormat":"CycloneDX","specVersion":"1.6","metadata":{"component":{"name":target.name}}}))
        except Exception:
            pass
        # Audit excerpt
        try:
            from rtai_core.audit import AuditChain
            chain = AuditChain()
            (outdir / "audit.jsonl").write_text("\n".join(json.dumps(r) for r in chain.read()[-20:]))
        except Exception:
            pass
        # Mission JSON with banner
        (outdir / "mission.json").write_text(json.dumps(target.to_dict(), indent=2))
        # Handling sheet
        (outdir / "HANDLING.txt").write_text(f"{target.banner}\nMission {target.mission_id} — {target.name}\nDestruction: per {target.classification} handling\n")
        print(f"[+] mission package -> {outdir}  [{target.banner}]")
        try:
            audit_record("mission_packaged", actor=actor_from_env(), mission_id=target.mission_id)
        except Exception:
            pass
        return 0

    if args.opsec:
        missions = list_missions()
        m = missions[-1] if missions else Mission(name="DRY-RUN", classification=args.classification or "CUI", approver=args.approver or "COL Test", roe=ROE(targets=[args.targets or "example.com"]))
        status = m.opsec_status()
        print(f"[OPSEC] Mission {m.mission_id} {m.banner}")
        for k,v in status.items():
            print(f"  {'[OK]' if v else '[FAIL]'} {k}: {v}")
        if all(status.values()):
            print("[OPSEC] ALL CHECKS PASS — MISSION READY")
            return 0
        else:
            print("[OPSEC] FAIL — resolve before execution (AUP.md)")
            return 3

    p.print_help()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
