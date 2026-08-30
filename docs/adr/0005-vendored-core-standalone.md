# ADR-0005: Vendored Core for Per-Project Standalone Operation

**Status:** Accepted · **Date:** 2026-08-25

## Context
Coursework is graded per project; students and reviewers zip single folders onto
air-gapped lab machines (Windows laptops, Kali VMs). ADR-0004's shared-core install
made folders dependent on a repository-wide editable install.

## Decision
Each project embeds its own complete copy of `rtai_core` (vendored). Resolution:
- Inside a project folder → vendored copy wins (script dir precedes sys.path).
- Repo-root pytest/dev mode → root conftest orders the shared core first, so the
  suite exercises one module identity.

Additionally: HTTP servers set SO_REUSEADDR (fast restarts on Linux TIME_WAIT),
and optional dependencies (dnspython, jinja2) fail with actionable install
messages instead of tracebacks.

## Consequences
- (+) Any single folder is portable; dual-OS support documented per project and
      enforced by subprocess launch tests in CI.
- (-) Core fixes must be re-synced to five vendored copies — mitigated by the
      shared-copy dev mode plus contract tests that fail loudly on drift.
