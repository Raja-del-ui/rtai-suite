"""Passive reconnaissance collectors: RDAP, DNS, CT logs, email security, HTTP posture,
TLS certificates and Wayback Machine history."""

import ipaddress
import json
import re
import socket
import ssl
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

try:
    import dns.exception
    import dns.resolver
    _DNS_OK = True
except ImportError:
    _DNS_OK = False


def _require_dns():
    if not _DNS_OK:
        raise RuntimeError('optional dependency missing - install with: '
                           'pip install dnspython>=2.6 (see requirements.txt)')

from rtai_core.exceptions import ValidationError
from rtai_core.registry import Registry

USER_AGENT = "Mozilla/5.0 (compatible; AIReconAgent/1.0; authorized-research)"
HTTP_TIMEOUT = 15

SECURITY_HEADERS = [
    "content-security-policy",
    "strict-transport-security",
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
    "permissions-policy",
]

_DOMAIN_RE = re.compile(
    r"(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}"
)


def valid_domain(domain):
    return bool(_DOMAIN_RE.fullmatch(str(domain).strip().lower()))


def fetch_json(url, timeout=HTTP_TIMEOUT):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode(errors="replace"))


def resolve_ips(domain):
    infos = socket.getaddrinfo(domain.strip().lower(), None)
    results = []
    seen = set()
    for info in infos:
        ip = info[4][0]
        if ip in seen:
            continue
        seen.add(ip)
        parsed = ipaddress.ip_address(ip)
        results.append({"ip": ip, "version": parsed.version, "private": parsed.is_private})
    return results


def rdap_lookup(domain):
    data = fetch_json(f"https://rdap.org/domain/{domain}")
    events = {e.get("eventAction"): e.get("eventDate") for e in data.get("events", [])}
    registrar = None
    nameservers = []
    for entity in data.get("entities", []):
        if "registrar" in (entity.get("roles") or []):
            for vcard in entity.get("vcardArray", [None, []])[1]:
                if vcard[0] == "fn":
                    registrar = vcard[3]
    nameservers = [ns.get("ldhName") for ns in data.get("nameservers", []) if ns.get("ldhName")]
    return {
        "status": data.get("status"),
        "registrar": registrar,
        "registered": events.get("registration"),
        "expires": events.get("expiration"),
        "updated": events.get("last changed"),
        "nameservers": nameservers,
    }


def dns_records(domain):
    _require_dns()
    resolver = dns.resolver.Resolver()
    resolver.lifetime = 10
    records = {}
    for rtype in ["A", "AAAA", "MX", "NS", "TXT", "SOA"]:
        try:
            answers = resolver.resolve(domain, rtype)
            values = sorted(str(r).rstrip(".") for r in answers)
            if rtype == "TXT":
                values = sorted(" ".join(part.decode() if isinstance(part, bytes) else str(part)
                                        for part in r.strings) for r in answers)
            records[rtype] = values
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers,
                dns.exception.Timeout, OSError):
            records[rtype] = []
    www = {}
    try:
        www["CNAME"] = sorted(str(r).rstrip(".") for r in resolver.resolve(f"www.{domain}", "CNAME"))
    except Exception:
        www["CNAME"] = []
    records["WWW_CNAME"] = www["CNAME"]
    return records


def email_security(dns_data, domain):
    _require_dns()
    spf = [t for t in dns_data.get("TXT", []) if t.lower().startswith("v=spf1")]
    dmarc = []
    caa = []
    resolver = dns.resolver.Resolver()
    resolver.lifetime = 10
    try:
        dmarc = sorted(str(r).rstrip(".") for r in resolver.resolve(f"_dmarc.{domain}", "TXT"))
    except Exception:
        pass
    try:
        caa = sorted(str(r) for r in resolver.resolve(domain, "CAA"))
    except Exception:
        pass
    return {
        "mx_present": bool(dns_data.get("MX")),
        "spf": spf or None,
        "dmarc": dmarc or None,
        "caa": caa or None,
        "spf_all_pass": bool(spf and "~all" in spf[0]),
        "spf_all_strict": bool(spf and ("-all" in spf[0])),
    }


def ct_subdomains(domain):
    entries = fetch_json(f"https://crt.sh/?q=%.{domain}&output=json", timeout=45)
    names = set()
    for entry in entries:
        for name in str(entry.get("name_value", "")).splitlines():
            name = name.strip().lower().lstrip("*.")
            if name.endswith(domain) and name != domain:
                names.add(name)
    return sorted(names)[:200]


def verify_subdomains(subdomains, concurrency=16):
    def resolves(name):
        try:
            socket.gethostbyname(name)
            return name
        except OSError:
            return None

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        checked = list(pool.map(resolves, subdomains))
    return sorted(name for name in checked if name)


def tls_certificate(domain, port=443):
    def grab(verify):
        context = (ssl.create_default_context() if verify
                   else ssl._create_unverified_context())
        with socket.create_connection((domain, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as tls_sock:
                return tls_sock.getpeercert()

    try:
        cert = grab(verify=True)
        validated = True
    except ssl.SSLError:
        cert = grab(verify=False)
        validated = False
    issuer = dict(x[0] for x in cert.get("issuer", ())).get("organizationName")
    subject = dict(x[0] for x in cert.get("subject", ())).get("commonName")
    sans = sorted(v for k, v in cert.get("subjectAltName", ()) if k == "DNS")
    days_left = int((ssl.cert_time_to_seconds(cert["notAfter"]) - time.time()) // 86400)
    return {
        "validated_chain": validated,
        "issuer": issuer,
        "subject_cn": subject,
        "not_after": cert["notAfter"],
        "days_remaining": days_left,
        "expired": days_left < 0,
        "expiring_soon": 0 <= days_left < 30,
        "sans_count": len(sans),
        "sans_sample": sans[:25],
    }


def wayback_urls(domain, limit=60):
    api = ("https://web.archive.org/cdx/search/cdx"
           f"?url={domain}/*&output=json&collapse=urlkey&limit=400&fl=original,timestamp")
    rows = fetch_json(api, timeout=45)[1:]
    seen = set()
    paths = []
    for original, _timestamp in rows:
        path = str(original).split(str(domain), 1)[-1].split("?")[0]
        if path and path not in seen and not path.startswith("/web/"):
            seen.add(path)
            paths.append({"path": path[:120], "archived": _timestamp})
        if len(paths) >= limit:
            break
    return {"count": len(paths), "paths": paths}


def tech_hints(fingerprint_data):
    hints = set()
    for key in ("https_fingerprint", "http_fingerprint"):
        data = fingerprint_data.get(key, {}).get("data") or {}
        banner = " ".join(filter(None, [data.get("server"), data.get("x_powered_by"),
                                        data.get("generator")]))
        lowered = banner.lower()
        for stack in ["nginx", "apache", "iis", "cloudflare", "php", "asp.net",
                      "express", "next.js", "wordpress", "drupal", "joomla"]:
            if stack in lowered:
                hints.add(stack)
    return sorted(hints)


def http_fingerprint(domain, scheme="https"):
    req = urllib.request.Request(f"{scheme}://{domain}", headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
    })
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            body = resp.read(65536).decode(errors="replace")
            final_url = resp.geturl()
            status = resp.status
            headers = {k.lower(): v for k, v in resp.headers.items()}
    except urllib.error.HTTPError as exc:
        headers = {k.lower(): v for k, v in exc.headers.items()} if exc.headers else {}
        body, final_url, status = "", f"{scheme}://{domain}", exc.code
    title_match = re.search(r"<title[^>]*>(.*?)</title>", body, re.DOTALL | re.IGNORECASE)
    generator_match = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', body,
                                re.IGNORECASE)
    return {
        "scheme": scheme,
        "status": status,
        "final_url": final_url,
        "server": headers.get("server"),
        "x_powered_by": headers.get("x-powered-by"),
        "title": re.sub(r"\s+", " ", title_match.group(1)).strip()[:120] if title_match else None,
        "generator": generator_match.group(1) if generator_match else None,
        "missing_security_headers": [h for h in SECURITY_HEADERS if h not in headers],
    }


def collect(target, include_http=False):
    findings = {"target": target, "sources": {}, "warnings": []}
    results = {}

    def run(name, fn, *args):
        try:
            results[name] = {"ok": True, "data": fn(*args)}
        except Exception as exc:
            results[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            findings["warnings"].append(f"{name} failed: {exc}")

    jobs = [
        ("dns", dns_records, (target,), 10, True),
        ("rdap", rdap_lookup, (target,), 20, True),
        ("tls_certificate", tls_certificate, (target,), 30, True),
        ("certificate_transparency", ct_subdomains, (target,), 40, True),
        ("wayback_history", wayback_urls, (target,), 50, True),
        ("ip_resolution", resolve_ips, (target,), 60, True),
        ("https_fingerprint", http_fingerprint, (target, "https"), 70, False),
        ("http_fingerprint", http_fingerprint, (target, "http"), 71, False),
    ]
    jobs = [job for job in jobs if job[4] or include_http]

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(run, name, fn, *args)
                   for name, fn, args, _prio, _active in sorted(jobs, key=lambda j: j[3])]
        for future in futures:
            future.result()

    findings["sources"] = dict(sorted(results.items(),
                                      key=lambda kv: COLLECTOR_ORDER.index(kv[0])
                                      if kv[0] in COLLECTOR_ORDER else 99))
    if findings["sources"].get("dns", {}).get("ok"):
        run("email_security", email_security, findings["sources"]["dns"]["data"],
            target)
        findings["sources"]["email_security"] = results["email_security"]
    if include_http:
        hints = tech_hints({k: v for k, v in findings["sources"].items()
                            if k.endswith("fingerprint")})
        if hints:
            findings["sources"]["tech_hints"] = {"ok": True, "data": hints}
    subs = findings["sources"].get("certificate_transparency", {})
    if subs.get("ok") and subs["data"]:
        live = verify_subdomains(subs["data"])
        findings["sources"]["live_subdomains"] = {"ok": True, "data": {
            "resolving_count": len(live),
            "resolving": live[:100],
        }}
    return findings


COLLECTORS = Registry("collectors")
COLLECTORS.register("dns", dns_records, passive=True, priority=10)
COLLECTORS.register("rdap", rdap_lookup, passive=True, priority=20)
COLLECTORS.register("tls_certificate", tls_certificate, passive=True, priority=30)
COLLECTORS.register("certificate_transparency", ct_subdomains,
                    passive=True, priority=40)
COLLECTORS.register("wayback_history", wayback_urls, passive=True, priority=50)
COLLECTORS.register("ip_resolution", resolve_ips, passive=True, priority=60)
COLLECTORS.register("https_fingerprint", http_fingerprint, active=True, priority=70)
COLLECTORS.register("http_fingerprint", http_fingerprint, active=True, priority=71)

COLLECTOR_ORDER = ["dns", "email_security", "rdap", "tls_certificate",
                   "certificate_transparency", "wayback_history", "ip_resolution",
                   "https_fingerprint", "http_fingerprint", "tech_hints",
                   "live_subdomains"]
