"""Deterministic exposure scoring and baseline diffing (no LLM involved)."""

WEIGHTS = {
    "spf_missing": 25,
    "spf_softfail_only": 10,
    "dmarc_missing": 20,
    "caa_missing": 5,
    "cert_expired": 20,
    "cert_expiring_soon": 10,
    "cert_unvalidated_chain": 8,
    "http_alive": 12,
    "missing_security_header": 4,
    "anonymous_service": 15,
}

SEVERITY_BANDS = [(25, "LOW"), (50, "MEDIUM"), (75, "HIGH"), (101, "CRITICAL")]


def _band(score):
    for threshold, label in SEVERITY_BANDS:
        if score < threshold:
            return label
    return "CRITICAL"


def compute_score(findings):
    src = findings.get("sources", {})

    def data(name):
        entry = src.get(name) or {}
        return entry.get("data") or {}

    drivers = []
    score = 0

    email = data("email_security")
    if email:
        if not email.get("spf"):
            score += WEIGHTS["spf_missing"]
            drivers.append(("spf_missing", WEIGHTS["spf_missing"], "no SPF record: domain trivially spoofable"))
        elif not email.get("spf_all_strict"):
            score += WEIGHTS["spf_softfail_only"]
            drivers.append(("spf_softfail_only", WEIGHTS["spf_softfail_only"], "SPF ends ~all: spoofing partially feasible"))
        if not email.get("dmarc"):
            score += WEIGHTS["dmarc_missing"]
            drivers.append(("dmarc_missing", WEIGHTS["dmarc_missing"], "no DMARC policy"))
        if not email.get("caa"):
            score += WEIGHTS["caa_missing"]
            drivers.append(("caa_missing", WEIGHTS["caa_missing"], "no CAA record: any CA may issue certificates"))

    cert = data("tls_certificate")
    if cert:
        if cert.get("expired"):
            score += WEIGHTS["cert_expired"]
            drivers.append(("cert_expired", WEIGHTS["cert_expired"], "TLS certificate expired"))
        elif cert.get("expiring_soon"):
            score += WEIGHTS["cert_expiring_soon"]
            drivers.append(("cert_expiring_soon", WEIGHTS["cert_expiring_soon"],
                            f"certificate expires in {cert['days_remaining']} days"))
        if not cert.get("validated_chain"):
            score += WEIGHTS["cert_unvalidated_chain"]
            drivers.append(("cert_unvalidated_chain", WEIGHTS["cert_unvalidated_chain"], "chain failed public validation"))

    http = data("http_fingerprint")
    if isinstance(http, dict) and http.get("status") == 200:
        score += WEIGHTS["http_alive"]
        drivers.append(("http_alive", WEIGHTS["http_alive"], f"plaintext HTTP serves content ({len(http.get('missing_security_headers', []))} headers missing on https side)" ))

    https = data("https_fingerprint")
    missing = len(https.get("missing_security_headers") or []) if isinstance(https, dict) else 0
    if missing:
        score += missing * WEIGHTS["missing_security_header"]
        drivers.append(("missing_security_header", missing * WEIGHTS["missing_security_header"],
                        f"{missing} security headers absent"))

    return {"score": min(score, 100), "band": _band(score), "drivers": drivers}


def diff_findings(baseline, current):
    changes = []

    def subs(snapshot):
        entry = (snapshot.get("sources") or {}).get("live_subdomains") or {}
        return set((entry.get("data") or {}).get("resolving") or [])

    old_subs, new_subs = subs(baseline), subs(current)
    added = sorted(new_subs - old_subs)
    removed = sorted(old_subs - new_subs)

    def txt_records(snapshot):
        entry = (snapshot.get("sources") or {}).get("dns") or {}
        records = entry.get("data") or {}
        return set(records.get("TXT") or []), set(records.get("A") or [])

    old_txt, old_a = txt_records(baseline)
    new_txt, new_a = txt_records(current)

    def cert_days(snapshot):
        entry = (snapshot.get("sources") or {}).get("tls_certificate") or {}
        return (entry.get("data") or {}).get("days_remaining")

    delta_days = None
    before, after = cert_days(baseline), cert_days(current)
    if before is not None and after is not None:
        delta_days = after - before

    if added:
        changes.append(f"New resolving subdomains: {', '.join(added[:15])}")
    if removed:
        changes.append(f"Subdomains no longer resolve: {', '.join(removed[:15])}")
    txt_added = sorted(new_txt - old_txt)
    if txt_added:
        changes.append(f"New TXT records: {'; '.join(t[:80] for t in txt_added[:5])}")
    a_added = sorted(new_a - old_a)
    if a_added:
        changes.append(f"New A records: {', '.join(a_added[:8])}")
    if delta_days not in (None, 0):
        changes.append(f"Certificate validity shifted by {delta_days:+d} days")
    if not changes:
        changes.append("No material differences detected")
    return changes
