# ADR-0002: Provider Abstraction with Factory Autodetection

**Status:** Accepted · **Date:** 2026-08-25

## Context
Tools must run against OpenAI, Anthropic, or a local Ollama without code changes,
including in air-gapped classrooms where cloud keys are unavailable.

## Decision
`ChatProvider` ABC defines one class per wire protocol (OpenAI-compatible covers
Ollama/vLLM/LM Studio). A factory resolves explicit args > env (`LLM_PROVIDER`,
keys) > autodetect (any cloud key present, else Ollama). `ChatClient` is the only
surface tools see.

## Consequences
- (+) Swapping providers is configuration, not refactoring.
- (+) Deterministic retry/backoff policy lives in one place.
- (-) New protocol = new provider class; factory must stay dependency-free.
