"""Contract tests: machine reports must validate against published JSON Schemas."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]
jsonschema = pytest.importorskip("jsonschema")


@pytest.fixture(scope="module")
def validator_factory():
    def build(schema_file):
        schema = json.loads((ROOT / "schemas" / schema_file).read_text(encoding="utf-8"))
        return jsonschema.Draft202012Validator(schema)
    return build


def test_recon_bundle_schema_shape(validator_factory):
    from scoring import compute_score

    bundle = {
        "target": "lab.example",
        "generated": "2026-08-25T00:00:00",
        "changes_since_baseline": [],
        "exposure": compute_score({"sources": {}}),
        "evidence": {"target": "lab.example", "sources": {}, "warnings": []},
    }
    errors = list(validator_factory("recon-bundle.schema.json").iter_errors(bundle))
    assert not [err.message for err in errors]


def test_recon_bundle_rejects_bad_band(validator_factory):
    bundle = {"target": "lab.example", "generated": "x",
              "exposure": {"score": 10, "band": "CATASTROPHIC"},
              "evidence": {"target": "t", "sources": {}}}
    errors = list(validator_factory("recon-bundle.schema.json").iter_errors(bundle))
    assert errors, "invalid band must be rejected by schema contract"


def test_findings_bundle_matches_copilot_emission(validator_factory):
    from parsers import (dedupe_and_rank, effective_severity, parse_nmap_xml,
                         parse_nessus, parse_nuclei_jsonl, stats)

    raw = (parse_nmap_xml(ROOT / "05-pentest-report-copilot/samples/sample-nmap.xml") +
           parse_nuclei_jsonl(ROOT / "05-pentest-report-copilot/samples/sample-nuclei.jsonl") +
           parse_nessus(ROOT / "05-pentest-report-copilot/samples/sample-scan.nessus"))
    findings = dedupe_and_rank(raw)
    bundle = {
        "company": "Acme Corp",
        "assessment_type": "Test",
        "stats": stats(findings),
        "findings": [{
            **{k: f.get(k) for k in ("ref", "tool", "host", "hostname",
                                     "location", "title", "cve")},
            "severity": effective_severity(f),
            "correlated_service": None,
        } for f in findings],
    }
    errors = list(validator_factory("findings-bundle.schema.json").iter_errors(bundle))
    assert not [err.message for err in errors]
