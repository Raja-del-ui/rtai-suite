# Reconnaissance Report — example.com

*Generated 2026-08-31 02:29 · Mode: PASSIVE ONLY · Authorized engagement use only*

## Collection Status

| Collector | Status |
|---|---|
| dns | OK |
| rdap | OK |
| tls_certificate | OK |
| certificate_transparency | FAILED (HTTPError: HTTP Error 502: Bad Gateway) |
| wayback_history | OK |
| ip_resolution | OK |
| email_security | OK |

## AI Analysis

## Executive Summary
The target `example.com` demonstrates a highly hardened external posture, utilizing Cloudflare for infrastructure and employing strict "Null MX" and DMARC policies to prevent email spoofing. While the rule-based score of 5/100 correctly identifies a missing CAA record, it fails to account for a sensitive access token leak identified in historical archives. I **disagree** with the "Low" score and would elevate it to **Medium** due to the presence of actionable credentials in the `wayback_history`.

## Attack Surface Overview
*   **Infrastructure:** The domain is fronted by Cloudflare, masking the origin server behind Anycast IPs (`104.20.23.154`, `172.66.147.243`) and utilizing Cloudflare's name servers (`elliott.ns.cloudflare.com`).
*   **Email:** Highly restrictive configuration; the domain uses a Null MX record (`MX 0`) and a "hard fail" SPF policy, indicating it is not intended to send or receive mail.
*   **Web:** The web surface has been subject to extensive automated fuzzing and security research, as evidenced by 60 archived paths containing XSS, SQLi, and RCE payloads. 
*   **Certificates:** A wildcard TLS certificate (`*.example.com`) is issued by SSL Corporation, valid until October 2026.

## Priority Findings
1.  **Observation: Leaked Access Token in Historical Archive**
    *   **Evidence:** `wayback_history.data.paths`: `/%22%20\\l%20%22access_token=06ee7434-9499-4766-8502-5d858f3d53c4&token_type=bearer&expires_in=41970` (Archived: 2024-10-06).
    *   **Attacker Value:** This Bearer token, archived as recently as late 2024, may still be valid or provide a template for session hijacking. It suggests a potential misconfiguration where sensitive tokens are leaked into URLs or logs.
    *   **Remediation:** Revoke the specific UUID token and audit application code to ensure sensitive credentials are never passed via GET parameters or exposed in headers that could be indexed.

2.  **Observation: Extensive Exposure to Automated Exploitation Tools**
    *   **Evidence:** `wayback_history.data.paths` contains multiple payloads: `/%22%20&%20start%20calc.exe` (RCE), `/%22&gt;&lt;script&gt;alert(/XSSPOSED/);&lt;/script&gt;` (XSS), and `/%22%20-F%20%22file=@/etc/passwd` (LFI/File Upload).
    *   **Attacker Value:** The presence of these paths in the Wayback Machine indicates the site is a frequent target for automated scanners. An attacker can analyze which specific paths were archived to identify historical vulnerabilities or bypasses

---
_AI-generated analysis: verify every claim against the raw evidence in `raw_findings.json` before acting on it._

## Deterministic Exposure Score

**5/100 (LOW)**

| Driver | Points | Note |
|---|---|---|
| caa_missing | +5 | no CAA record: any CA may issue certificates |
