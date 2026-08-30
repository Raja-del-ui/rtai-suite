# ADR-0003: Deterministic-First AI Integration

**Status:** Accepted · **Date:** 2026-08-25

## Context
LLMs hallucinate; severity math, deduplication, ranking, and authorization gates
must be auditable and repeatable for academic and client trust.

## Decision
Rules compute all scores, rankings, and verdicts that carry consequences.
LLMs operate *above* deterministic outputs: they narrate evidence, judge ambiguous
responses (with regex detectors able to override the judge), mutate payloads, and
author detections/reports from structured JSON contracts. Every AI-influenced
artifact displays its deterministic counterpart (e.g., exposure score beside the
model's opinion).

## Consequences
- (+) Hallucinations cannot silently change risk ratings.
- (+) Every tool has a `--no-llm` / offline degradation path.
- (-) Some model capabilities (free-form reasoning about tradeoffs) are bounded.
