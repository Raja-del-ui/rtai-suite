#!/usr/bin/env python3
"""Royal-Sec: Generate docs/PRESENTATION_SLIDES.pptx for all 5 projects."""
import pathlib
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt, Emu

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "PRESENTATION_SLIDES.pptx"

ROYAL = RGBColor(0x0A, 0x19, 0x31)
GOLD = RGBColor(0xFF, 0xC1, 0x07)
GREY = RGBColor(0x54, 0x6E, 0x7A)
BG = RGBColor(0xF5, 0xF7, 0xFA)

SLIDES = [
    ("ROYAL-SEC  —  AI-Integrated Red Team Toolkit", [
        "v4.0.0  •  Military-Grade Platform  •  Windows  •  Kali Linux  •  Authorized Use Only",
        "Five standalone tools on one engineered core — REST API + GUI + Audit Chain",
        "Royal-Sec Ltd  •  legal@royal-sec.com  •  security@royal-sec.com  •  2026",
    ]),
    ("Agenda", [
        "1. Problem & Objectives  •  Scope & Ethics",
        "2. Architecture: rtai_core + Platform Layer",
        "3. Five Projects — Deep Dive (Recon / Fuzzer / Phish / C2 Lab / Report)",
        "4. Platform: CLI + GUI + REST API + Observability",
        "5. Quality Gates & Military-Grade Gaps (All Closed)",
        "6. Live Demo Plan  •  Evaluation  •  Future Roadmap",
    ]),
    ("Problem Statement", [
        "Manual recon & reporting don't scale — reporting is 30-50% of engagement effort",
        "LLM-integrated apps are a new attack surface (OWASP LLM01: Prompt Injection)",
        "Awareness training lacks realistic, measurable, authorized simulation",
        "Blue teams lack safe, tunable C2 telemetry to engineer detections",
        "Education needs industrial-grade, standalone, cross-platform tooling (Windows + Kali)",
    ]),
    ("Objectives (SMART)", [
        "O1 — Ship 5 working tools spanning MITRE ATT&CK phases (Recon → Report)",
        "O2 — Substantive AI: evidence→prompt contracts, JSON-validated outputs, judge+mutation",
        "O3 — Safety-by-construction: attestations, lab-only IP guards, blocklists, X-PhishSim",
        "O4 — Industrial practice: 91 tests + ruff + strict mypy + CI matrix (Ubuntu/Windows × 3.11/3.13)",
        "O5 — Royal-Sec platform: GUI, REST API, SBOM/SLSA, audit chain, containers",
    ]),
    ("Scope & Ethics", [
        "IN: passive OSINT • fuzzing endpoints you own • authorized simulations • lab C2 telemetry • report generation",
        "OUT: third-party exploitation, real malware, autonomous live-target exploitation",
        "Every tool enforces typed attestation or runtime guard (RTAI_AUDIT_LOG)",
        "Authorization gates + STRIDE threat model in docs/SECURITY_AND_ETHICS.md",
    ]),
    ("Architecture — One Core, Five Tools, Royal-Sec Platform", [
        "rtai_core (installable, stdlib-only runtime): providers • config • registry • storage • audit • metrics • military_*",
        "Deterministic-first: rules compute scores/rankings; LLM narrates/mutates/judges above the core",
        "Front doors: unified `rtai` CLI (10 tools) + `rtai gui` (Royal-Sec 6-tab console) + hardened REST API",
        "Persistence: JSONL + SQLite (hash-chained audit), per-project vendored core for standalone air-gap",
    ]),
    ("Platform Layer — Unified CLI + Royal-Sec GUI", [
        "`rtai --list` → recon, fuzz, phish, phish-landing, phish-metrics, c2-listen, c2-beacon, c2-analyze, report, gui",
        "`rtai gui` — Royal-Sec branded console: navy (#0A1931) / gold (#FFC107) banner, Dashboard + 5 tool tabs",
        "GUI: WorkerThread for every tool (non-blocking), live dark-terminal output, progress, stop/clear, QSettings-ready",
        "Per-project standalone: vendored rtai_core → zip any folder → works with only Python ≥3.11 + requirements.txt",
    ]),
    ("Platform Layer — REST API & Observability", [
        "Auth: Bearer token when RTAI_API_TOKEN set; per-IP sliding-window rate limiter; body caps",
        "Endpoints: /health • /version • /metrics (Prometheus) • /openapi.json • POST /v1/recon • async jobs",
        "Async jobs: POST /v1/recon/async → 202 + job_id → poll /v1/jobs/{id} (worker pool, optional SQLite history)",
        "Security headers on every response; active recon requires X-RTAI-Authorized: yes; 401/429 are audit-logged",
    ]),
    ("Tool 1/5 — Recon Agent (Reconnaissance)", [
        "Collectors (parallel registry): RDAP • DNS • CT logs • TLS inspection • Wayback • HTTP fingerprint",
        "Deterministic exposure score (rule-based) shown beside LLM assessment — audit-friendly",
        "Baseline diffing: --baseline previous.json → new subdomains / DNS drift / cert expiry",
        "Demo: rtai recon --target lab.local --json-out findings.json (+ machine-readable bundle, schema-validated)",
    ]),
    ("Tool 2/5 — Injection Fuzzer (App Attack) ★", [
        "20 payloads: authority_override, persona_switch, context_escape, obfuscation, multi-turn chains + custom JSON arsenals",
        "Ensemble: regex detectors (high recall) + LLM-as-judge (high precision) — detector overrides judge",
        "Adaptive loop: near-miss (score ≥3) → LLM mutates payload → re-test; rate limit --rps",
        "Outputs: resilience % (regression KPI) • SARIF 2.1 • JUnit XML (failures = bypasses) • SQLite run log",
    ]),
    ("Tool 3/5 — Phishing Awareness Simulator (Initial Access)", [
        "Governed templates (password_expiry, hr_bonus_letter, invoice_attachment, package_delivery, + MFA/QR in v4.1)",
        "Click tracking: tokenized links → landing server → education page; per-template metrics",
        "Safety chain: config validation → typed attestation → blocklist → X-PhishSim header → send lock (allow_send + --send)",
        "Outputs: .eml files + manifest.csv + answer_key.md + metrics.html dashboard",
    ]),
    ("Tool 4/5 — C2 Detection Lab (Command & Control) ★ Offline", [
        "Listener ⇄ beacon simulator: timing presets (regular/low_slow/bursty/office_hours), schedule-aware, encoded tasks",
        "Kill switch (--kill-after), jitter, UA rotation; telemetry mirrored to JSONL + SQLite (SO_REUSEADDR)",
        "Stats: stdev • CV • regularity index • lag-1 autocorrelation; analyze --compare for purple-team diffs",
        "AI role: drafts Sigma + Suricata rules from your telemetry — fully offline lab",
    ]),
    ("Tool 5/5 — Report Copilot (Reporting)", [
        "Parsers: nmap XML + nuclei JSONL + Nessus .nessus → normalize → dedupe → rank (severity overrides)",
        "Correlation: nuclei/Nessus findings link to nmap service banners (product + ref) for LLM context",
        "AI: per-finding narratives + exec summary + Attack Narrative (Entry→Escalation→Impact) + 30/60/90 roadmap",
        "Outputs: Markdown, HTML (--format html, styled badges), JSON bundle (schema-validated), SARIF",
    ]),
    ("Supply Chain & Military Depth", [
        "SBOM: CycloneDX 1.6 + SPDX 2.3 + SLSA v1.0 provenance — generated in release.yml as mandatory pre-build",
        "PQC: hybrid X25519+ML-KEM-768 via HKDF (liboqs optional, graceful fallback) + CryptoAgilityManager",
        "TPM 2.0: tpm2-tools via TemporaryDirectory (Bandit-clean), PCR quote & remote attestation verifier",
        "STIG: STIGProfileGenerator emits Linux + Python baselines; Dockerfile runs as non-root rtai with HEALTHCHECK",
    ]),
    ("Quality Gates & CI/CD", [
        "91 tests (core 14 + audit 8 + contracts 3 + platform 12 + standalone 8 + 5 projects 34) + 8 vendored-sync guards",
        "Static: ruff (caught real NameError) • Types: mypy strict on 38 core files (military_* isolated with rationale)",
        "CI: lint job + matrix (Ubuntu/Windows × 3.11/3.13, pytest --basetemp=C:\\tmp\\pytest, coverage) + Pages deploy",
        "Release: tag → SBOM/SLSA → sdist/wheel → clean-env smoke test → artifact upload; Dependabot (pip/Actions/Docker)",
    ]),
    ("Evaluation Highlights", [
        "Fuzzer: resilience % delta weak vs hardened prompt — the KPI for prompt defenses",
        "C2 Lab: regularity index ~1.0 (regular) vs <0.6 (bursty); SQLite queryable telemetry",
        "Report: 10 findings (nmap+nuclei+nessus) → 4 correlated to service banners (schema-valid JSON)",
        "Verification battery caught 4 defects pre-submission (version drift, runpy path, SystemExit mapping, /tmp races)",
    ]),
    ("Live Demo Plan (14 min)", [
        "0:00 Platform tour — rtai --list + rtai gui screenshot + curl /health /metrics",
        "0:02 Fuzzer (highlight) — --list-payloads → live adaptive round on Ollama (resilience %)",
        "0:06 C2 Lab (offline) — presets regular vs bursty → analyze --compare",
        "0:10 Report Copilot — --no-llm → --format html (styled badges) + JSON bundle schema check",
        "Every segment has an offline fallback artifact — no network required to pass",
    ]),
    ("Limitations", [
        "LLM hallucination risk → evidence-only prompting + deterministic override + human QA gate",
        "Recon is passive-first; crt.sh rate limits degrade gracefully (warnings, not crash)",
        "Judge models can be fooled → regex detectors win; military modules degrade gracefully without native libs",
        "Single-node API today; RBAC is token-scope level (OPA bundle hot-reload is next)",
    ]),
    ("Future Roadmap (future.md) — 40 Features Across 4 Releases", [
        "v4.1 Operator Experience: SLSA L4 (cosign), dark/light GUI theme, STIG enforcement, bench regression gate",
        "v4.2 Detection Fabric: JA3 fingerprints, indirect prompt corpus, MFA/QR templates, Jira bridge",
        "v5.0 Scale & Enterprise: Helm chart, workspaces, offline LLM bundle, Nix flake, benchmark dashboard",
        "v6.0 Autonomy: agentic recon, purple-team closed loop, formal TLA+ verified core",
    ]),
    ("Conclusion — Royal-Sec Standard", [
        "Five phases, one engineered platform: AI where it reasons, rules where it counts — Royal-Sec branded",
        "Safety is a feature, not a disclaimer: gates are typed, tested (negative tests), and CI-enforced",
        "Fully reproducible: 91-test gate, typed core, $0 Ollama path, containers, air-gap bundles, SBOM",
        "All gaps closed — see docs/MILITARY_GRADE_GAP_ANALYSIS.md (15 controls → CLOSED)",
    ]),
    ("References", [
        "OWASP Top 10 for LLM Applications (2023-2025) — LLM01 Prompt Injection",
        "MITRE ATT&CK Enterprise + ATLAS (AI threat landscape)",
        "NIST SP 800-53 rev5, CMMC 2.0 L2, DISA STIG, SLSA v1.0, NIST PQC (CNSA 2.0)",
        "Greshake et al. 2023 — Indirect Prompt Injection; Sigma HQ — Generic SIEM format",
    ]),
    ("Q&A — Backup Slides", [
        "Backup: architecture diagram, STRIDE table (incl. API row), vendored-core sync test",
        "Docs: proposal • study guide (viva Q&A) • runbook • rubric • ethics • 6 ADRs • BOOK.md (696 lines)",
        "Artifacts: SBOM (CycloneDX/SPDX), SLSA provenance, STIG profiles, TLA+ specs, STIX bundles",
        "Ask us anything — live demo fallback artifacts ready",
    ]),
]

def _add_title_slide(prs, title, bullets):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    # Royal-Sec banner
    bg = slide.shapes.add_shape(1, 0, 0, prs.slide_width, Inches(0.9))  # rectangle
    bg.fill.solid()
    bg.fill.fore_color.rgb = ROYAL
    bg.line.fill.background()
    tx = slide.shapes.add_textbox(Inches(0.4), Inches(0.18), Inches(7.5), Inches(0.55))
    tf = tx.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "ROYAL-SEC"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = GOLD
    p = tf.add_paragraph()
    p.text = "Red Team Operations  •  Military-Grade AI Platform"
    p.font.size = Pt(9)
    p.font.color.rgb = RGBColor(0xB0, 0xBE, 0xC5)
    # Version tag
    vt = slide.shapes.add_textbox(prs.slide_width - Inches(2.2), Inches(0.3), Inches(2.0), Inches(0.3))
    vt.text_frame.paragraphs[0].text = "v4.0.0  •  Windows  •  Kali Linux"
    vt.text_frame.paragraphs[0].font.size = Pt(8)
    vt.text_frame.paragraphs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    vt.text_frame.paragraphs[0].alignment = 2  # right
    # Title
    tbox = slide.shapes.add_textbox(Inches(0.4), Inches(1.2), Inches(9.2), Inches(0.9))
    tf = tbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(26)
    p.font.bold = True
    p.font.color.rgb = ROYAL
    # Bullets
    btop = Inches(2.2)
    for b in bullets:
        box = slide.shapes.add_textbox(Inches(0.6), btop, Inches(8.9), Inches(0.4))
        tf = box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = "•  " + b
        p.font.size = Pt(11)
        p.font.color.rgb = GREY
        p.space_after = Pt(4)
        btop += Inches(0.38) + (Inches(0.38) if len(b) > 90 else 0)
    # Footer
    ft = slide.shapes.add_textbox(Inches(0.4), prs.slide_height - Inches(0.35), Inches(9.2), Inches(0.25))
    p = ft.text_frame.paragraphs[0]
    p.text = "Royal-Sec  •  Authorized Use Only  •  Audit-logged  •  Standalone  •  Industrial"
    p.font.size = Pt(7)
    p.font.color.rgb = GREY
    p.alignment = 1  # center
    return slide

def build():
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)
    for title, bullets in SLIDES:
        _add_title_slide(prs, title, bullets)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    print(f"[+] {OUT}  ({len(SLIDES)} slides — Royal-Sec branded)")

if __name__ == "__main__":
    build()
