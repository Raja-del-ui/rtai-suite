# Military Modules — rtai_core/military_*

Optional hardened extensions, graceful fallback without native libs (`mypy.ini:11-29`).

- `military_sbom.py` CycloneDX/SPDX + `NOTICE.md`
- `military_mtls.py` `mTLSContextManager` for `services/api/server.py:349-364`
- `military_tpm.py:195-198` `seal_secret` (fixed `pcr_policy.items()`) + `military_pqc.py:77` ML-KEM
- `military_opa.py` `export_bundle`, `military_airgap.py:27-148` bundle generator, `military_tla.py`, `military_stix.py`
- See `docs/MILITARY_GRADE_GAP_ANALYSIS.md:10-26` MG-01..MG-15
