# TPM Attestation

`rtai_core/military_tpm.py:195-198` fixed `pcr_policy.items()`, `TPM2Interface`/`TPMKeyManager`, `WindowsTPM`. Use `TemporaryDirectory` (Bandit-clean). Seals `RTAI_API_TOKEN`/`RTAI_ATTEST_KEY`.
