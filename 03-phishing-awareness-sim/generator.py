"""LLM email generation with hard content-safety validation."""

import json

GENERATOR_SYSTEM = (
    "You are a security-awareness trainer's assistant. You draft SIMULATED phishing "
    "emails for an authorized employee-awareness program. Hard rules: no malware, no real "
    "credential-harvesting pages, no attachments, no instructions for wrongdoing, and the "
    "email must remain clearly harmless if inspected. It must read like a realistic "
    "corporate message and deliberately include exactly the red flags listed. "
    "Respond strictly as JSON."
)

FORBIDDEN_SNIPPETS = ("<script", "<iframe", "javascript:", "eval(", "powershell -",
                      "curl http", "wget http", "/etc/passwd", "cmd.exe")


def validate_draft(draft):
    body = str(draft.get("body", ""))
    subject = str(draft.get("subject", ""))
    if not subject or not body:
        raise ValueError("draft missing subject or body")
    if len(body) > 8000:
        raise ValueError("body too long")
    lowered = (subject + "\n" + body).lower()
    for snippet in FORBIDDEN_SNIPPETS:
        if snippet in lowered:
            raise ValueError(f"forbidden content in draft: {snippet!r}")
    return True


def generate_email(client, template_key, template, campaign, recipient, index, link_url=None):
    first_name = str(recipient).split("@")[0].split(".")[0].capitalize()
    red_flags = "\n".join(f"- {rf['flag']} ({rf['why']})" for rf in template["red_flags"])
    landing = link_url or campaign.get("landing_url",
                                        f"https://{campaign['sender_domain']}/training-landing")
    prompt = f"""Draft ONE simulated phishing email for awareness training.

COMPANY: {campaign['company']}
SENDER: security-alerts@{campaign['sender_domain']}   (deliberate lookalike domain)
RECIPIENT: {recipient}
TEMPLATE SCENARIO: {template['name']} — {template['scenario']}
LINK LABEL TO INCLUDE: "{template['link_label']}" pointing to {landing}

RED FLAGS THE DRAFT MUST CONTAIN (all of them, naturally woven in):
{red_flags}

CONSTRAINTS:
- Plain text body only (no HTML, no attachments).
- Under 220 words.
- Do not mention that this is a simulation inside the email itself.
- Replace nothing with placeholders; write final copy.

Respond as JSON: {{"subject": "...", "body": "..."}}"""
    draft = client.ask_json(prompt, GENERATOR_SYSTEM)
    try:
        validate_draft(draft)
    except ValueError:
        draft = client.ask_json(prompt + "\n\nPrevious draft violated safety rules. Regenerate.",
                                GENERATOR_SYSTEM)
        validate_draft(draft)
    return {
        "index": index,
        "recipient": recipient,
        "template": template_key,
        "first_name": first_name,
        "subject": str(draft["subject"]).strip(),
        "body": str(draft["body"]).strip(),
        "landing_url": landing,
    }


def campaign_manifest(rows):
    import csv
    import io
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["file", "recipient", "template", "subject"])
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def links_csv(rows):
    import csv
    import io
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["token", "recipient", "template", "file"])
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def answer_key(emails, templates):
    lines = ["# Trainer Answer Key", "",
             "_Red flags planted in each simulation, for the debrief session._", ""]
    for email in emails:
        template = templates[email["template"]]
        lines.append(f"## {email['file']}")
        lines.append(f"*Recipient:* `{email['recipient']}` · *Template:* {template['name']}")
        lines.append(f"*Subject:* {email['subject']}")
        lines.append("")
        for rf in template["red_flags"]:
            lines.append(f"- **{rf['flag'].title()}** — {rf['why']}")
        lines.append("")
    return "\n".join(lines)


def build_eml(email, sender_domain):
    from email.message import EmailMessage
    from email.utils import formatdate
    message = EmailMessage()
    message["From"] = f"{email['first_name']} Security <security-alerts@{sender_domain}>"
    message["To"] = email["recipient"]
    message["Subject"] = email["subject"]
    message["Date"] = formatdate(localtime=True)
    message["X-PhishSim"] = "awareness-training; do-not-report-as-incident"
    message.set_content(email["body"])
    return bytes(message)
