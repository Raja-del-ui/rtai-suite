# ADR-0001: Standard Library Only at Runtime

**Status:** Accepted · **Date:** 2026-08-25

## Context
The suite runs on student laptops, offline lab networks, and CI. Heavy dependency
trees (cloud SDKs) create install friction, supply-chain surface, and version drift.

## Decision
`rtai_core` and every tool runtime path depend only on the Python standard library.
Optional extras (`dnspython`, `jinja2`, `jsonschema`, `python-pptx`) are isolated to
single projects or dev workflows via `pyproject.toml` extras. HTTP is spoken through
`urllib`; LLM wire protocols are hand-implemented behind an abstraction.

## Consequences
- (+) One-command onboarding anywhere Python >=3.11 exists.
- (+) Full auditability of every network byte the suite sends.
- (-) We maintain provider protocol code ourselves (mitigated by contract tests).
