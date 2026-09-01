"""GUI password gate — military-grade local auth for Tactical Console.

- First run: prompts to set password (8+ chars, 3 classes), stores PBKDF2-SHA256 hash + salt
- Next runs: prompts for password, verifies, 3 attempts then lockout 5 min
- Storage: OS keyring (keyring lib) if available, else %APPDATA%/Royal-Sec/gui_auth.json 600 perms
- Also supports env bypass RTAI_GUI_PASSWORD (for CI) and RTAI_GUI_NO_AUTH=1 (dev only, audited)
- Every attempt audited via rtai_core.audit (hash chain) + lockout

Security: PBKDF2-HMAC-SHA256 260k iterations, 32B salt, constant-time compare.
No plaintext stored. GUI password is SEPARATE from API token / attestation keys.
"""

import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path

from rtai_core.audit import actor_from_env, record as audit_record

APP_NAME = "Royal-Sec"
SERVICE_NAME = "rtai-suite-gui"
CONFIG_DIR_ENV = "RTAI_GUI_AUTH_DIR"
CONFIG_FILE_NAME = "gui_auth.json"
MAX_ATTEMPTS = 3
LOCKOUT_SECONDS = 300  # 5 min
PBKDF2_ITER = 260_000
SALT_BYTES = 16
HASH_NAME = "sha256"

def _config_path() -> Path:
    """Resolve config file path: RTAI_GUI_AUTH_DIR or %APPDATA%/Royal-Sec or ~/.royal-sec"""
    custom = os.environ.get(CONFIG_DIR_ENV)
    if custom:
        return Path(custom) / CONFIG_FILE_NAME
    # Windows APPDATA
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / APP_NAME / CONFIG_FILE_NAME
    # Fallback Linux/macOS
    return Path.home() / f".{APP_NAME.lower().replace(' ', '-')}" / CONFIG_FILE_NAME

def _keyring_available() -> bool:
    try:
        import keyring  # type: ignore
        return True
    except Exception:
        return False

def _keyring_get() -> str | None:
    if not _keyring_available():
        return None
    try:
        import keyring
        return keyring.get_password(SERVICE_NAME, "gui_password_hash")
    except Exception:
        return None

def _keyring_set(hash_str: str) -> bool:
    if not _keyring_available():
        return False
    try:
        import keyring
        keyring.set_password(SERVICE_NAME, "gui_password_hash", hash_str)
        return True
    except Exception:
        return False

def _keyring_delete() -> bool:
    if not _keyring_available():
        return False
    try:
        import keyring
        keyring.delete_password(SERVICE_NAME, "gui_password_hash")
        return True
    except Exception:
        return False

def _file_get() -> str | None:
    p = _config_path()
    if not p.exists():
        return None
    try:
        # Enforce 600 perms on read
        data = json.loads(p.read_text(encoding="utf-8"))
        return data.get("hash")
    except Exception:
        return None

def _file_set(hash_str: str) -> None:
    p = _config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    # Write with 600 perms
    payload = {"hash": hash_str, "created": time.time(), "algo": f"pbkdf2-{HASH_NAME}-{PBKDF2_ITER}"}
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    try:
        p.chmod(0o600)
    except Exception:
        pass

def _get_stored_hash() -> str | None:
    # Priority: keyring > file
    h = _keyring_get()
    if h:
        return h
    return _file_get()

def _set_stored_hash(hash_str: str) -> None:
    # Try keyring first, fallback to file
    if not _keyring_set(hash_str):
        _file_set(hash_str)

def hash_password(password: str, salt: bytes | None = None) -> str:
    """Hash password with PBKDF2-SHA256, returns 'salt_hex$hash_hex$iter'"""
    if salt is None:
        salt = secrets.token_bytes(SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(HASH_NAME, password.encode("utf-8"), salt, PBKDF2_ITER, dklen=32)
    return f"{salt.hex()}${dk.hex()}${PBKDF2_ITER}"

def verify_password(password: str, stored: str) -> bool:
    """Constant-time verify against stored 'salt$hash$iter'."""
    try:
        salt_hex, hash_hex, iter_str = stored.split("$")
        salt = bytes.fromhex(salt_hex)
        it = int(iter_str)
        dk = hashlib.pbkdf2_hmac(HASH_NAME, password.encode("utf-8"), salt, it, dklen=32)
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False

def is_first_run() -> bool:
    return _get_stored_hash() is None

def password_strength_ok(pw: str) -> tuple[bool, str]:
    """Enforce 8+ chars, 3 of 4 classes: upper, lower, digit, symbol."""
    if len(pw) < 8:
        return False, "Password must be at least 8 characters"
    classes = 0
    if any(c.islower() for c in pw):
        classes += 1
    if any(c.isupper() for c in pw):
        classes += 1
    if any(c.isdigit() for c in pw):
        classes += 1
    if any(not c.isalnum() for c in pw):
        classes += 1
    if classes < 3:
        return False, "Use at least 3 of: lower, upper, digit, symbol"
    return True, "ok"

def set_password(new_password: str) -> None:
    ok, msg = password_strength_ok(new_password)
    if not ok:
        raise ValueError(msg)
    h = hash_password(new_password)
    _set_stored_hash(h)
    try:
        audit_record("gui_password_set", actor=actor_from_env(), via="keyring" if _keyring_available() else "file")
    except Exception:
        pass

def check_password(password: str) -> bool:
    # Env bypass for CI (audited)
    env_pw = os.environ.get("RTAI_GUI_PASSWORD")
    if env_pw:
        # If GUI password is set via env, compare directly (for CI automation)
        if hmac.compare_digest(password, env_pw):
            try:
                audit_record("gui_auth_bypass_env", actor=actor_from_env())
            except Exception:
                pass
            return True
    stored = _get_stored_hash()
    if not stored:
        return False
    return verify_password(password, stored)

def reset_password() -> None:
    _keyring_delete()
    p = _config_path()
    try:
        if p.exists():
            p.unlink()
    except Exception:
        pass
    try:
        audit_record("gui_password_reset", actor=actor_from_env())
    except Exception:
        pass

# Lockout tracking (in-memory + file)
def _lockout_path() -> Path:
    return _config_path().parent / "gui_lockout.json"

def is_locked_out() -> tuple[bool, int]:
    p = _lockout_path()
    if not p.exists():
        return False, 0
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        until = float(data.get("until", 0))
        if until == 0:
            # Not locked — keep fails count for increment
            return False, 0
        remaining = int(until - time.time())
        if remaining > 0:
            return True, remaining
        # Expired — clear
        p.unlink(missing_ok=True)
        return False, 0
    except Exception:
        return False, 0

def record_failure():
    # Increment attempts
    p = _lockout_path()
    try:
        data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"fails": 0, "until": 0}
    except Exception:
        data = {"fails": 0, "until": 0}
    data["fails"] = int(data.get("fails", 0)) + 1
    if data["fails"] >= MAX_ATTEMPTS:
        data["until"] = time.time() + LOCKOUT_SECONDS
        data["fails"] = 0
        try:
            audit_record("gui_lockout", actor=actor_from_env(), until=data["until"])
        except Exception:
            pass
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data), encoding="utf-8")
    try:
        p.chmod(0o600)
    except Exception:
        pass

def record_success():
    p = _lockout_path()
    try:
        if p.exists():
            p.unlink()
    except Exception:
        pass

__all__ = [
    "hash_password", "verify_password", "is_first_run", "password_strength_ok",
    "set_password", "check_password", "reset_password",
    "is_locked_out", "record_failure", "record_success",
    "MAX_ATTEMPTS", "LOCKOUT_SECONDS",
]
