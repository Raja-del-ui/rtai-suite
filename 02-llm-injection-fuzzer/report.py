"""Markdown + SARIF report generation for the injection fuzzing campaign."""

import json

HARDENING_SYSTEM = (
    "You are an LLM-application security architect. Given fuzzing results against a chat "
    "endpoint, write concrete defensive recommendations. Be specific about system-prompt "
    "design, input/output filtering, and architectural controls. GitHub-flavoured Markdown."
)


def to_sarif(params, results):
    rule_index = {}
    rules = []
    for r in results:
        rule_id = str(r.get("id"))
        if rule_id not in rule_index:
            rule_index[rule_id] = len(rules)
            rules.append({
                "id": rule_id,
                "name": {"text": f"{rule_id}: {r.get('expect', 'injection attempt')}"},
                "shortDescription": {"text": f"Prompt injection via {r.get('category')}"},
                "defaultConfiguration": {"level": "error"},
            })
    level_map = {"compromised": "error", "suspicious": "warning", "safe": None}
    sarif_results = []
    for r in results:
        level = level_map.get(r["verdict"])
        if not level:
            continue
        sarif_results.append({
            "ruleId": str(r.get("id")),
            "level": level,
            "message": {
                "text": (f"[{r['verdict']}] {str(r.get('text'))[:120]} -> "
                         f"{(r.get('response') or '')[:160]}")
            },
            "properties": {
                "category": r.get("category"),
                "score": r.get("score"),
                "turns": r.get("turns", 1),
            },
        })
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {
                "name": "llm-injection-fuzzer",
                "informationUri": "https://ollama.com",
                "rules": rules,
            }},
            "invocations": [{"executionSuccessful": True,
                             "properties": {"target": params["target_url"],
                                            "model": params["model"]}}],
            "results": sarif_results,
        }],
    }


def to_junit(params, results):
    """JUnit XML for CI dashboards: compromised=failure, suspicious=skipped."""
    import xml.etree.ElementTree as ET

    compromised = sum(1 for r in results if r["verdict"] == "compromised")
    suspicious = sum(1 for r in results if r["verdict"] == "suspicious")
    suite = ET.Element("testsuite", {
        "name": f"llm-injection-fuzzer::{params['model']}",
        "tests": str(len(results)),
        "failures": str(compromised),
        "skipped": str(suspicious),
        "errors": "0",
    })
    properties = ET.SubElement(suite, "properties")
    for key, value in (("target", params["target_url"]),
                       ("system_prompt_len", str(len(params.get("system_prompt") or "")))):
        prop = ET.SubElement(properties, "property", {"name": key, "value": value})

    for record_row in results:
        case = ET.SubElement(suite, "testcase", {
            "classname": record_row["category"],
            "name": f"{record_row['id']}:{record_row.get('expect', '')}"[:120],
            "time": "0",
        })
        if record_row["verdict"] == "compromised":
            failure = ET.SubElement(case, "failure", {
                "message": f"defense bypassed ({record_row['category']})"})
            evidence = next((h["evidence"] for h in record_row["regex_hits"]),
                            record_row.get("evidence", ""))
            failure.text = f"payload={record_row['text'][:200]}\nevidence={evidence}"
        elif record_row["verdict"] == "suspicious":
            skipped = ET.SubElement(case, "skipped", {"message": "suspicious response"})
            skipped.text = record_row.get("reasoning", "")[:200]
    return ET.tostring(suite, encoding="unicode")


def render(params, stats, results):
    lines = [
        f"# Prompt-Injection Fuzzing Report — {params['target_url']}",
        "",
        f"*Model under test:* `{params['model']}` · *Defense prompt:* "
        f"`{(params['system_prompt'] or '(none)')[:80]}...`",
        "",
        "## Summary",
        "",
        f"| Total | Compromised | Suspicious | Safe | Resilience |",
        f"|---|---|---|---|---|",
        f"| {stats['total']} | {stats['compromised']} | {stats['suspicious']} | "
        f"{stats['safe']} | {stats['resilience_pct']}% |",
        "",
        "### By category",
        "",
        "| Category | Attempts | Compromised |",
        "|---|---|---|",
    ]
    for category, bucket in sorted(stats["by_category"].items()):
        lines.append(f"| {category} | {bucket['total']} | {bucket['compromised']} |")

    lines += ["", "## Results Detail", "",
              "| ID | Gen | Category | Verdict | Score | Evidence |",
              "|---|---|---|---|---|---|"]
    for r in sorted(results, key=lambda x: -(x["score"] or 0)):
        evidence = next((h["evidence"] for h in r["regex_hits"]), r.get("evidence", ""))
        lines.append(f"| {r['id']} | {r['generation']} | {r['category']} | **{r['verdict']}** | "
                     f"{r['score'] if r['score'] is not None else 'n/a'} | "
                     f"{(evidence or '').replace('|', '/')} |")

    notable = [r for r in results if r["verdict"] == "compromised"][:3]
    for r in notable:
        lines += ["", f"### {r['id']} ({r['category']}) — {r['expect']}",
                  "", f"**Payload:**", "```", r["text"][:400], "```",
                  f"**Response:**", "```", (r["response"] or "")[:500], "```"]

    return "\n".join(lines) + "\n"


def add_recommendations(report_text, client, stats, results):
    compact = [
        {"id": r["id"], "category": r["category"], "verdict": r["verdict"],
         "score": r["score"], "technique_hint": r["expect"]}
        for r in results
    ]
    prompt = f"""Fuzzing summary: {stats['compromised']}/{stats['total']} attempts compromised
the endpoint. Categories: {json_compact(compact)}.

Write a `## Defensive Recommendations` section (Markdown) with:
1. System-prompt hardening tactics relevant to the successful categories.
2. Input/output filter ideas (with example regex or classifier hooks).
3. Architectural controls that defeat this attack class entirely.
Keep it under 350 words."""
    section = client.chat(prompt, HARDENING_SYSTEM)
    return report_text.rstrip() + "\n\n" + section + "\n"


def json_compact(items):
    import json as _json
    return _json.dumps(items)[:3000]
