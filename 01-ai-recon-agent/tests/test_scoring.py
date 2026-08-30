import sources
import scoring


def test_valid_domain_accepts_and_rejects():
    assert sources.valid_domain("example.com")
    assert not sources.valid_domain("bad")
    assert not sources.valid_domain("-x.com")


def test_score_flags_missing_email_controls():
    findings = {
        "target": "t",
        "sources": {
            "email_security": {"ok": True, "data": {"spf": None, "dmarc": None, "caa": None}},
        },
    }
    result = scoring.compute_score(findings)
    drivers = {key for key, _pts, _note in result["drivers"]}
    assert {"spf_missing", "dmarc_missing", "caa_missing"} <= drivers
    assert result["score"] >= 45


def test_score_band_ordering():
    clean = {"sources": {}}
    dirty = {"sources": {"http_fingerprint": {"ok": True, "data": {"status": 200}}}}
    assert scoring.compute_score(clean)["score"] < scoring.compute_score(dirty)["score"]


def test_diff_detects_new_subdomain_and_txt():
    baseline = {"sources": {
        "live_subdomains": {"data": {"resolving": ["a.x.com"]}},
        "dns": {"data": {"TXT": ["v=spf1 -all"], "A": ["1.2.3.4"]}},
    }}
    current = {"sources": {
        "live_subdomains": {"data": {"resolving": ["a.x.com", "b.x.com"]}},
        "dns": {"data": {"TXT": ["v=spf1 -all", "v=DMARC1; p=reject"], "A": ["1.2.3.4"]}},
    }}
    changes = "\n".join(scoring.diff_findings(baseline, current))
    assert "b.x.com" in changes
    assert "DMARC1" in changes


def test_diff_no_change_message():
    snapshot = {"sources": {"live_subdomains": {"data": {"resolving": []}},
                            "dns": {"data": {"TXT": [], "A": []}}}}
    assert scoring.diff_findings(snapshot, snapshot) == ["No material differences detected"]
