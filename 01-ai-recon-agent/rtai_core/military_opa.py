"""Military-grade OPA/Rego policy engine for zero-trust authorization."""

import json
import os
import subprocess
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import opa_wasm
    OPA_WASM_AVAILABLE = True
except ImportError:
    OPA_WASM_AVAILABLE = False

try:
    import rego
    REGO_AVAILABLE = True
except ImportError:
    REGO_AVAILABLE = False


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    rules_matched: list[str]
    obligations: list[str] = field(default_factory=list)


@dataclass
class PolicyRule:
    name: str
    package: str
    rule: str
    description: str
    severity: str = "medium"  # low, medium, high, critical


class OPAPolicyEngine:
    """OPA/Rego policy engine for zero-trust authorization."""

    BUILTIN_POLICIES = {
        "zero_trust": """
package rtai.authz

default allow = false

allow {
    input.method == "GET"
    input.path == "/health"
}

allow {
    input.method == "GET"
    input.path == "/version"
}

allow {
    input.method == "GET"
    input.path == "/metrics"
}

allow {
    input.auth.valid == true
    input.auth.scopes[_] == "recon:read"
    input.method == "GET"
    input.path == "/v1/recon"
}

allow {
    input.auth.valid == true
    input.auth.scopes[_] == "recon:write"
    input.method == "POST"
    input.path == "/v1/recon/async"
}

allow {
    input.auth.valid == true
    input.auth.scopes[_] == "jobs:read"
    input.method == "GET"
    startswith(input.path, "/v1/jobs")
}

allow {
    input.auth.valid == true
    input.auth.scopes[_] == "fuzz:execute"
    input.method == "POST"
    input.path == "/v1/payloads/validate"
}

# Deny by default
deny {
    not allow
}

# Obligations for audit
obligations["audit"] := true {
    allow
    input.method in {"POST", "PUT", "DELETE"}
}
""",

        "data_protection": """
package rtai.data

default allow = false

# Classify data sensitivity
classification = "public" {
    not input.data.classification
}

classification = input.data.classification {
    input.data.classification
}

# Allow public data freely
allow {
    classification == "public"
}

# CUI requires auth + encryption
allow {
    classification == "CUI"
    input.auth.valid == true
    input.encryption == "AES-256-GCM"
}

# Secret requires auth + mTLS + audit
allow {
    classification == "SECRET"
    input.auth.valid == true
    input.mtls == true
    input.audit == true
}

# Top Secret requires all controls + TPM attestation
allow {
    classification == "TOP_SECRET"
    input.auth.valid == true
    input.mtls == true
    input.audit == true
    input.tpm_attestation == true
}

deny {
    not allow
}
""",

        "network_security": """
package rtai.network

default allow = false

# Allow local loopback
allow {
    input.source.ip == "127.0.0.1"
}

allow {
    input.source.ip == "::1"
}

# Allow RFC1918 with mTLS
allow {
    is_private_ip(input.source.ip)
    input.mtls == true
}

# Block known bad
deny {
    is_tor_exit(input.source.ip)
}

deny {
    input.rate > 1000  # requests per minute
}

is_private_ip(ip) {
    startswith(ip, "10.")
    startswith(ip, "172.16.")
    startswith(ip, "192.168.")
}

is_tor_exit(ip) {
    ip in data.tor_exits
}
""",

        "compliance": """
package rtai.compliance

# CMMC Level 2 controls
cmmc_ac_1_1 {
    input.auth.mfa == true
}

cmmc_ac_1_2 {
    input.auth.session_timeout <= 15
}

cmmc_au_2_1 {
    input.audit.events[_].timestamp
    input.audit.events[_].actor
    input.audit.events[_].action
}

cmmc_ia_2_1 {
    input.auth.mfa == true
    input.auth.password_policy.min_length >= 15
}

cmmc_sc_8_1 {
    input.transport.encryption == "TLS1.3"
    input.transport.cipher in ["AES-256-GCM", "CHACHA20-POLY1305"]
}

# NIST 800-53 mappings
nist_ac_2 {
    input.account.management.automated == true
}

nist_au_6 {
    input.audit.review.frequency == "weekly"
}

nist_sc_8 {
    input.transport.encryption != "none"
}

nist_sc_13 {
    input.crypto.fips_validated == true
}
"""
    }

    def __init__(self, policy_dir: Path = None, use_wasm: bool = True):
        self.policies: dict[str, str] = {}
        self.compiled: dict[str, Any] = {}
        self.policy_dir = policy_dir or Path("policies")
        self.use_wasm = use_wasm and OPA_WASM_AVAILABLE

        # Load built-in policies
        for name, rego_code in self.BUILTIN_POLICIES.items():
            self.load_policy(name, rego_code)

        # Load custom policies from directory
        if self.policy_dir.exists():
            for rego_file in self.policy_dir.glob("*.rego"):
                self.load_policy(rego_file.stem, rego_file.read_text())

    def load_policy(self, name: str, rego_code: str):
        """Load and compile a Rego policy."""
        self.policies[name] = rego_code
        if REGO_AVAILABLE:
            try:
                self.compiled[name] = rego.compile(rego_code)
            except Exception as e:
                print(f"[!] Failed to compile policy {name}: {e}")

    def evaluate(self, policy_name: str, input_data: dict) -> PolicyDecision:
        """Evaluate input against a policy."""
        if policy_name not in self.compiled:
            return PolicyDecision(False, f"Policy {policy_name} not found or not compiled", [])

        try:
            query = f"data.{policy_name}"
            results = self.compiled[policy_name].evaluate(query, input_data)
            result = results[0] if results else {}

            allowed = result.get("allow", False)
            rules = [k for k, v in result.items() if k.startswith("allow") and v]
            obligations = result.get("obligations", {})

            return PolicyDecision(
                allowed=allowed,
                reason="Policy evaluated",
                rules_matched=rules,
                obligations=list(obligations.keys()) if isinstance(obligations, dict) else []
            )
        except Exception as e:
            return PolicyDecision(False, f"Policy evaluation error: {e}", [])

    def evaluate_all(self, input_data: dict) -> dict[str, PolicyDecision]:
        """Evaluate input against all loaded policies."""
        return {name: self.evaluate(name, input_data) for name in self.compiled}

    def add_policy_file(self, path: Path):
        """Load policy from .rego file."""
        self.load_policy(path.stem, path.read_text())

    def export_bundle(self, output: Path):
        """Export policies as OPA bundle."""
        bundle = {"manifest": {}, "policies": {}}
        for name, code in self.policies.items():
            bundle["policies"][f"{name}.rego"] = code
        output.write_text(json.dumps(bundle, indent=2))


# Default policy engine instance
DEFAULT_ENGINE = OPAPolicyEngine()


def evaluate_policy(policy_name: str, input_data: dict) -> PolicyDecision:
    """Convenience function to evaluate against default engine."""
    return DEFAULT_ENGINE.evaluate(policy_name, input_data)


def evaluate_all_policies(input_data: dict) -> dict[str, PolicyDecision]:
    """Evaluate against all loaded policies."""
    return DEFAULT_ENGINE.evaluate_all(input_data)


# Convenience functions for common checks
def authorize_request(input_data: dict) -> PolicyDecision:
    """Check zero-trust authorization."""
    return evaluate_policy("zero_trust", input_data)


def check_data_access(input_data: dict) -> PolicyDecision:
    """Check data protection policy."""
    return evaluate_policy("data_protection", input_data)


def check_network_access(input_data: dict) -> PolicyDecision:
    """Check network security policy."""
    return evaluate_policy("network_security", input_data)


def check_compliance(input_data: dict) -> dict[str, bool]:
    """Check compliance controls."""
    result = evaluate_policy("compliance", {})
    return {k: v for k, v in result.items() if k.startswith("cmmc_") or k.startswith("nist_")}


# Export for external use
__all__ = [
    "OPAPolicyEngine",
    "PolicyDecision",
    "PolicyRule",
    "DEFAULT_ENGINE",
    "evaluate_policy",
    "evaluate_all_policies",
    "authorize_request",
    "check_data_access",
    "check_network_access",
    "check_compliance",
]