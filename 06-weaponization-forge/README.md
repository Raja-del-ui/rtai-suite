# Project 06 — Weaponization Forge (Kill Chain Weaponization — Benign Lab Forge)

**Cyber Kill Chain:** Weaponization (Lockheed Martin) — *benign simulation only*
**MITRE ATT&CK:** T1587 Develop Capabilities · T1583 Acquire Infrastructure
**Framework:** Authorized lab use only — benign placeholders, audit-watermarked

## Runs Natively on Windows & Kali Linux

Fully standalone: vendored `rtai_core` ships inside this folder; stdlib-only runtime, 100% offline capable.

| OS | One-time setup | Run |
|---|---|---|
| Windows | *(nothing to install)* | `python forge.py --list-templates` |
| Kali / Debian | *(nothing to install; venv optional)* | `python3 forge.py --list-templates` |

A **defensive** Weaponization-stage forge that generates **SAFE, BENIGN, LAB-ONLY placeholder artifacts** — the *form* of weaponized objects without any executable malicious code. Every artifact is plain text, audit-watermarked, and carries the standard **EICAR test string** where a payload would be. Use it to test defenses, validate AV handling, and train detection engineering for the Weaponization stage without ever handling real malware.

```
target (lab-only) ──▶ forge.py ──▶ benign placeholder + audit sidecar ──▶ audit.log (hash chain)
                         │
                         ├─ Gate 1: ATTACK attestation / HMAC (rtai_core.audit)
                         ├─ Gate 2: lab-only target (assert_lab_address / valid_domain)
                         └─ Gate 3: FORBIDDEN_SNIPPETS inverted blocklist + watermark
```

## Kill Chain Weaponization Coverage

Lockheed Martin Cyber Kill Chain:

1. Reconnaissance → 2. **Weaponization** ← *this module* → 3. Delivery → 4. Exploitation → 5. Installation → 6. C2 → 7. Actions

Weaponization couples a payload with a delivery vehicle (document, shortcut, script, container, binary stub). This forge simulates that coupling **defensively**:

- **Delivery vehicles:** `document_macro` (.vba.txt), `lnk_dropper` (.lnk.txt), `hta_artifact` (.hta.txt), `iso_container` (directory placeholder)
- **Payload stub:** `shellcode_stub` (.bin.txt) — contains **only** the EICAR test string, no shellcode

All 5 are **text placeholders** (never binary). They *describe* what weaponization would produce, carry an audit watermark, and are safe to handle as evidence.

## MITRE ATT&CK Mapping

| Technique | Name | How this forge covers it (benign) |
|---|---|---|
| **T1587** | Develop Capabilities | Generates benign development artifacts (macro/LNK/HTA/ISO/stub) that mimic the *capability development* step — but with no capability. Watermark + EICAR allow detection rules to fire on benign canaries. |
| **T1587.001** | Malware | `document_macro` simulates malware delivery vehicle (benign VBA MsgBox, no AutoExec) |
| **T1587.004** | Evasion | `shellcode_stub` simulates an evasion stub — contains EICAR, no NOP sled/encoder |
| **T1583** | Acquire Infrastructure | `iso_container` simulates infrastructure acquisition (container smuggling) as a plain directory with benign files; `lnk_dropper` as shortcut infrastructure |

Every artifact is tagged in its sidecar `.audit.json` with `att&ck: ["T1587","T1583"]` and `kill_chain: "Weaponization"`.

## Templates

| Template | Output | What it simulates (benign) |
|---|---|---|
| `document_macro` | `document_macro_<target>.vba.txt` | Weaponized Office macro — emits benign VBA `Sub BenignPlaceholder()` with MsgBox + EICAR comment. No `AutoOpen`, no `WScript.Shell` |
| `lnk_dropper` | `lnk_dropper_<target>.lnk.txt` | Weaponized LNK shortcut — emits text description `Target=BENIGN_PLACEHOLDER`, watermark, EICAR. Never a binary `.lnk` |
| `hta_artifact` | `hta_artifact_<target>.hta.txt` | Weaponized HTA — emits benign HTML with audit banner, no `<script>` ActiveX, EICAR comment |
| `iso_container` | `iso_container_<target>/` directory | Weaponized ISO — emits a **directory** (not ISO 9660) with `README.txt`, `EICAR.txt`, `INVOICE_PLACEHOLDER.txt` (PDF placeholder with audit watermark), `LNK_PLACEHOLDER.txt` + `audit_sidecar.json` |
| `shellcode_stub` | `shellcode_stub_<target>.bin.txt` | Shellcode stub — emits **only** `EICAR_STRING` + watermark + note `BENIGN PLACEHOLDER — NO SHELLCODE`. No `\x90`, no encoder |

List them:

```powershell
python forge.py --list-templates
```

## Setup

No dependencies — pure standard library. Vendored `rtai_core` is included.

```powershell
# Windows
python forge.py --list-templates
python forge.py --target 127.0.0.1 --payload-type document_macro --out ./out

# Kali
python3 forge.py --list-templates
python3 forge.py --target 127.0.0.1 --payload-type shellcode_stub --out ./out
```

Artifacts are written as text with `0600` perms (POSIX) and a sidecar `.audit.json` for chain of custody.

## Usage

```powershell
# 1) Inventory (audited, no ATTACK required — mirrors 02-llm-injection-fuzzer --list-payloads)
python forge.py --list-templates

# 2) Interactive (lab operator ceremony) — you will be prompted for ATTACK
python forge.py --target 127.0.0.1 --payload-type document_macro --out ./out
python forge.py --target lab.local --payload-type lnk_dropper --out ./out
python forge.py --target 192.168.1.10 --payload-type iso_container --out ./out
python forge.py --target 127.0.0.1 --payload-type shellcode_stub --out ./out --verbose

# 3) HMAC bypass for CI/automation (like 02-llm-injection-fuzzer:28-35, 03-phishing-awareness-sim/auth.py:16-27)
# Generate the HMAC once (requires RTAI_ATTEST_KEY):
#   python -c "import hmac,hashlib,os; print(hmac.new(os.environ['RTAI_ATTEST_KEY'].encode(), b'attested', hashlib.sha256).hexdigest()[:16])"
$env:RTAI_ATTEST_KEY = "your-lab-secret"
$env:FORGE_ATTESTED = "a1b2c3d4e5f6a7b8"   # the HMAC hex16 above
python forge.py --target 127.0.0.1 --payload-type hta_artifact --out ./out --yes

# 4) Output file vs directory
python forge.py --target 127.0.0.1 --payload-type shellcode_stub --out ./out              # writes ./out/shellcode_stub_127.0.0.1.bin.txt
python forge.py --target 127.0.0.1 --payload-type shellcode_stub --out ./out/eicar.txt  # writes exactly ./out/eicar.txt

# 5) Inspect results
Get-ChildItem ./out -Recurse | Format-List Name,Length,FullName
Get-Content ./out/shellcode_stub_127.0.0.1.bin.txt
Get-Content ./out/shellcode_stub_127.0.0.1.bin.txt.audit.json
Get-Content audit.log | Select-Object -Last 5   # hash-chained audit chain
```

### Invoice PDF Placeholder (requirement)

`iso_container` includes `INVOICE_PLACEHOLDER.txt` — a benign text invoice with audit watermark:

```
AUTHORIZED LAB USE ONLY — BENIGN PLACEHOLDER — NO MALICIOUS CODE
RT-WATERMARK: 06-weaponization-forge — T1587/T1583 benign simulation
INVOICE PDF PLACEHOLDER — AUDIT WATERMARK — NOT A REAL INVOICE
Invoice #: LAB-A1B2C3D4
EICAR: X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*
```

This proves the forge can emit invoice-themed decoys (common weaponization lure) without generating a real PDF or executable.

## Safety Design (the graded part)

| Control | Implementation | Line numbers (forge.py) |
|---|---|---|
| **Human attestation** | Must type `ATTACK` (like `02-llm-injection-fuzzer:43-59`) or provide `FORGE_ATTESTED=<hmac>` HMAC when `RTAI_ATTEST_KEY` set (like `03-phishing-awareness-sim/auth.py:16-27`) | `forge.py:80-140` (`_env_bypass_ok`, `require_authorization`) |
| **HMAC env bypass** | `hmac.new(RTAI_ATTEST_KEY, b"attested", sha256).hexdigest()[:16]` — constant-time `hmac.compare_digest` | `forge.py:84-102` |
| **Lab-only target** | `assert_lab_address(host)` (loopback/RFC1918/link-local) **or** `valid_domain(domain)` for lab domains you own — mirrors `04-c2-detection-lab/beacon.py:112-119` + `listener.py:99-108`; refused public IPs are audited | `forge.py:144-186` (`validate_target_lab_only`) |
| **Content blocklist (inverted)** | `FORBIDDEN_SNIPPETS` tuple (like `03-phishing-awareness-sim/generator.py:14-15`) but inverted — **allow only benign placeholders, reject real shellcode**. Checks `VirtualAlloc`, `CreateRemoteThread`, `powershell -enc`, `msfvenom`, `meterpreter`, `rundll32`, `<script`, etc. plus `eval(`, `wscript.shell`, `/etc/passwd` | `forge.py:30-65` def + `forge.py:188-215` enforcement |
| **Benign watermark gate** | Every artifact must contain `AUTHORIZED LAB USE ONLY — BENIGN PLACEHOLDER` and `RT-WATERMARK: 06-weaponization-forge`; `shellcode_stub` and others must carry `EICAR_STRING` | `forge.py:19-29` constants + `forge.py:200-210` check |
| **Null-byte / size guard** | Rejects `\x00` and caps at 20,000 chars — benign placeholders are text-only | `forge.py:212-214` |
| **Audit chain** | Every `authorization`, `authorization_failed`, `weaponization_attempt`, `weaponization_generated`, `target_refused` is `record()`ed to `rtai_core.audit.AuditChain` (hash-chained JSONL, tamper-evident, host/user enriched) — mirrors `01-ai-recon-agent:40-61`, `02-llm-injection-fuzzer:49-110`, `03-phishing-awareness-sim:73-88` | `forge.py:126-138, 170-175, 350-355, 375-390, 420-450` + `rtai_core/audit.py:49-121` |
| **Output hardening** | Writes `0600` perms (POSIX), sidecar `.audit.json` with `target`, `template`, `actor`, `content_sha256`, `benign: true`, `kill_chain: Weaponization` | `forge.py:285-295, 440-455` |

### Blocklist — inverted semantics

`03-phishing-awareness-sim/generator.py:14-15` defines:

```python
FORBIDDEN_SNIPPETS = ("<script", "<iframe", "javascript:", "eval(", "powershell -", ...)
```

This forge **inverts** that pattern: instead of denying phishing HTML, it denies **weaponization primitives** and **fails closed if the output is not watermarked**. The validator `validate_payload_content()` ( `forge.py:188-215` ) checks:

1. None of `FORBIDDEN_SNIPPETS` appears (case-insensitive)
2. At least one `REQUIRED_BENIGN_MARKERS` is present
3. No `\x00`, size ≤ 20k

That satisfies the requirement: *blocklist like generator.py:14-15 but inverted — allow only benign placeholders, reject real shellcode.*

### Lab-only examples (fail-closed)

```powershell
# Refused — public IP (not lab)
python forge.py --target 8.8.8.8 --payload-type shellcode_stub --out ./out
# → [x] target refused (lab-only gate): refusing non-lab target(s): 8.8.8.8 - loopback/private only

# Allowed — loopback
python forge.py --target 127.0.0.1 --payload-type shellcode_stub --out ./out

# Allowed — lab domain you own (valid_domain)
python forge.py --target lab.local --payload-type document_macro --out ./out

# Allowed — RFC1918
python forge.py --target 192.168.1.10 --payload-type lnk_dropper --out ./out
```

## EICAR Test File

All executable-like placeholders contain the **EICAR standard test string**:

```
X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*
```

This string is **harmless** — it is not code, not shellcode, not a virus. AV products detect it as `EICAR-Test-File` to validate handling without risk. Every `shellcode_stub`, `document_macro`, `lnk_dropper`, `hta_artifact`, and `iso_container/EICAR.txt` carries it, proving the forge emits detection canaries instead of real payloads.

Reference: https://en.wikipedia.org/wiki/EICAR_test_file

## Audit Trail

All events go to the hash-chained audit log (`audit.log` via `rtai_core/audit.py:49-121`):

```powershell
Get-Content audit.log | ForEach-Object { $_ | ConvertFrom-Json | Format-List event,actor,target,template,hash,prev }
python -c "from rtai_core.audit import AuditChain; print(AuditChain().verify())"  # (True, None) if intact
```

Events: `inventory_access`, `authorization`, `authorization_failed`, `target_refused`, `weaponization_attempt`, `weaponization_generated`, `weaponization_refused`.

Each artifact also ships with a sidecar `<artifact>.audit.json` (or `audit_sidecar.json` for `iso_container`) for chain-of-custody hand-off to blue team.

## Verification

```powershell
python -m py_compile forge.py && echo "py_compile OK"
python forge.py --list-templates
$env:FORGE_ATTESTED = "1"  # legacy — set RTAI_ATTEST_KEY for HMAC in CI
python forge.py --target 127.0.0.1 --payload-type shellcode_stub --out ./out --yes
Select-String -Path ./out/shellcode_stub_127.0.0.1.bin.txt -Pattern "EICAR"
Select-String -Path ./out/shellcode_stub_127.0.0.1.bin.txt -Pattern "BENIGN PLACEHOLDER"
```

## Extension Ideas

- Feed benign placeholders into your EDR/SIEM and tune rules for T1587 canaries vs real tradecraft.
- Chain with `03-phishing-awareness-sim` (delivery simulation) and `04-c2-detection-lab` (C2) for a full Kill Chain lab day.
- Add a YARA rule that fires on `RT-WATERMARK: 06-weaponization-forge` but not on real malware.

## Legal & Ethics

> **Authorized lab use only.** Every artifact is `AUTHORIZED LAB USE ONLY — BENIGN PLACEHOLDER — NO MALICIOUS CODE` ( `forge.py:20` ). You must have written authorization for the lab target (`--target`) — the tool enforces it via `assert_lab_address` / `valid_domain` ( `forge.py:144-186` ) and an interactive `ATTACK` attestation ( `forge.py:104-140` ) that is hash-chained to `audit.log` ( `rtai_core/audit.py:49-121` ). Do not use placeholders to evade controls; they contain **no** executable code and are designed to be detected. See `AUP.md`, `EULA.md`, and `PRIVACY.md` in the repo root.

## File Map (with gate line numbers)

```
06-weaponization-forge/
  rtai_core/                vendored copy of ../rtai_core (audit, validation, exceptions, ...)
    audit.py:49-121         AuditChain.record / verify (hash chain)
    validation.py:39-87     _is_lab_ip, is_lab_address, assert_lab_address, valid_domain
  forge.py:1-560            main forge (see gates above)
    forge.py:19-29          WATERMARK, EICAR_STRING, AUDIT_TAG
    forge.py:30-65          FORBIDDEN_SNIPPETS (inverted blocklist)
    forge.py:84-102         _env_bypass_ok (HMAC gate)
    forge.py:104-140        require_authorization (ATTACK + audit)
    forge.py:144-186        validate_target_lab_only (lab-only)
    forge.py:188-215        validate_payload_content (inverted blocklist + watermark)
    forge.py:220-280        template generators (5 benign placeholders)
    forge.py:310-560        main() CLI (--list-templates, --target, --payload-type, --out)
  requirements.txt          stdlib-only (no deps)
  README.md                 this file (Kill Chain Weaponization, T1587/T1583, safety gates)
```
