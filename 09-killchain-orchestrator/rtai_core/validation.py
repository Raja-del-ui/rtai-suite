"""Semantic validation primitives shared across projects."""

import ipaddress
import re
import socket

_DOMAIN_RE = re.compile(
    r"(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def valid_domain(value) -> bool:
    return bool(_DOMAIN_RE.fullmatch(str(value).strip().lower()))


def normalize_domain(value) -> str:
    domain = str(value).strip().lower()
    if not valid_domain(domain):
        raise ValueError(f"invalid domain: {value!r}")
    return domain


def valid_email(value) -> bool:
    return bool(_EMAIL_RE.match(str(value)))


# Documentation / reserved test nets that are technically marked private in some
# Python versions but must NOT be considered lab (RFC 5737, RFC 3849, RFC 3927 partial).
_RESERVED_LAB_DENY = [
    ipaddress.ip_network("192.0.2.0/24"),    # TEST-NET-1
    ipaddress.ip_network("198.51.100.0/24"), # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),  # TEST-NET-3
    ipaddress.ip_network("192.88.99.0/24"),  # 6to4 relay (deprecated)
    ipaddress.ip_network("192.0.0.0/24"),    # IANA special
    ipaddress.ip_network("2001:db8::/32"),   # documentation prefix v6
]


def _is_lab_ip(parsed: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    # Explicit deny for documentation nets
    for net in _RESERVED_LAB_DENY:
        try:
            if parsed in net:
                return False
        except TypeError:
            continue  # v4 vs v6 mismatch
    # Lab = loopback OR RFC1918 private OR link-local. is_reserved deliberately excluded.
    # Note: some Python builds mark TEST-NET as is_private True — denied above.
    if parsed.is_loopback or parsed.is_link_local:
        return True
    # Private but not global, not multicast, not reserved (already denied), not unspecified
    if parsed.is_private and not parsed.is_multicast and not parsed.is_unspecified:
        # Further exclude is_global which indicates public routable
        if not getattr(parsed, "is_global", False):
            return True
        # Even if is_global False but is_private True for CGNAT etc, we still allow
        # only RFC1918 and ULA. Tighten to RFC1918/ULA nets:
        try:
            if isinstance(parsed, ipaddress.IPv4Address):
                return parsed in ipaddress.ip_network("10.0.0.0/8") or \
                       parsed in ipaddress.ip_network("172.16.0.0/12") or \
                       parsed in ipaddress.ip_network("192.168.0.0/16") or \
                       parsed in ipaddress.ip_network("100.64.0.0/10")  # CGNAT, allow as private lab
            else:
                return parsed in ipaddress.ip_network("fc00::/7") or \
                       parsed in ipaddress.ip_network("fe80::/10")
        except Exception:
            return True
    return False


def is_lab_address(host: str) -> tuple[bool, list[str]]:
    infos = socket.getaddrinfo(host, None)
    verdicts: dict[str, bool] = {}
    for info in infos:
        raw = str(info[4][0])
        parsed = ipaddress.ip_address(raw.split("%")[0])
        verdicts[raw] = _is_lab_ip(parsed)
    return all(verdicts.values()), sorted(verdicts)


def assert_lab_address(host: str) -> None:
    allowed, ips = is_lab_address(host)
    if not allowed:
        offenders = ", ".join(ips)
        raise ValueError(
            f"refusing non-lab target(s): {offenders} - loopback/private only")
