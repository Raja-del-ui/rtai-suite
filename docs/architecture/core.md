# Core Library — rtai_core

Shared library vendored into `01-*/05-*/rtai_core/` (verified `tests/test_meta.py:23-35`).

- `audit.py:17-69` hash-chain, `validation.py:27-46` lab IP, `exceptions.py:26-29` `AuthError:77`, `cli.py:45-52` error funnel, `storage.py` JSONL+SQLite, `providers/` factory
- Deterministic-first: scoring, dedupe, correlation are rule-based; LLM narrates above
- See `docs/adr/0004-shared-core-package.md` and `0005-vendored-core-standalone.md`
