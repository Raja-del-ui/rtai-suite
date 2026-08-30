"""Authorization gate and campaign configuration validation."""

import hashlib
import hmac
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

from rtai_core.config import BaseConfig

ATTEST_PHRASE = "I AM AUTHORIZED"
ENV_BYPASS = "PHISHSIM_ATTESTED"


def _env_bypass_ok() -> bool:
    val = os.environ.get(ENV_BYPASS) or ""
    if not val:
        return False
    key = os.environ.get("RTAI_ATTEST_KEY")
    if key:
        expected = hmac.new(key.encode(), b"attested", hashlib.sha256).hexdigest()[:16]
        return hmac.compare_digest(val, expected)
    if hmac.compare_digest(val, "1"):
        print(f"[*] authorization attested via {ENV_BYPASS}=1 (legacy — set RTAI_ATTEST_KEY for HMAC)")
        return True
    return False
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_RECIPIENTS = 50


@dataclass
class CampaignConfig(BaseConfig):
    company: str = ""
    sender_domain: str = ""
    landing_base_url: str = "http://127.0.0.1:8000"
    attested_by: str = ""
    recipients: List[str] = field(default_factory=list)
    allow_send: bool = False
    smtp: Optional[dict] = None


def attest():
    if _env_bypass_ok():
        return True
    # If env var set but HMAC failed, treat as explicit failure
    if os.environ.get(ENV_BYPASS):
        return False
    try:
        answer = input(f"Type exactly '{ATTEST_PHRASE}' to certify you are approved to send "
                       f"simulations to the listed recipients: ").strip()
    except EOFError:
        answer = ""
    if not hmac.compare_digest(answer, ATTEST_PHRASE):
        return False
    return True


def validate_campaign(config):
    errors = []
    try:
        CampaignConfig.from_layers(overrides=dict(config))
    except Exception as exc:
        errors.append(f"schema check failed: {exc}")

    for key in ("company", "attested_by", "recipients"):
        if not config.get(key):
            errors.append(f"missing required key '{key}'")
    recipients = config.get("recipients") or []
    if len(recipients) > MAX_RECIPIENTS:
        errors.append(f"{len(recipients)} recipients exceeds cap of {MAX_RECIPIENTS}")
    bad = [r for r in recipients if not EMAIL_RE.match(str(r))]
    if bad:
        errors.append(f"invalid recipient emails: {bad[:5]}")
    sender_domain = str(config.get("sender_domain", ""))
    if not re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", sender_domain.lower()):
        errors.append("'sender_domain' must be a lookalike domain you control "
                      "(e.g. acme-secure.example)")
    if config.get("smtp") and not config.get("allow_send"):
        errors.append("smtp block present but 'allow_send' is not true - sending stays disabled")
    if errors:
        raise ValueError("campaign config invalid:\n  - " + "\n  - ".join(errors))
    return True
