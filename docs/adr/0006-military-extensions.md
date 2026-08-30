# ADR-0006: Military-Grade Extensions (SBOM, OPA, mTLS, TPM, PQC, Audit Chain)

**Date:** 2026-08-30  
**Status:** Accepted — extended 2026-08-30 for Royal-Sec commercial hardening  
**Context:** See `docs/MILITARY_GRADE_GAP_ANALYSIS.md:10-26` MG-01..MG-15 and `rtai_core/military_*.py` modules. Suite needed SLSA/BOM, policy, crypto, and attestation surfaces for DoD/IC labs and Royal-Sec authorized commercial use.

## Decision

Add optional military-grade modules under `rtai_core/` that degrade gracefully when native libs absent:

* **SBOM** `rtai_core/military_sbom.py` — SPDX/CycloneDX generation (used for `NOTICE.md`, `release.yml`).
* **OPA** `rtai_core/military_opa.py` — policy bundle export (`export_bundle`) for future RBAC (`future.md:F-A01`).
* **mTLS/SPIFFE** `rtai_core/military_mtls.py` — `mTLSContextManager`/`MTLS` for `services/api/server.py` TLS termination.
* **TPM** `rtai_core/military_tpm.py` — `TPM2Interface`/`TPMKeyManager.seal_secret` (fixed `pcr_policy.items()` at `military_tpm.py:198`) for sealing `RTAI_API_TOKEN`/`RTAI_ATTEST_KEY`.
* **PQC** `rtai_core/military_pqc.py` — ML-KEM/ML-DSA hybrid for forward secrecy.
* **Audit chain** `rtai_core/audit.py` — hash-chained JSONL (`GENESIS`, `sha256(canonical)`) for `authorization`/`auth_failure`/`recon_*` events.

All are typed but `mypy.ini:11-26` `ignore_errors` while `liboqs`/`tpm2` optional.

## Consequences

* Commercial: SBOM shipped as `NOTICE.md` + release artefact; TPM sealing roadmaps to `F-M05`; audit chain required by `EULA.md` §2.3.
* Vendored copies in `01-05/rtai_core/` must stay byte-identical — enforced by `tests/test_meta.py:23-35`.
* No breaking change to stdlib-only runtime (`docs/adr/0001-stdlib-only-runtime.md`) — military modules are extra.
