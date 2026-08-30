# Royal-Sec Terms of Service — Hosted API & Docs

**Applies to:** Hosted instances of `services/api/server.py` and docs at `https://royal-sec.com/docs` where Royal-Sec is operator.  
**Incorporates:** `EULA.md`, `AUP.md`, `PRIVACY.md`, `EXPORT_CONTROL.md`  
**Contact:** `legal@royal-sec.com`

## 1. Service

Royal-Sec may host the rtai-suite API (endpoints `GET /health /version /metrics /openapi.json`, `POST /v1/recon`, etc — `services/api/server.py:193-209`, `BOOK.md:384-433`) for your authorized lab. Use requires a bearer token (`RTAI_API_TOKEN`) and compliance with rate limits (`SlidingWindowLimiter:60-75`).

## 2. Acceptable Use

Bound by `AUP.md` §2-3. Royal-Sec may rate-limit, suspend, or audit (`audit_record("auth_failure" / "rate_limited")`).

## 3. Availability

No SLA for gratis tier; paid tiers per Order Form. Maintenance windows notified via status page. `GET /health` is not an SLA probe.

## 4. Customer Data

You retain ownership of prompts, recipient lists, and evidence you post to the API. Royal-Sec processes it per `DPA.md`. LLM calls you enable are sub-processed per your instruction.

## 5. Suspension & Termination

For breach of `AUP.md`, Royal-Sec may suspend on notice and terminate per `EULA.md` §14.

## 6. Governing Law

England & Wales.

---

*For self-hosted/air-gap deployments, `EULA.md` controls without this document.*
