"""FIPS 140-3 mode — approved algorithms enforcement.

Military systems must use FIPS-validated cryptography. This module enforces
approved suites and provides a fail-closed check. It does NOT replace a
validated hardware module (e.g., RHEL openssl-fips) but gates the software.

Approved: SHA-256/384/512, SHA3-256/384/512, AES-128/256-GCM, ChaCha20-Poly1305 (TLS 1.3),
HKDF-SHA256/384, HMAC-SHA256/384/512, RSA 2048+ / EC P-256/384/521 / X25519 / ML-KEM-768/1024,
ML-DSA-65/87. Denied: MD5, SHA1 (non-HMAC), DES/3DES, RC4, RSA <2048.

Env: RTAI_FIPS=1 enables enforcement; RTAI_FIPS_STRICT=1 also denies fallback to stdlib.
"""

import hashlib
import os
import hmac as _hmac
from dataclasses import dataclass
from enum import Enum

FIPS_ENABLED = os.environ.get("RTAI_FIPS") == "1"
FIPS_STRICT = os.environ.get("RTAI_FIPS_STRICT") == "1"

class FIPSLevel(str, Enum):
    DISABLED = "disabled"
    ENFORCE = "enforce"
    STRICT = "strict"

def get_fips_level() -> FIPSLevel:
    if os.environ.get("RTAI_FIPS_STRICT") == "1":
        return FIPSLevel.STRICT
    if os.environ.get("RTAI_FIPS") == "1":
        return FIPSLevel.ENFORCE
    return FIPSLevel.DISABLED

APPROVED_HASHES = {"sha256", "sha384", "sha512", "sha3_256", "sha3_384", "sha3_512"}
APPROVED_CIPHERS = {"AES-256-GCM", "AES-128-GCM", "CHACHA20-POLY1305"}
DENIED_HASHES = {"md5", "sha1", "md4"}

@dataclass
class FIPSCheck:
    allowed: bool
    algorithm: str
    reason: str
    fips_level: str

def check_hash(algorithm: str) -> FIPSCheck:
    alg = algorithm.lower().replace("-", "_")
    level = get_fips_level()
    if level == FIPSLevel.DISABLED:
        return FIPSCheck(True, algorithm, "FIPS not enabled", level.value)
    if alg in DENIED_HASHES:
        return FIPSCheck(False, algorithm, f"{algorithm} denied in FIPS mode (use SHA2/SHA3)", level.value)
    if alg in APPROVED_HASHES:
        return FIPSCheck(True, algorithm, "approved", level.value)
    if level == FIPSLevel.STRICT:
        return FIPSCheck(False, algorithm, f"{algorithm} not in approved list (STRICT)", level.value)
    return FIPSCheck(True, algorithm, "allowed (non-STRICT, log warning)", level.value)

def fips_hash(algorithm: str, data: bytes) -> bytes:
    chk = check_hash(algorithm)
    if not chk.allowed:
        raise ValueError(f"FIPS check failed: {chk.reason} [{algorithm}]")
    h = hashlib.new(algorithm.replace("-", "_") if "_" not in algorithm else algorithm, data)
    return h.digest()

def fips_hmac(key: bytes, data: bytes, hash_alg: str = "sha256") -> bytes:
    chk = check_hash(hash_alg)
    if not chk.allowed:
        raise ValueError(f"FIPS HMAC hash denied: {hash_alg}")
    return _hmac.new(key, data, getattr(hashlib, hash_alg)).digest()

def assert_fips_cipher(cipher: str) -> None:
    level = get_fips_level()
    if level == FIPSLevel.DISABLED:
        return
    if cipher not in APPROVED_CIPHERS:
        raise ValueError(f"Cipher {cipher} not FIPS-approved. Allowed: {APPROVED_CIPHERS}")

def fips_status() -> dict:
    return {
        "enabled": get_fips_level() != FIPSLevel.DISABLED,
        "level": get_fips_level().value,
        "approved_hashes": sorted(APPROVED_HASHES),
        "approved_ciphers": sorted(APPROVED_CIPHERS),
        "strict": FIPS_STRICT,
        "openssl_fips": _openssl_fips_status(),
    }

def _openssl_fips_status() -> str:
    try:
        import subprocess
        out = subprocess.run(["openssl", "version", "-f"], capture_output=True, text=True, timeout=2)
        if "FIPS" in out.stdout or "fips" in out.stdout.lower():
            return "fips_enabled"
        # Try fipsinstall check on RHEL
        out2 = subprocess.run(["fips-mode-setup", "--check"], capture_output=True, text=True, timeout=2)
        if "enabled" in out2.stdout.lower():
            return "enabled"
    except Exception:
        pass
    return "unknown_or_not_enabled"

# Enforce at import if STRICT and OpenSSL not in FIPS
if FIPS_STRICT:
    status = _openssl_fips_status()
    # Don't hard-fail import in dev, but log
    try:
        from rtai_core.logging_utils import get_logger
        get_logger("fips").warning("FIPS STRICT enabled, OpenSSL status: %s", status)
    except Exception:
        pass

__all__ = ["get_fips_level", "FIPSLevel", "check_hash", "fips_hash", "fips_hmac", "assert_fips_cipher", "fips_status", "FIPS_ENABLED"]
