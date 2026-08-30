"""v3.3 feature tests: audit chain wiring, JUnit export, HTML outputs."""

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_fuzzer_junit_export(tmp_path):
    from payloads import builtin_payloads
    from report import to_junit

    results = []
    for payload in builtin_payloads(include_chains=False)[:3]:
        results.append({"id": payload["id"], "category": payload["category"],
                        "text": payload["text"], "expect": payload["expect"],
                        "verdict": "compromised", "score": 10,
                        "regex_hits": [{"evidence": "PWNED"}],
                        "evidence": "", "reasoning": ""})
    results.append({"id": "X-99", "category": "x", "text": "t", "expect": "e",
                    "verdict": "safe", "score": 0, "regex_hits": [],
                    "evidence": "", "reasoning": ""})
    xml = to_junit({"model": "m", "target_url": "http://x"}, results)
    root = ET.fromstring(xml)
    assert root.tag == "testsuite"
    assert root.get("tests") == "4" and root.get("failures") == "3"
    assert len(root.findall("testcase/failure")) == 3


def test_p5_html_report_rendered(tmp_path):
    copilot_dir = ROOT / "05-pentest-report-copilot"
    out = tmp_path / "report.html"
    result = subprocess.run(
        [sys.executable, "copilot.py",
         "--nmap", "samples/sample-nmap.xml",
         "--nuclei", "samples/sample-nuclei.jsonl",
         "--company", "Acme", "--no-llm",
         "--format", "html", "--out", str(out)],
        cwd=str(copilot_dir), capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr[-600:]
    html = out.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html and "severity-badge" not in html  # class=badge
    assert 'class="badge' in html and "Detailed Findings" in html


def test_p3_metrics_html_dashboard(tmp_path):
    sim = ROOT / "03-phishing-awareness-sim"
    links = tmp_path / "links.csv"
    links.write_text(
        "token,recipient,template,file\n"
        "tok1,a@x,password_expiry,s1.eml\n"
        "tok2,b@x,password_expiry,s2.eml\n"
        "tok3,c@x,invoice_attachment,s3.eml\n", encoding="utf-8")
    clicks = tmp_path / "clicks.jsonl"
    clicks.write_text(
        json.dumps({"event": "click", "token": "tok1", "ts": "2026-08-25T10:00:00"}) + "\n" +
        json.dumps({"event": "click", "token": "tok3", "ts": "2026-08-25T10:05:00"}) + "\n",
        encoding="utf-8")

    html_out = tmp_path / "metrics.html"
    result = subprocess.run(
        [sys.executable, "metrics.py", "--links", str(links),
         "--clicks", str(clicks), "--out", str(tmp_path / "m.md"),
         "--html", str(html_out)],
        cwd=str(sim), capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr[-500:]
    html = html_out.read_text(encoding="utf-8")
    assert '<div class="kpi"' in html and 'class="bar"' in html
    assert "Click rate" in html and "invoice_attachment" in html


def test_audit_wired_into_phish_gate(tmp_path, monkeypatch):
    import os

    from rtai_core.audit import AuditChain
    log_file = tmp_path / "audit.log"
    monkeypatch.setenv("RTAI_AUDIT_LOG", str(log_file))
    monkeypatch.setattr("rtai_core.audit._DEFAULT", None)

    campaign_py = ROOT / "03-phishing-awareness-sim" / "campaign.py"
    env = {**os.environ, "RTAI_AUDIT_LOG": str(log_file),
           "PHISHSIM_ATTESTED": "1"}
    result = subprocess.run(
        [sys.executable, "-c",
         "\n".join([
             "import sys, json",
             "sys.argv=['campaign.py','--config','samples/campaign.example.json',"
             "'--validate-config-only']",
             "import auth",
             "from rtai_core.audit import actor_from_env, record as audit_record",
             "cfg = json.load(open('samples/campaign.example.json', encoding='utf-8'))",
             "auth.validate_campaign(cfg)",
             "audit_record('authorization', actor=actor_from_env(), tool='phish-sim')",
         ])],
        cwd=str(campaign_py.parent), capture_output=True, text=True,
        timeout=60, env=env)
    assert result.returncode == 0, result.stderr[-400:]
    ok, broken = AuditChain(log_file).verify()
    assert ok and broken is None
    assert AuditChain(log_file).read()[0]["tool"] == "phish-sim"
