# ADR-0004: Shared Core Package Instead of Per-Project Copies

**Status:** Accepted · **Date:** 2026-08-25

## Context
v1 duplicated `llm_client.py` across five folders; fixes had to be applied five times
and behavior drifted.

## Decision
Introduce `rtai_core` as an installable package (`pip install -e .`) owning all
cross-cutting concerns (providers, logging, config layering, registries, storage,
validation, models). Project-local `llm_client.py` files remain only as deprecation
shims re-exporting the core so existing imports and public APIs survive.

## Consequences
- (+) Single fix point; contract tests cover the core once.
- (+) Console entry points (`rtai ...`) become possible.
- (-) Projects are no longer fully standalone single-file-copy demos;
     `RTAI_HOME`/editable install required (documented in README).
