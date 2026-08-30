"""Phishing Awareness Simulator: LLM-drafted, template-governed training campaigns.

Usage:
    python campaign.py --config samples/campaign.example.json --template password_expiry
    python campaign.py --config my_campaign.json --validate-config-only
    python campaign.py --config my_campaign.json --send     # requires allow_send=true

Every .eml is stamped with an X-PhishSim header so mail systems can whitelist it.
Sending requires BOTH config 'allow_send': true AND the --send flag AND typed attestation.
"""

import argparse
import datetime as dt
import json
import pathlib
import smtplib
import ssl
import sys
import uuid

import auth
from generator import answer_key, build_eml, campaign_manifest, generate_email, links_csv
from llm_client import ChatClient, LLMError
from rtai_core.audit import actor_from_env, record as audit_record
from templates import TEMPLATES


def load_config(path):
    with open(path, encoding="utf-8") as fh:
        config = json.load(fh)
    auth.validate_campaign(config)
    return config


def maybe_send(config, eml_bytes, recipient, dry_run=True):
    smtp = config.get("smtp")
    if dry_run or not smtp:
        return False
    with smtplib.SMTP(smtp["host"], int(smtp.get("port", 587)), timeout=30) as server:
        if smtp.get("starttls", True):
            server.starttls(context=ssl.create_default_context())
        if smtp.get("user"):
            server.login(smtp["user"], smtp.get("password", ""))
        server.sendmail(config["sender_domain"] and smtp.get("from_override",
                        f"security-alerts@{config['sender_domain']}"), [recipient], eml_bytes)
    return True


def main():
    parser = argparse.ArgumentParser(description="Authorized phishing-awareness campaign builder")
    parser.add_argument("--config", required=True, help="campaign JSON (see samples/)")
    parser.add_argument("--template", default="password_expiry",
                        choices=sorted(TEMPLATES) + ["all"],
                        help="'all' runs every template against each recipient")
    parser.add_argument("--out", default="out")
    parser.add_argument("--provider", choices=["openai", "anthropic", "ollama"])
    parser.add_argument("--model")
    parser.add_argument("--base-url")
    parser.add_argument("--send", action="store_true",
                        help="actually send via configured SMTP (requires allow_send)")
    parser.add_argument("--validate-config-only", action="store_true")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        sys.exit(f"[!] {exc}")
    print(f"[+] config valid - company={config['company']} "
          f"recipients={len(config['recipients'])} attested_by={config['attested_by']}")
    if args.validate_config_only:
        # G4: even validate-only is audited to avoid silent probing
        try:
            audit_record("validate_config", actor=actor_from_env(), tool="phish-sim",
                         company=config["company"], recipients=len(config["recipients"]))
        except Exception:
            pass
        return

    if not auth.attest():
        try:
            audit_record("authorization_failed", actor=actor_from_env(), tool="phish-sim",
                         company=config["company"])
        except Exception:
            pass
        sys.exit("[!] authorization not confirmed — aborting.")
    audit_record("authorization", actor=actor_from_env(),
                 tool="phish-sim", company=config["company"],
                 recipients=len(config["recipients"]), template=args.template)

    try:
        client = ChatClient(provider=args.provider, model=args.model, base_url=args.base_url)
    except LLMError as exc:
        sys.exit(f"[!] {exc}")
    print(f"[*] generator = {client.provider}:{client.model}")

    outdir = pathlib.Path(args.out) / dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    outdir.mkdir(parents=True, exist_ok=True)

    selected_templates = (sorted(TEMPLATES) if args.template == "all"
                          else [args.template])
    landing_base = config.get("landing_base_url", "http://127.0.0.1:8000").rstrip("/")

    emails, manifest_rows, link_rows, sent_count = [], [], [], 0
    sequence = 0
    for template_key in selected_templates:
        for index, recipient in enumerate(config["recipients"], start=1):
            sequence += 1
            token = uuid.uuid4().hex[:16]
            link_url = f"{landing_base}/l/{token}"
            print(f"[*] drafting {sequence:3} [{template_key}] -> {recipient}")
            try:
                email = generate_email(client, template_key, TEMPLATES[template_key],
                                       config, recipient, index, link_url=link_url)
            except (LLMError, ValueError) as exc:
                print(f"    [warn] skipped ({exc})")
                continue
            filename = f"sim_{sequence:03d}_{template_key}.eml"
            email["file"] = filename
            (outdir / filename).write_bytes(build_eml(email, config["sender_domain"]))
            manifest_rows.append({"file": filename, "recipient": recipient,
                                  "template": template_key, "subject": email["subject"]})
            link_rows.append({"token": token, "recipient": recipient,
                              "template": template_key, "file": filename})
            if args.send:
                try:
                    sent_count += bool(maybe_send(config, build_eml(email, config["sender_domain"]),
                                                  recipient, dry_run=False))
                except (OSError, smtplib.SMTPException) as exc:
                    print(f"    [warn] send failed: {exc}")

    (outdir / "manifest.csv").write_text(campaign_manifest(manifest_rows), encoding="utf-8")
    (outdir / "campaign_links.csv").write_text(links_csv(link_rows), encoding="utf-8")
    templates_subset = {key: TEMPLATES[key] for key in selected_templates}
    (outdir / "answer_key.md").write_text(answer_key(emails, templates_subset), encoding="utf-8")

    print(f"[+] {len(emails)} drafts written -> {outdir}")
    print(f"[+] tokenized links: {len(link_rows)} (campaign_links.csv)")
    print(f"[*] next: python landing.py --links \"{outdir / 'campaign_links.csv'}\" "
          f"--company \"{config['company']}\"  then run: python metrics.py "
          f"--links \"{outdir / 'campaign_links.csv'}\" --out metrics.md")
    if args.send:
        print(f"[+] {sent_count} emails sent via SMTP")
    else:
        print("[*] dry-run mode: .eml files only (use --send plus allow_send to deliver)")


if __name__ == "__main__":
    main()
