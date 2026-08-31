# 09 — APT Kill Chain Orchestrator

**Kill Chain:** Full 7-phase Lockheed Martin — Reconnaissance → Weaponization → Delivery → Exploitation → Installation → C2 → Actions on Objectives

**Orchestrates (lab-only, audit-chained):**
```
01 Recon (passive OSINT) ──┐
06 Weaponization (benign forge) ─┤
03 Phishing (tokenized link) ────┤
02 Fuzzer (LLM injection) ───────┤──▶ 05 Report (STIX + Navigator + classification)
04 C2 Lab (jittered beacon) ─────┤         ▲
07 Persistence (registry/cron sim)┤         │
08 Discovery/Lateral/Exfil ───────┘
```

**Usage:**
```
rtai mission --create --name "MANTICORE SHIELD" --classification SECRET --caveat NOFORN --targets 127.0.0.1 --approver "COL Smith"
python 09-killchain-orchestrator/orchestrator.py --target 127.0.0.1 --mission missions/OP-XXXX.json --dry-run --yes
python 09-killchain-orchestrator/orchestrator.py --target 127.0.0.1 --yes  # full run, requires KILLCHAIN_ATTESTED env or interactive I AM AUTHORIZED
python 09-killchain-orchestrator/orchestrator.py --list-phases
```

**Gates:**
- `orchestrator.py:31` `KILLCHAIN_ATTESTED` HMAC `RTAI_ATTEST_KEY` or interactive `I AM AUTHORIZED` (line 43)
- `orchestrator.py:55` `validate_target()` `assert_lab_address` or `valid_domain` (lab-only)
- Every phase `audit_record("killchain_phase_start/complete")` + `killchain_start/complete` via `rtai_core/audit.py:49`

**Phases file:line:**
- `orchestrator.py:33` `PHASES` list with script rel + args
- `orchestrator.py:65` `run_phase()` subprocess dry-run via `--help` for safe demos, timeout 15s
- `orchestrator.py:133` ROE window check via `Mission.is_active` (rtai_core/mission.py:58)

**Standalone:** Vendored `rtai_core` ships inside folder — zip and run with Python ≥3.11 only.
