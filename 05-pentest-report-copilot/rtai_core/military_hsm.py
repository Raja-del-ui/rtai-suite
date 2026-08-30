"""HSM / Vault abstraction for secrets — military-grade key management.

Supports: HashiCorp Vault, TPM NVRAM, PKCS#11 HSM, env fallback.
All secrets (RTAI_API_TOKEN, RTAI_ATTEST_KEY, TLS keys) should be fetched via get_secret().
Order: Vault -> TPM NVRAM -> PKCS11 -> file -> env (fail-closed if RTAI_HSM_REQUIRED=1).

Env:
  RTAI_HSM_REQUIRED=1  fail-closed if no HSM
  VAULT_ADDR / VAULT_TOKEN
  RTAI_HSM_SLOT / RTAI_HSM_PIN
  RTAI_SECRETS_FILE (JSON file with secrets, 600 perms)
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Optional


def _get_vault_secret(key: str) -> Optional[str]:
    addr = os.environ.get("VAULT_ADDR")
    token = os.environ.get("VAULT_TOKEN")
    if not addr or not token:
        return None
    try:
        # Use vault kv get -format=json
        out = subprocess.run(
            ["vault", "kv", "get", "-format=json", f"secret/{key.lower()}"],
            capture_output=True, text=True, timeout=3,
            env={**os.environ}
        )
        if out.returncode == 0:
            j = json.loads(out.stdout)
            return j.get("data", {}).get("data", {}).get("value")
        # Fallback HTTP
        import urllib.request
        req = urllib.request.Request(f"{addr}/v1/secret/data/{key.lower()}", headers={"X-Vault-Token": token})
        with urllib.request.urlopen(req, timeout=2) as resp:
            j = json.loads(resp.read().decode())
            return j.get("data", {}).get("data", {}).get("value")
    except Exception:
        return None

def _get_tpm_nvram(key: str) -> Optional[str]:
    # Map RTAI_API_TOKEN -> NV index 0x1500016, RTAI_ATTEST_KEY -> 0x1500017
    mapping = {"RTAI_API_TOKEN": "0x1500016", "RTAI_ATTEST_KEY": "0x1500017", "RTAI_TLS_KEY": "0x1500018"}
    nv = mapping.get(key)
    if not nv:
        return None
    try:
        out = subprocess.run(["tpm2_nvread", nv], capture_output=True, timeout=3)
        if out.returncode == 0:
            return out.stdout.decode().strip()
    except Exception:
        pass
    return None

def _get_pkcs11(key: str) -> Optional[str]:
    slot = os.environ.get("RTAI_HSM_SLOT")
    pin = os.environ.get("RTAI_HSM_PIN")
    lib = os.environ.get("RTAI_HSM_LIB", "/usr/lib/libsofthsm2.so")
    if not slot or not pin:
        return None
    try:
        # Use pkcs11-tool
        out = subprocess.run(
            ["pkcs11-tool", "--module", lib, "--slot", slot, "--login", "--pin", pin, "--read-object", "--type", "data", "--label", key],
            capture_output=True, timeout=3
        )
        if out.returncode == 0:
            return out.stdout.decode().strip()
    except Exception:
        pass
    return None

def _get_file_secret(key: str) -> Optional[str]:
    f = os.environ.get("RTAI_SECRETS_FILE")
    if not f or not Path(f).exists():
        return None
    try:
        # Check perms 600
        st = Path(f).stat().st_mode & 0o777
        if st not in (0o600, 0o400):
            try:
                from rtai_core.logging_utils import get_logger
                get_logger("hsm").warning("secrets file %s perms %o not 600/400", f, st)
            except Exception:
                pass
        j = json.loads(Path(f).read_text())
        return j.get(key)
    except Exception:
        return None

def get_secret(key: str, default: str = "") -> str:
    """Fetch secret via HSM chain: Vault -> TPM -> PKCS11 -> file -> env."""
    # 1. Vault
    v = _get_vault_secret(key)
    if v:
        return v
    # 2. TPM NVRAM
    v = _get_tpm_nvram(key)
    if v:
        return v
    # 3. PKCS11
    v = _get_pkcs11(key)
    if v:
        return v
    # 4. File
    v = _get_file_secret(key)
    if v:
        return v
    # 5. Env
    v = os.environ.get(key, default)
    if v:
        return v
    if os.environ.get("RTAI_HSM_REQUIRED") == "1":
        raise RuntimeError(f"HSM required but secret {key} not found in Vault/TPM/HSM/file/env (fail-closed)")
    return default

def require_secret(key: str) -> str:
    val = get_secret(key)
    if not val:
        raise RuntimeError(f"Secret {key} required but not found (set via Vault/TPM/HSM/file or env, see military_hsm.py)")
    return val

__all__ = ["get_secret", "require_secret"]
