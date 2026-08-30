# Audit Chain — rtai_core/audit.py

Hash-chained JSONL `GENESIS 0*64` + `sha256(canonical)` `audit.py:17-69`. `RTAI_AUDIT_LOG` path `31`, `verify()` per line `58-69`, `actor_from_env() 86-90` + host/os_user enrichment, advisory `fcntl/msvcrt` lock `64-83`. Every `authorization`, `authorization_failed`, `auth_failure`, `recon_success`, `recon_forbidden`, `report_generated`.

```bash
RTAI_AUDIT_LOG=audit.log rtai recon --target example.com
RTAI_AUDIT_LOG=audit.log python -c "from rtai_core.audit import AuditChain; print(AuditChain().verify())"
```
