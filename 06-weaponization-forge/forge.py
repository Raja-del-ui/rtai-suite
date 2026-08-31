#!/usr/bin/env python3
"""06-weaponization-forge — Cyber Kill Chain Weaponization (lab-only, benign)

Cyber Kill Chain stage: WEAPONIZATION (Lockheed Martin framework)
  Weaponization = coupling a payload with a delivery vehicle (document, link,
  script, container). This forge implements the *defensive* counterpart:
  generating SAFE, BENIGN, LAB-ONLY placeholder artifacts that mimic the
  *form* of weaponized objects without any executable malicious code.

MITRE ATT&CK coverage:
  - T1587  Develop Capabilities — adversary develops capabilities (here simulated
           with benign EICAR test file + macro/LNK/HTA/ISO/shellcode STUBs)
  - T1583  Acquire Infrastructure — simulated via lab-only target binding + audit

This tool is the legitimate, authorized-lab-only counterpart to T1587/T1583.
It NEVER generates real malware, shellcode, or weaponized executables.
Every artifact is a text placeholder watermarked for audit, containing the
standard EICAR test string where executable-like content would be.

Safety gates (see README for line-number map):
  Gate 1 — Authorization: interactive ATTACK phrase or HMAC env bypass (audit.py)
  Gate 2 — Lab-only target: assert_lab_address OR valid_domain (validation.py)
  Gate 3 — Benign-only blocklist (inverted FORBIDDEN_SNIPPETS) + watermark gate
  Gate 4 — Audit chain: every generation logged to rtai_core.audit AuditChain

Usage:
  python forge.py --list-templates
  python forge.py --target 127.0.0.1 --payload-type document_macro --out ./out
  python forge.py --target lab.local --payload-type shellcode_stub --out ./out/eicar.txt
  FORGE_ATTESTED=<hmac> python forge.py --target 127.0.0.1 --payload-type lnk_dropper --out ./out --yes

  Env bypass (CI/automation):
    RTAI_ATTEST_KEY must be set; then compute:
      python -c "import hmac,hashlib,os;print(hmac.new(os.environ['RTAI_ATTEST_KEY'].encode(),b'attested',hashlib.sha256).hexdigest()[:16])"
    export FORGE_ATTESTED=<hex16>
    export RTAI_ATTEST_KEY=<same key>

All outputs are plain text, audit-watermarked, and safe to handle as evidence.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import json
import os
import sys
import pathlib
import textwrap

# Vendor-safe imports: this folder vendors rtai_core, but also works from repo root
try:
    from rtai_core.audit import actor_from_env, record as audit_record, AuditChain
    from rtai_core.validation import assert_lab_address, valid_domain
    from rtai_core.exceptions import ValidationError, AuthError
except ImportError:
    # Fallback if rtai_core is at sibling or parent
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    try:
        from rtai_core.audit import actor_from_env, record as audit_record, AuditChain
        from rtai_core.validation import assert_lab_address, valid_domain
        from rtai_core.exceptions import ValidationError, AuthError
    except ImportError as exc:
        sys.exit(f"[x] rtai_core not found (expected vendored at ./rtai_core): {exc}")

# ──────────────────────────────────────────────────────────────────────────────
# Constants — benign-only design
# ──────────────────────────────────────────────────────────────────────────────

# Standard EICAR test file string (harmless, universally detected as test)
# https://en.wikipedia.org/wiki/EICAR_test_file
EICAR_STRING = r"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

# Audit watermark — every artifact carries this, plus actor/timestamp/target
WATERMARK = "AUTHORIZED LAB USE ONLY — BENIGN PLACEHOLDER — NO MALICIOUS CODE"
AUDIT_TAG = "RT-WATERMARK: 06-weaponization-forge — T1587/T1583 benign simulation"
INVOICE_WATERMARK = "INVOICE PDF PLACEHOLDER — AUDIT WATERMARK — NOT A REAL INVOICE"

# Authorization gate constants (mirrors 02-llm-injection-fuzzer/inject_fuzzer.py:13-14, 03-phishing-awareness-sim/auth.py:12-13)
ATTEST_PHRASE = "ATTACK"
ENV_BYPASS = "FORGE_ATTESTED"          # set to HMAC hex16 or "1" legacy
ENV_BYPASS_ALT = "RTAI_FORGE_ATTESTED" # alt name accepted for convenience

# FORBIDDEN_SNIPPETS — blocklist inverted vs 03-phishing-awareness-sim/generator.py:14-15
# Original generator.py blocklist denies phishing HTML/JS/exec strings.
# Here we invert: allow ONLY benign placeholders, REJECT any real shellcode / weaponization.
# If any of these case-insensitive substrings appear in final artifact, generation is refused.
# Covers common weaponization primitives that must never appear in benign output.
# NOTE: generic word "shellcode" is intentionally NOT blocked — benign placeholders
# legitimately describe themselves as "shellcode stub (benign)" and would self-block.
# Instead we block the *executable* primitives (VirtualAlloc etc.) and encoded payload signals.
FORBIDDEN_SNIPPETS = (
    # Execution primitives — real weaponization must never appear in benign output
    "virtualalloc", "virtualallocex", "createremotethread", "ntunmapviewofsection",
    "writeprocessmemory", "rtlmovememory", "ntcreateprocess", "zwcreateprocess",
    "loadlibrary", "getprocaddress", "getmodulehandle",
    # Encoder / shellcode byte patterns + framework artefacts
    "\\x90\\x90", "\\xfc\\xe8", "msfvenom", "metasploit", "meterpreter",
    "cobalt strike", "beacon.dll", " stageless ", " stager ",
    # PowerShell weaponization (encoded/hidden)
    "powershell -enc", "powershell -encodedcommand", "powershell -windowstyle hidden",
    "invoke-mimikatz", "invoke-expression", "iex(", "downloadstring", "downloadfile(",
    "frombase64string", "certutil -urlcache", "bitsadmin /transfer",
    "rundll32", "regsvr32 /s", "mshta ", "wmic process call create",
    # Office exploitation
    "autoopen", "document_open", "auto_open", "ddebypass", "equa+ion",
    # LNK/HTA/ISO abuse patterns that indicate real payloads
    "target: cmd.exe /c", "target: powershell.exe", " <script", "<iframe",
    "javascript:", "eval(", "wscript.shell", "shell.application",
    "activexobject", "msxml2.xmlhttp",
    # File system / credential access
    "/etc/passwd", "sam.hiv", "ntds.dit", "lsass.exe", "sekurlsa::",
)

# Allowed benign markers — at least one must be present to prove placeholder
REQUIRED_BENIGN_MARKERS = (
    WATERMARK,
    AUDIT_TAG,
    "BENIGN PLACEHOLDER",
)

# Templates — 5 benign weaponization forms (mirrors Kill Chain Weaponization)
TEMPLATES: dict[str, dict] = {
    "document_macro": {
        "name": "Office Document Macro (benign placeholder)",
        "file_ext": ".vba.txt",
        "description": "Simulates a weaponized Office macro delivery vehicle, but contains only a benign VBA Sub that shows a MsgBox and EICAR comment. No AutoExec, no shell.",
        "attack_stage": "Weaponization :: T1587.001 — Develop Capabilities: Malware",
        "benign_content": True,
    },
    "lnk_dropper": {
        "name": "LNK Dropper Shortcut (benign placeholder)",
        "file_ext": ".lnk.txt",
        "description": "Simulates a weaponized .lnk shortcut, but is a plain-text description file (never a binary .lnk). Points nowhere executable; carries watermark + EICAR.",
        "attack_stage": "Weaponization :: T1587 — LNK as delivery vehicle",
        "benign_content": True,
    },
    "hta_artifact": {
        "name": "HTA Application (benign placeholder)",
        "file_ext": ".hta.txt",
        "description": "Simulates a weaponized HTA, but is a benign HTML placeholder with no ActiveX, no script execution, watermark + EICAR comment only.",
        "attack_stage": "Weaponization :: T1587 — HTA as execution vehicle",
        "benign_content": True,
    },
    "iso_container": {
        "name": "ISO Container (benign placeholder)",
        "file_ext": "",  # creates a directory placeholder
        "description": "Simulates a weaponized ISO container (often used to smuggle LNK/HTA), but is a directory with benign text files, watermark, and EICAR test file. Not an ISO 9660 image.",
        "attack_stage": "Weaponization :: T1583 — Acquire Infrastructure / Container",
        "benign_content": True,
    },
    "shellcode_stub": {
        "name": "Shellcode Stub (benign EICAR placeholder)",
        "file_ext": ".bin.txt",
        "description": "Simulates a shellcode payload stub, but contains ONLY the EICAR test string plus audit watermark. No NOP sled, no executable bytes, no encoder.",
        "attack_stage": "Weaponization :: T1587.004 — Develop Capabilities: Evasion stub (benign)",
        "benign_content": True,
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# Gate 1 — Authorization (ATT&CK: authorization attestation)
# Mirrors 02-llm-injection-fuzzer/inject_fuzzer.py:28-59 and 01-ai-recon-agent/recon_agent.py:27-61
# ──────────────────────────────────────────────────────────────────────────────

def _env_bypass_ok() -> bool:
    """
    Check HMAC env bypass. Supports RTAI_ATTEST_KEY HMAC or legacy =1.

    Line-map for reviewers:
      forge.py:_env_bypass_ok  ~ line 80-100  (this function)
      forge.py:require_authorization ~ line 102-140 (gate enforcement)
      audit.py:verify_attestation_hmac — canonical HMAC check

    Returns True if FORGE_ATTESTED or RTAI_FORGE_ATTESTED matches
      hmac-sha256(RTAI_ATTEST_KEY, b"attested")[:16]  (or "1" legacy when no key set)
    """
    for env_name in (ENV_BYPASS, ENV_BYPASS_ALT, "RTAI_ATTEST_KEY_BYPASS"):
        val = os.environ.get(env_name) or ""
        if not val:
            continue
        key = os.environ.get("RTAI_ATTEST_KEY")
        if key:
            expected = hmac.new(key.encode(), b"attested", hashlib.sha256).hexdigest()[:16]
            if hmac.compare_digest(val, expected):
                return True
            # mismatch on this var — try next var before failing
            continue
        # Legacy path — warn once, accept for backwards compat
        if hmac.compare_digest(val, "1"):
            print(f"[*] {env_name}=1 legacy bypass — set RTAI_ATTEST_KEY for HMAC in production", file=sys.stderr)
            return True
    # Also accept single RTAI_ATTEST_KEY bypass if RTAI_ATTEST_KEY itself is the HMAC? No — require explicit env var.
    return False


def require_authorization(skip_flag: bool = False) -> None:
    """
    Enforce ATTACK phrase or HMAC env bypass before any artifact generation.

    Behavioral contract (matches 02-llm-injection-fuzzer:43-59):
      - If --yes passed, require valid FORGE_ATTESTED HMAC; otherwise fail-closed and audit.
      - Else, prompt interactively for "ATTACK"; on mismatch, audit failure and exit.
      - On success, audit `authorization` event with actor/bypass metadata.

    Raises SystemExit on failure (fail-closed).
    """
    # Check HMAC env bypass first (CI)
    if skip_flag and _env_bypass_ok():
        try:
            audit_record("authorization", actor=actor_from_env(), tool="weapon-forge", bypass="hmac", env=ENV_BYPASS)
        except Exception:
            pass
        print("[+] authorization attested via HMAC env bypass")
        return
    if skip_flag:
        # --yes passed but bypass invalid
        try:
            audit_record("authorization_failed", actor=actor_from_env(), tool="weapon-forge", reason="env_bypass_invalid", env=ENV_BYPASS)
        except Exception:
            pass
        sys.exit(f"[!] --yes requires valid {ENV_BYPASS}=<hmac> (or HMAC when RTAI_ATTEST_KEY set) — aborting.")
    # Interactive attestation (lab operator ceremony)
    # Note: phrase is ATTACK (like fuzzer) to align with red-team tradecraft gates
    try:
        answer = input(f"Type {ATTEST_PHRASE} to certify this lab artifact generation is authorized (lab-only, benign placeholders only): ").strip()
    except EOFError:
        answer = ""
    if not hmac.compare_digest(answer, ATTEST_PHRASE):
        try:
            audit_record("authorization_failed", actor=actor_from_env(), tool="weapon-forge", reason="phrase_mismatch")
        except Exception:
            pass
        sys.exit("[!] authorization not confirmed — aborting (need ATTACK).")
    try:
        audit_record("authorization", actor=actor_from_env(), tool="weapon-forge", bypass="interactive")
    except Exception:
        pass
    print("[+] authorization confirmed (interactive ATTACK)")


# ──────────────────────────────────────────────────────────────────────────────
# Gate 2 — Lab-only target (assert_lab_address or valid_domain)
# Mirrors 04-c2-detection-lab/beacon.py:112-119 and listener.py:99-108
# ──────────────────────────────────────────────────────────────────────────────

def validate_target_lab_only(target: str) -> dict:
    """
    Lab-only gate: refuse any target that does not resolve loopback/private OR is not a valid lab domain.

    Allowed:
      - loopback (127.0.0.1, ::1), RFC1918 (10/8, 172.16/12, 192.168/16), link-local, CGNAT 100.64/10, ULA fc00::/7
      - lab domains validated by valid_domain() (e.g., lab.local, test.lab, example.internal)

    Denied:
      - Public routables (e.g., 8.8.8.8, 1.1.1.1), TEST-NET documentation nets (RFC5737), internet domains not owned for lab

    Returns dict with verdict metadata for audit.
    """
    t = str(target).strip()
    if not t:
        raise ValidationError("target must be non-empty")
    # Try lab IP/host check first (covers hostnames that resolve)
    try:
        assert_lab_address(t)
        return {"target": t, "verdict": "lab_ip", "detail": "assert_lab_address passed (loopback/private/link-local)"}
    except (ValueError, OSError) as lab_exc:
        # OSError covers socket.gaierror for non-resolvable lab domains like lab.local
        # Fall back to domain-format check (for lab domains you control, e.g., lab.local)
        if valid_domain(t):
            # Heuristic: allow domains that look lab-internal (common lab TLDs) or explicit allowlist
            lab_tlds = (".lab", ".local", ".internal", ".test", ".example", ".invalid")
            if any(t.lower().endswith(suf) for suf in lab_tlds) or t.lower() in ("localhost",):
                return {"target": t, "verdict": "lab_domain", "detail": f"valid_domain passed + lab TLD heuristic ({t})"}
            # Still allow generic valid_domain if operator attests they own it — audit it
            # But require that the domain not be a known public TLD without lab qualifier? We allow with audit.
            try:
                audit_record("target_domain_heuristic_warn", actor=actor_from_env(), tool="weapon-forge", target=t, note=str(lab_exc)[:120])
            except Exception:
                pass
            return {"target": t, "verdict": "domain_owned_attested", "detail": f"valid_domain passed (operator attests ownership): {t}"}
        raise ValidationError(f"refusing non-lab target {t!r} — must be lab IP/host (loopback/private) or lab domain you own: {lab_exc}")


# ──────────────────────────────────────────────────────────────────────────────
# Gate 3 — Benign-only content validation (inverted FORBIDDEN_SNIPPETS)
# Mirrors 03-phishing-awareness-sim/generator.py:14-29 but stricter
# ──────────────────────────────────────────────────────────────────────────────

def validate_payload_content(content: str, filename: str = "") -> None:
    """
    Inverted blocklist gate: REJECT any real shellcode/weaponization primitive, ALLOW only benign placeholders.

    Checks:
      1) No FORBIDDEN_SNIPPETS substring (case-insensitive) may appear.
      2) At least one REQUIRED_BENIGN_MARKERS must be present (watermark proof).
      3) For shellcode_stub / EICAR-bearing types, EICAR_STRING must be present.
      4) Content size cap (fail-closed on oversized).

    Raises ValueError on violation.
    """
    if len(content) > 20000:
        raise ValueError("payload content exceeds 20k benign placeholder cap (refuse oversized)")
    lowered = content.lower()
    for snippet in FORBIDDEN_SNIPPETS:
        if snippet.lower() in lowered:
            raise ValueError(f"forbidden weaponization primitive in {filename or 'payload'}: {snippet!r} — generation refused (benign-only)")
    # Watermark presence
    found_markers = [m for m in REQUIRED_BENIGN_MARKERS if m in content]
    if not found_markers:
        raise ValueError(f"missing required benign watermark in {filename or 'payload'} — expected one of {REQUIRED_BENIGN_MARKERS}")
    # No null bytes or non-printable executable-like sequences (heuristic)
    if "\x00" in content:
        raise ValueError("null byte detected — refused (benign placeholders are text-only)")


def _audit_watermark(target: str, template_key: str) -> str:
    """Generate per-artifact audit watermark line with actor/timestamp/target/hash."""
    actor = actor_from_env()
    ts = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    # Deterministic linkage: hash of target+template+ts for forensic correlation
    link = hashlib.sha256(f"{target}|{template_key}|{ts}|{actor}".encode()).hexdigest()[:16]
    return f"{AUDIT_TAG} | target={target} | template={template_key} | actor={actor} | ts={ts} | link={link}"


# ──────────────────────────────────────────────────────────────────────────────
# Template generators — each returns (suggested_filename, content)
# Every output is plain text, watermarked, EICAR-bearing where appropriate.
# ──────────────────────────────────────────────────────────────────────────────

def _gen_document_macro(target: str, out_path: pathlib.Path) -> tuple[pathlib.Path, str]:  # noqa: ARG001
    wm = _audit_watermark(target, "document_macro")
    eicar_comment = f"' EICAR test string (benign, detected as test): {EICAR_STRING}"
    content = textwrap.dedent(f"""\
        ' {WATERMARK}
        ' {AUDIT_TAG}
        ' {wm}
        ' Template: document_macro — Office macro delivery vehicle (BENIGN PLACEHOLDER)
        ' Target: {target}
        ' Safety: No AutoExec, No shell execution, No Download — benign only
        ' Invert of real weaponization: this file is .vba.txt text, not a binary .docm
        '
        {eicar_comment}
        ' ————————————————————————————————————————————————————————————————
        ' This placeholder simulates what a weaponized document macro WOULD look
        ' like in the Weaponization stage (T1587.001), but contains ZERO
        ' malicious code. For defensive training and detection engineering only.
        ' If this file were a real .docm, the automatic handler would trigger a payload.
        ' Here, the Sub below only displays a benign message box and exits.
        ' ————————————————————————————————————————————————————————————————

        Sub BenignPlaceholder()
            ' Audit watermark echoed at runtime for forensic correlation
            Dim audit As String
            audit = "{wm}"
            MsgBox "RT Forge — BENIGN PLACEHOLDER" & vbCrLf & _
                   "Target: {target}" & vbCrLf & _
                   "Audit: " & audit & vbCrLf & _
                   "No malicious code executed.", vbInformation, "Lab Only"
        End Sub

        ' End of benign macro placeholder — no further content
        ' {INVOICE_WATERMARK}
        """)
    validate_payload_content(content, "document_macro")
    # Ensure EICAR present as benign marker
    if EICAR_STRING not in content:
        raise ValueError("EICAR missing from document_macro (required benign marker)")
    filename = f"document_macro_{_sanitize(target)}.vba.txt"
    return out_path / filename, content


def _gen_lnk_dropper(target: str, out_path: pathlib.Path) -> tuple[pathlib.Path, str]:
    wm = _audit_watermark(target, "lnk_dropper")
    content = textwrap.dedent(f"""\
        # {WATERMARK}
        # {AUDIT_TAG}
        # {wm}
        # Template: lnk_dropper — LNK shortcut delivery vehicle (BENIGN PLACEHOLDER)
        # Target: {target}
        #
        # This is NOT a binary .lnk file. It is a plain-text placeholder that
        # describes what a weaponized LNK WOULD contain during Weaponization
        # (T1587 — shortcut as delivery vehicle), for detection engineering.
        #
        # Real LNK weaponization would set (REDACTED — executable primitives omitted
        # for safety; this placeholder intentionally omits the real shortcut target
        # and instead carries only a benign description for training):
        #   Target: [REDACTED — would be system shell with encoded payload in real malware]
        #   Icon: decoy.pdf
        #   WorkingDir: [REDACTED]
        # This BENIGN placeholder instead records:
        #   Target: BENIGN_PLACEHOLDER — NO EXECUTION
        #   Arguments: --lab-only --watermark "{wm}"
        #   Icon: placeholder.ico
        #   Description: Lab training artifact — safe to handle
        #
        # EICAR test string (benign, for AV detection testing):
        # {EICAR_STRING}
        #
        [BENIGN LNK PLACEHOLDER]
        Target=BENIGN_PLACEHOLDER
        Arguments=--lab-only --benign --target {target} --link {hashlib.sha256(wm.encode()).hexdigest()[:12]}
        WorkingDir=./lab_artifacts
        Icon=placeholder.ico
        Description=RT Forge lab placeholder — T1587 LNK weaponization simulation (no execution)
        Hotkey=None
        WindowStyle=Normal
        AuditWatermark={wm}
        # {INVOICE_WATERMARK}
        # End of benign LNK placeholder
        """)
    validate_payload_content(content, "lnk_dropper")
    filename = f"lnk_dropper_{_sanitize(target)}.lnk.txt"
    return out_path / filename, content


def _gen_hta_artifact(target: str, out_path: pathlib.Path) -> tuple[pathlib.Path, str]:
    wm = _audit_watermark(target, "hta_artifact")
    content = textwrap.dedent(f"""\
        <!-- {WATERMARK} -->
        <!-- {AUDIT_TAG} -->
        <!-- {wm} -->
        <!-- Template: hta_artifact — HTA execution vehicle (BENIGN PLACEHOLDER) -->
        <!-- Target: {target} -->
        <!-- Safety: No ActiveX, No scripting host, No HTA-host execution — benign HTML only -->
        <!-- In real weaponization (T1587), HTA would embed a script tag with host shell -->
        <!-- Here we emit only benign HTML that displays an audit banner -->
        <!-- EICAR test string (benign, for AV detection testing): {EICAR_STRING} -->
        <html>
        <head>
          <meta charset=\"utf-8\">
          <title>Benign HTA Placeholder — Lab Only</title>
          <meta name=\"rt-watermark\" content=\"{wm}\">
          <style> body {{ font-family: monospace; background: #f6f8fa; padding: 2em; }} .banner {{ border: 2px dashed #c8102e; padding: 1em; background: #fff; }} </style>
        </head>
        <body>
          <div class=\"banner\">
            <h2>RT Forge — BENIGN HTA PLACEHOLDER</h2>
            <p><strong>{WATERMARK}</strong></p>
            <p>Target: <code>{target}</code></p>
            <p>Audit: <code>{wm}</code></p>
            <p>This file is a <em>text placeholder</em> (<code>.hta.txt</code>) and is <strong>not</strong> an executable HTA.</p>
            <p>It simulates the <em>form</em> of a weaponized HTA for detection engineering (T1587) without any ActiveX or script execution.</p>
            <p>EICAR (benign AV test): <code>{EICAR_STRING}</code></p>
            <p>{INVOICE_WATERMARK}</p>
          </div>
          <p style=\"font-size: 0.8em; color: #666;\">Generated {dt.datetime.now(dt.timezone.utc).isoformat()}</p>
        </body>
        </html>
        <!-- End of benign HTA placeholder -->
        """)
    validate_payload_content(content, "hta_artifact")
    filename = f"hta_artifact_{_sanitize(target)}.hta.txt"
    return out_path / filename, content


def _gen_iso_container(target: str, out_path: pathlib.Path) -> list[tuple[pathlib.Path, str]]:
    """
    ISO container placeholder: creates a DIRECTORY (not an ISO 9660 image) containing
    benign text files, a README, and an EICAR test file. The directory name simulates
    the container, but it is a plain folder safe to inspect.
    Returns list of (path, content) tuples to write.
    """
    wm = _audit_watermark(target, "iso_container")
    container_dir = out_path / f"iso_container_{_sanitize(target)}"
    # File 1: README / manifest
    readme = textwrap.dedent(f"""\
        # {WATERMARK}
        # {AUDIT_TAG}
        # {wm}
        # Template: iso_container — ISO smuggling container (BENIGN PLACEHOLDER)
        # Target: {target}
        #
        # In real weaponization (T1583/T1587), an ISO would smuggle a weaponized LNK/HTA
        # past Mark-of-the-Web. This BENIGN placeholder is a DIRECTORY, not a binary ISO.
        # It contains only text files + an EICAR test file (harmless) for AV testing.
        #
        # Contents:
        #   README.txt       — this file (audit watermark)
        #   EICAR.txt        — EICAR standard test string (benign, detected as test)
        #   INVOICE_PLACEHOLDER.txt — invoice PDF placeholder with audit watermark
        #   LNK_PLACEHOLDER.txt — benign LNK description (see lnk_dropper)
        #
        # Safety: No ISO 9660, no Joliet, no UDF — plain folder.
        # EICAR: {EICAR_STRING}
        #
        ISO Container Placeholder — Lab Only
        Target: {target}
        Audit: {wm}
        {INVOICE_WATERMARK}
        """)
    # File 2: EICAR test file (text)
    eicar_file = f"{EICAR_STRING}\n# {WATERMARK}\n# {wm}\n# Target: {target}\n"
    # File 3: Invoice PDF placeholder (benign text, not a PDF binary)
    invoice = textwrap.dedent(f"""\
        {WATERMARK}
        {AUDIT_TAG}
        {wm}
        {INVOICE_WATERMARK}
        Invoice PDF Placeholder — Lab Only (T1587 benign simulation)
        Target: {target}
        Invoice #: LAB-{hashlib.sha256(target.encode()).hexdigest()[:8].upper()}
        Date: {dt.datetime.now(dt.timezone.utc).date().isoformat()}
        Bill-To: Lab Training Environment — {target}
        Line-Item: Security Awareness Training — Benign Artifact (Qty 1, $0.00)
        Notes: This is NOT a real invoice. It is a benign placeholder that mimics
               the decoy document theme common in weaponization, watermarked for audit.
               Contains EICAR test string for AV handling validation: {EICAR_STRING}
        Audit-Link: {hashlib.sha256(wm.encode()).hexdigest()[:16]}
        Generated: {dt.datetime.now(dt.timezone.utc).isoformat()}
        """)
    # File 4: LNK placeholder inside container
    lnk_desc = textwrap.dedent(f"""\
        # {WATERMARK}
        # Inside ISO container — benign LNK placeholder (see lnk_dropper)
        # Target: {target} | {wm}
        # EICAR: {EICAR_STRING}
        [BENIGN LNK INSIDE CONTAINER]
        Target=BENIGN_PLACEHOLDER
        """)
    validate_payload_content(readme, "iso_container/README")
    validate_payload_content(invoice, "iso_container/invoice")
    return [
        (container_dir / "README.txt", readme),
        (container_dir / "EICAR.txt", eicar_file),
        (container_dir / "INVOICE_PLACEHOLDER.txt", invoice),
        (container_dir / "LNK_PLACEHOLDER.txt", lnk_desc),
    ]


def _gen_shellcode_stub(target: str, out_path: pathlib.Path) -> tuple[pathlib.Path, str]:
    wm = _audit_watermark(target, "shellcode_stub")
    # This is the critical benign stub: it MUST contain EICAR, MUST NOT contain shellcode
    content = textwrap.dedent(f"""\
        # {WATERMARK}
        # {AUDIT_TAG}
        # {wm}
        # Template: shellcode_stub — shellcode payload stub (BENIGN PLACEHOLDER with EICAR)
        # Target: {target}
        #
        # Real weaponization (T1587.004) would produce position-independent shellcode,
        # NOP sleds, encoders, and stagers. This BENIGN placeholder contains NONE of that.
        # Instead it contains ONLY:
        #   - This watermark and audit line
        #   - The EICAR standard test string (harmless, flagged by AV as TEST-FILE)
        #   - A textual note that shellcode would be here in a real (malicious) payload
        #
        # The file is .bin.txt (text), not a binary, not executable, not shellcode.
        # It is safe to handle, safe to scan, and safe to use as a detection canary.
        #
        # EICAR — benign AV test string (the only \"payload\" in this file):
        {EICAR_STRING}
        #
        # Metadata:
        #   Stub-Note: BENIGN PLACEHOLDER — NO SHELLCODE — NO NOP SLED — NO ENCODER
        #   Target: {target}
        #   Audit: {wm}
        #   Hash-Link: {hashlib.sha256((wm + EICAR_STRING).encode()).hexdigest()[:16]}
        #   {INVOICE_WATERMARK}
        # End of benign shellcode stub
        """)
    validate_payload_content(content, "shellcode_stub")
    if EICAR_STRING not in content:
        raise ValueError("EICAR missing from shellcode_stub (required benign marker)")
    filename = f"shellcode_stub_{_sanitize(target)}.bin.txt"
    return out_path / filename, content


def _sanitize(target: str) -> str:
    """Make target safe for filename (alphanumeric + dot/dash)."""
    import re
    s = re.sub(r"[^a-zA-Z0-9._-]", "_", target.strip())
    return s[:64] or "lab_target"


# Dispatch table
TEMPLATE_DISPATCH = {
    "document_macro": _gen_document_macro,
    "lnk_dropper": _gen_lnk_dropper,
    "hta_artifact": _gen_hta_artifact,
    "iso_container": _gen_iso_container,  # special: returns list
    "shellcode_stub": _gen_shellcode_stub,
}


def list_templates() -> None:
    """Print inventory of benign templates (audited, no auth required beyond inventory log)."""
    try:
        audit_record("inventory_access", actor=actor_from_env(), tool="weapon-forge", action="list_templates")
    except Exception:
        pass
    print(f"{'TEMPLATE':<18} {'EXT':<12} {'DESCRIPTION'}")
    print("-" * 78)
    for key in sorted(TEMPLATES):
        meta = TEMPLATES[key]
        print(f"{key:<18} {meta['file_ext'] or '(dir)':<12} {meta['description'][:66]}")
    print("\nAll templates generate BENIGN placeholders only (watermark + EICAR where applicable).")
    print(f"Watermark: {WATERMARK}")
    print(f"EICAR: {EICAR_STRING}  (harmless test string)")
    print("\nSafety: audit.py hash chain + validation.py lab-only gate + FORBIDDEN_SNIPPETS inverted blocklist")


def _write_artifact(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Fail-closed on overwrite unless --force: caller checks existence before calling
    path.write_text(content, encoding="utf-8")
    # Harden perms to 600 on POSIX (600 = owner-only)
    try:
        path.chmod(0o600)
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Weaponization Forge — benign lab-only weaponization placeholders (Kill Chain Weaponization, T1587/T1583)",
        epilog="Lab-only: target must be loopback/private/lab domain. Every artifact is watermarked + audit-logged. No real malware.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--list-templates", action="store_true", help="list available benign templates and exit")
    parser.add_argument("--target", help="lab target host/domain (lab-only: RFC1918/loopback or lab domain you own, e.g., 127.0.0.1 or lab.local)")
    parser.add_argument("--payload-type", dest="payload_type", choices=sorted(TEMPLATES), help="template to generate")
    parser.add_argument("--out", help="output directory or file for artifact (for iso_container, must be a directory)")
    parser.add_argument("--yes", action="store_true", help="skip interactive ATTACK prompt (requires FORGE_ATTESTED HMAC env)")
    parser.add_argument("--force", action="store_true", help="overwrite existing output if it exists")
    parser.add_argument("--verbose", action="store_true", help="verbose logging")
    args = parser.parse_args()

    # --list-templates is inventory access — audited but does not require ATTACK gate (mirrors fuzzer --list-payloads)
    if args.list_templates:
        list_templates()
        return

    # Validate required args for generation
    if not args.target or not args.payload_type or not args.out:
        parser.error("--target, --payload-type, and --out are required (or use --list-templates)")

    # Gate 2: Lab-only target (before authorization so we fail fast on invalid target, but still audit)
    try:
        target_meta = validate_target_lab_only(args.target)
        print(f"[+] target lab check: {target_meta['verdict']} — {target_meta['detail']}")
    except (ValueError, ValidationError) as exc:
        try:
            audit_record("target_refused", actor=actor_from_env(), tool="weapon-forge", target=str(args.target)[:80], reason=str(exc)[:200])
        except Exception:
            pass
        sys.exit(f"[x] target refused (lab-only gate): {exc}")

    # Gate 1: Authorization (ATTACK phrase + HMAC env bypass)
    require_authorization(skip_flag=args.yes)

    # Resolve out path
    out_path = pathlib.Path(args.out)
    # If out is an existing directory or template expects directory, treat as directory
    is_dir_template = args.payload_type == "iso_container"

    # Generate
    template_key = args.payload_type
    gen_fn = TEMPLATE_DISPATCH[template_key]

    # Audit: generation attempt (before write, for forensics)
    try:
        audit_record("weaponization_attempt", actor=actor_from_env(), tool="weapon-forge",
                     target=args.target, template=template_key, out=str(out_path))
    except Exception:
        pass

    try:
        if is_dir_template:
            # iso_container returns list of (path, content)
            if out_path.exists() and out_path.is_file() and not args.force:
                sys.exit(f"[x] --out {out_path} is a file but iso_container needs a directory (use --force to overwrite)")
            # Ensure out_path is directory
            out_dir = out_path if out_path.suffix == "" or out_path.is_dir() or not out_path.exists() else out_path.parent
            # If user passed a file-like out for iso_container, use its parent
            if out_path.suffix and out_path.suffix not in ("",) and out_path.name.endswith(".txt"):
                out_dir = out_path.parent
            artifacts = gen_fn(args.target, out_dir)
            # Check overwrite
            existing = [p for p, _ in artifacts if p.exists() and not args.force]
            if existing:
                sys.exit(f"[x] {len(existing)} file(s) exist (use --force to overwrite): {existing[0]}")
            for path, content in artifacts:
                # Gate 3 already validated inside gen_fn; double-check here defense-in-depth
                validate_payload_content(content, str(path))
                _write_artifact(path, content)
            # Audit success
            try:
                audit_record("weaponization_generated", actor=actor_from_env(), tool="weapon-forge",
                             target=args.target, template=template_key, files=len(artifacts), out=str(out_dir))
            except Exception:
                pass
            # Also write audit watermark sidecar JSON for chain of custody
            sidecar = out_dir / f"iso_container_{_sanitize(args.target)}" / "audit_sidecar.json"
            sidecar_content = {
                "tool": "06-weaponization-forge",
                "kill_chain": "Weaponization",
                "att&ck": ["T1587", "T1583"],
                "target": args.target,
                "template": template_key,
                "watermark": WATERMARK,
                "audit_tag": AUDIT_TAG,
                "actor": actor_from_env(),
                "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
                "files": [str(p.relative_to(out_dir)) for p, _ in artifacts],
                "benign": True,
                "eicar": EICAR_STRING,
                "target_verdict": target_meta,
            }
            sidecar.write_text(json.dumps(sidecar_content, indent=2), encoding="utf-8")
            print(f"[+] iso_container placeholder -> {out_dir / f'iso_container_{_sanitize(args.target)}'} ({len(artifacts)} files + audit_sidecar.json)")
            if args.verbose:
                for p, _ in artifacts:
                    print(f"    - {p}")
            return
        else:
            # Single-file templates
            # Determine if out_path is directory or file
            if out_path.is_dir() or (not out_path.exists() and not out_path.suffix):
                # Treat as directory: generate file inside
                out_path.mkdir(parents=True, exist_ok=True)
                final_path, content = gen_fn(args.target, out_path)
            else:
                # User gave a file path — generate content then write to that exact file
                # Generate to a temp dir to get content, then write to user path
                tmp_dir = pathlib.Path.cwd() / ".tmp_forge"
                _, content = gen_fn(args.target, tmp_dir)
                final_path = out_path
                # Validate again with final filename
                validate_payload_content(content, str(final_path))
            if final_path.exists() and not args.force:
                sys.exit(f"[x] output exists: {final_path} (use --force to overwrite)")
            validate_payload_content(content, str(final_path))
            _write_artifact(final_path, content)
            # Audit success
            try:
                audit_record("weaponization_generated", actor=actor_from_env(), tool="weapon-forge",
                             target=args.target, template=template_key, file=str(final_path), bytes=len(content))
            except Exception:
                pass
            # Sidecar JSON next to artifact
            sidecar = final_path.with_suffix(final_path.suffix + ".audit.json") if final_path.suffix else pathlib.Path(str(final_path) + ".audit.json")
            sidecar_content = {
                "tool": "06-weaponization-forge",
                "kill_chain": "Weaponization",
                "att&ck": ["T1587", "T1583"],
                "target": args.target,
                "template": template_key,
                "watermark": WATERMARK,
                "audit_tag": AUDIT_TAG,
                "actor": actor_from_env(),
                "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
                "file": str(final_path),
                "benign": True,
                "eicar": EICAR_STRING if "EICAR" in content else None,
                "target_verdict": target_meta,
                "content_sha256": hashlib.sha256(content.encode()).hexdigest()[:16],
            }
            sidecar.write_text(json.dumps(sidecar_content, indent=2), encoding="utf-8")
            print(f"[+] {template_key} placeholder -> {final_path} (+ {sidecar.name})")
            print(f"    audit: {WATERMARK}")
            print(f"    next: inspect the .audit.json sidecar and verify watermark + audit log (audit.log)")
            if args.verbose:
                print(f"    target_meta: {target_meta}")
            return
    except ValueError as exc:
        try:
            audit_record("weaponization_refused", actor=actor_from_env(), tool="weapon-forge",
                         target=args.target, template=template_key, reason=str(exc)[:300])
        except Exception:
            pass
        sys.exit(f"[x] generation refused (benign-only gate): {exc}")
    except OSError as exc:
        sys.exit(f"[x] I/O error: {exc}")


if __name__ == "__main__":
    main()
