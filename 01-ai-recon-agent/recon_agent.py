"""AI Recon Agent: passive OSINT collection fused into an LLM attack-surface assessment.

Usage:
    python recon_agent.py --target example.com
    python recon_agent.py --target example.com --include-http --out report.md
    python recon_agent.py --target example.com --provider ollama --model llama3.1

Only performs ACTIVE checks (HTTP GET to the target web root) when --include-http is set.
"""

import argparse
import datetime as dt
import hmac
import json
import os
import sys

from analyst import analyze
from llm_client import ChatClient
from rtai_core.audit import actor_from_env, record as audit_record
from rtai_core.cli import ExitCode, banner, ok, run_main
from rtai_core.exceptions import ConfigError, ProviderError, ValidationError
from scoring import compute_score, diff_findings
from sources import collect, valid_domain


def require_recon_authorization(include_http: bool) -> None:
    """Gate for active HTTP fingerprinting. Passive recon is open; active requires attestation."""
    if not include_http:
        return
    # Check HMAC env bypass first (CI) — supports RTAI_ATTEST_KEY or legacy =1
    env_val = os.environ.get("RECON_ATTESTED") or os.environ.get("RTAI_RECON_ATTESTED") or ""
    if env_val:
        # If RTAI_ATTEST_KEY set, require HMAC; else legacy with warning
        import hashlib as _hl
        key = os.environ.get("RTAI_ATTEST_KEY")
        if key:
            expected = hmac.new(key.encode(), b"attested", _hl.sha256).hexdigest()[:16]
            if hmac.compare_digest(env_val, expected):
                audit_record("authorization", actor=actor_from_env(), tool="recon", mode="active-http", bypass="hmac")
                return
            else:
                audit_record("authorization_failed", actor=actor_from_env(), tool="recon", reason="hmac_mismatch")
                raise ValidationError("RECON_ATTESTED HMAC mismatch — set to hmac(RTAI_ATTEST_KEY, 'attested')[:16]")
        else:
            if hmac.compare_digest(env_val, "1"):
                print("[*] authorization attested via RECON_ATTESTED=1 (legacy — set RTAI_ATTEST_KEY for HMAC)")
                audit_record("authorization", actor=actor_from_env(), tool="recon", mode="active-http", bypass="env-legacy")
                return
    # Interactive attestation
    try:
        answer = input("Type I AM AUTHORIZED to certify you have written scope for --include-http active recon: ").strip()
    except EOFError:
        answer = ""
    if answer != "I AM AUTHORIZED":
        try:
            audit_record("authorization_failed", actor=actor_from_env(), tool="recon", reason="phrase_mismatch")
        except Exception:
            pass
        raise ValidationError("authorization not confirmed — aborting active recon (need I AM AUTHORIZED)")
    audit_record("authorization", actor=actor_from_env(), tool="recon", mode="active-http", bypass="interactive")

BANNER = r"""
   ___  ____  ____  _  _   ____  _____  ____  ___
  / _ \(  _ \(_  _)( \/ ) (_  _)(  _  )(  _ \/ __)
 ( (_) ) ) /   )(   )  (    )(   )(_)(  )(_) )\ \
  \___/(_\_)\ (__) (_/\_)  (__) (_____)(____/ |___/
        passive OSINT -> LLM attack-surface assessment
"""


def source_status_table(findings):
    lines = ["| Collector | Status |", "|---|---|"]
    for name, result in findings["sources"].items():
        state = "OK" if result["ok"] else f"FAILED ({result['error'][:60]})"
        lines.append(f"| {name} | {state} |")
    return "\n".join(lines)


def appendix_tables(findings):
    parts = []
    src = findings["sources"]

    dns = src.get("dns", {}).get("data") or {}
    if dns:
        rows = "\n".join(f"| {rtype} | {', '.join(vals) if vals else '-'} |"
                         for rtype, vals in sorted(dns.items()))
        parts.append("### DNS Records\n\n| Type | Values |\n|---|---|\n" + rows)

    email = src.get("email_security", {}).get("data") or {}
    if email:
        rows = "\n".join(f"| {k} | {v} |" for k, v in sorted(email.items()))
        parts.append("### Email Security\n\n| Control | Value |\n|---|---|\n" + rows)

    rdap = src.get("rdap", {}).get("data") or {}
    if rdap:
        rows = "\n".join(f"| {k} | {v} |" for k, v in sorted(rdap.items()) if v)
        parts.append("### Registration (RDAP)\n\n| Field | Value |\n|---|---|\n" + rows)

    subs = src.get("certificate_transparency", {}).get("data") or []
    if subs:
        shown = "\n".join(f"- `{s}`" for s in subs[:40])
        extra = f"\n\n_({len(subs)} total, showing first 40)_" if len(subs) > 40 else ""
        parts.append("### Subdomains via Certificate Transparency\n\n" + shown + extra)

    for key in ("https_fingerprint", "http_fingerprint"):
        data = src.get(key, {}).get("data")
        if data:
            rows = "\n".join(f"| {k} | {v} |" for k, v in sorted(data.items()) if v not in (None, []))
            parts.append(f"### HTTP Posture ({key.split('_')[0].upper()})\n\n| Field | Value |\n|---|---|\n" + rows)

    return "\n\n".join(parts)


def build_report(target, findings, ai_analysis, include_http):
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    mode = "PASSIVE + light HTTP fingerprinting" if include_http else "PASSIVE ONLY"
    header = (
        f"# Reconnaissance Report — {target}\n\n"
        f"*Generated {stamp} · Mode: {mode} · Authorized engagement use only*\n\n"
        f"## Collection Status\n\n{source_status_table(findings)}\n"
    )
    footer = (
        "\n\n---\n_AI-generated analysis: verify every claim against the raw evidence in "
        "`raw_findings.json` before acting on it._\n"
    )
    return header + "\n## AI Analysis\n\n" + ai_analysis + footer


def main():
    parser = argparse.ArgumentParser(description="AI-powered passive reconnaissance agent")
    parser.add_argument("--target", required=True, help="domain to profile, e.g. example.com")
    parser.add_argument("--include-http", action="store_true",
                        help="also fetch the target web root (light active check)")
    parser.add_argument("--out", default="recon_report.md")
    parser.add_argument("--raw", default="raw_findings.json")
    parser.add_argument("--json-out", dest="json_out", default="recon_findings.json",
                        help="machine-readable report (score + diff + evidence)")
    parser.add_argument("--baseline", help="previous raw_findings.json to diff against")
    parser.add_argument("--provider", choices=["openai", "anthropic", "ollama"])
    parser.add_argument("--model")
    parser.add_argument("--base-url")
    args = parser.parse_args()

    target = args.target.strip().lower()
    if not valid_domain(target):
        raise ValidationError(f"invalid domain: {args.target!r}")

    # Authorization gate for active mode (G1 closure)
    require_recon_authorization(args.include_http)

    banner(["AI RECON AGENT", f"target: {target}",
            f"mode : {'passive + http' if args.include_http else 'passive only'}"])

    print("[*] collecting (parallel collectors) ...")
    findings = collect(target, include_http=args.include_http)
    with open(args.raw, "w", encoding="utf-8") as fh:
        json.dump(findings, fh, indent=2)
    print(f"[+] raw evidence saved -> {args.raw}")
    for warning in findings["warnings"]:
        print(f"    [warn] {warning}")

    exposure = compute_score(findings)
    print(f"[*] deterministic exposure: {exposure['score']}/100 ({exposure['band']})")
    for _key, points, note in exposure["drivers"]:
        print(f"      - +{points:<3} {note}")

    changes = None
    if args.baseline:
        with open(args.baseline, encoding="utf-8") as fh:
            baseline = json.load(fh)
        changes = diff_findings(baseline, findings)
        print(f"[*] baseline diff vs {args.baseline}: {len(changes)} entries")

    print("[*] initializing LLM client ...")
    try:
        client = ChatClient(provider=args.provider, model=args.model, base_url=args.base_url)
    except ProviderError as exc:
        raise ConfigError(str(exc)) from exc
    print(f"[*] provider={client.provider} model={client.model}")

    print("[*] analyzing ...")
    try:
        ai_analysis = analyze(findings, client, exposure=exposure, changes=changes)
    except ProviderError as exc:
        raise ProviderError(f"analysis failed: {exc}") from exc

    report = build_report(target, findings, ai_analysis, args.include_http)
    if changes:
        report += ("\n## Changes Since Baseline\n\n" +
                   "\n".join(f"- {change}" for change in changes) + "\n")
    report += (f"\n## Deterministic Exposure Score\n\n**{exposure['score']}/100 "
               f"({exposure['band']})**\n\n| Driver | Points | Note |\n|---|---|---|\n" +
               "\n".join(f"| {key} | +{points} | {note} |"
                         for key, points, note in exposure["drivers"]) + "\n")
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(report)
    llm_exposure = next((line for line in ai_analysis.splitlines()
                         if "Overall exposure" in line), "")
    print(f"[+] report saved -> {args.out}")
    if llm_exposure:
        print(f"[*] {llm_exposure.strip()}")

    if args.json_out:
        payload = {
            "target": target,
            "generated": dt.datetime.now().isoformat(timespec="seconds"),
            "exposure": {"score": exposure["score"], "band": exposure["band"],
                         "drivers": exposure["drivers"]},
            "changes_since_baseline": changes or [],
            "evidence": findings,
        }
        with open(args.json_out, "w", encoding="utf-8") as jfh:
            json.dump(payload, jfh, indent=2, default=str)
        print(f"[+] machine report saved -> {args.json_out}")


if __name__ == "__main__":
    raise SystemExit(run_main(main))
