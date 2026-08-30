"""LLM-driven analysis of reconnaissance results into a prioritized assessment."""

import json

SYSTEM_PROMPT = (
    "You are a senior offensive-security consultant reviewing PASSIVE reconnaissance "
    "data collected during an authorized engagement. Analyse only what the supplied JSON "
    "shows; never fabricate findings that are not supported by it. Be concrete and cite "
    "the exact evidence (record, header, hostname) for every claim. Respond in "
    "GitHub-flavoured Markdown."
)


def build_prompt(findings, exposure=None, changes=None):
    compact = json.dumps(findings, indent=1)
    if len(compact) > 14000:
        compact = compact[:14000] + "\n...TRUNCATED..."
    extras = ""
    if exposure:
        drivers = "; ".join(f"{d[2]} (+{d[1]})" for d in exposure["drivers"]) or "none"
        extras += (f"\nDETERMINISTIC EXPOSURE SCORE: {exposure['score']}/100 "
                   f"({exposure['band']}). Drivers: {drivers}\n"
                   "Agree or disagree with this rule-based score in your summary.\n")
    if changes:
        extras += ("\nCHANGES SINCE LAST BASELINE SCAN:\n- " +
                   "\n- ".join(changes) + "\n")
    return f"""Below is passive reconnaissance data collected for {findings['target']}.
{extras}
DATA:
{compact}

Produce an attack-surface assessment using EXACTLY these Markdown sections:

## Executive Summary
Three sentences maximum.

## Attack Surface Overview
What is externally visible, grouped by infrastructure / email / web / certificates.

## Priority Findings
Numbered list. For each: **observation**, evidence from the data, why it matters to an
attacker, and the single highest-value remediation. Order by attacker value.

## Email Security Assessment
SPF/DMARC/CAA/MX posture and spoofing feasibility against this domain.

## Recommended Next Steps
Active enumeration steps appropriate ONLY for an authorized engagement, ordered
cheapest-first. Flag each step as `SAFE` or `INTRUSIVE`.

End with one line: `Overall exposure: <LOW|MEDIUM|HIGH|CRITICAL>`."""


def analyze(findings, client, exposure=None, changes=None):
    return client.chat(build_prompt(findings, exposure, changes), SYSTEM_PROMPT)
