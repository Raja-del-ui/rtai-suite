# Building AI for Royal-Sec rtai-suite — End-to-End Guide

> **Audience:** Contributors adding or hardening any LLM-powered capability.  
> **Prerequisite:** `pip install -e .[dev]` + at least one provider (Ollama is free).  
> **Philosophy:** *Deterministic-first* — rules score; AI narrates, judges, and mutates **above** the core, never inside it.

---

## 1. The Provider Abstraction (30 min to first LLM call)

All AI flows through one surface: `rtai_core/providers`.

```python
from rtai_core.providers import ChatClient  # facade, not SDK

client = ChatClient()  # autodetects: OPENAI_API_KEY → openai, else ANTHROPIC_API_KEY → anthropic, else ollama
# explicit:
client = ChatClient(provider="ollama", model="llama3.1", timeout=60)

text = client.chat("Summarize this finding in one sentence.", system="You are a pentest report author. Be concise.")
data = client.ask_json('Return JSON: {"ok": true}', system="Respond as JSON only.")
```

**Why no SDK?** `rtai_core` is stdlib-only at runtime. `ChatProvider` ABC implements wire protocols with `urllib` + `RetryPolicy` (exponential backoff, status-aware). Adding a new provider = one class:

```python
# rtai_core/providers/my_provider.py
class MyProvider(ChatProvider):
    name = "my_provider"
    def endpoint(self): return f"{self.base_url}/chat"
    def headers(self): return {"Authorization": f"Bearer {self.api_key}"}
    def payload(self, messages, temperature, max_tokens): ...
    def extract(self, response_json): return response_json["choices"][0]["text"]
```

Register in `factory.py: PROVIDER_DEFAULTS` + `OPENAI_LIKE` map. Test with `tests/test_rtai_core.py::test_provider_factory`.

**Env contract:**

| Variable | Effect |
|---|---|
| `LLM_PROVIDER` | `openai` / `anthropic` / `ollama` (overrides autodetect) |
| `LLM_MODEL` / `LLM_BASE_URL` | model and base URL overrides |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | presence drives autodetect |

---

## 2. Prompt Engineering Contract (the only way we prompt)

Every AI call in the suite follows this contract — copy-paste it:

```python
SYSTEM_PROMPT = (
    "You are a <role>. Ground every claim in the supplied evidence; "
    "where evidence is thin, stay conservative. Cite the exact field that supports each claim. "
    "Respond as <format> only."
)

def build_prompt(evidence: dict, precomputed: dict | None = None) -> str:
    compact = json.dumps(evidence, indent=1)[:14000]  # truncation-aware
    extras = ""
    if precomputed:  # deterministic score shown beside model opinion
        extras = f"DETERMINISTIC SCORE: {precomputed['score']}/100 ({precomputed['band']}). Agree or disagree explicitly.\n"
    return f"{extras}DATA:\n{compact}\n\nTask: <numbered sections, exact headings, final line format>"
```

**Rules:**

1. **Evidence-only** — the model sees *only* the JSON we pass; system prompt forbids unsupported claims.
2. **Truncation-aware** — every `build_prompt` slices at ~14k chars and appends `...TRUNCATED...`.
3. **JSON fence stripping** — `ChatClient.ask_json` handles ```json fences + fallback regex `\{.*\}` before `json.loads`.
4. **No math in LLM** — severity, ranking, dedupe, scores are computed in Python and *shown* to the model (see `P1: compute_score` and `P5: dedupe_and_rank`).

**Example (P1 recon → analyst):**

```python
# sources.py → findings dict
# scoring.py → exposure = compute_score(findings)  # deterministic
# analyst.py → prompt = build_prompt(findings, exposure) → client.chat(prompt, SYSTEM_PROMPT)
```

---

## 3. Per-Tool AI Patterns — Copy What Exists

### P1 — Recon Agent (`01-ai-recon-agent/analyst.py`)

*Pattern: Evidence-fused assessment.*  
Collectors emit `{"ok": bool, "data": ...}` per source. `scoring.py` computes a rule-based `exposure` dict. `analyst.build_prompt` injects both. The model must cite `evidence` fields.

**To add a collector:**

```python
# sources.py
from rtai_core.registry import Registry
COLLECTORS.register("my_collector", my_fn, passive=True, priority=25)
# collect() iterates registry in priority order; passive collectors respect --include-http gate
```

### P2 — Injection Fuzzer (`02-llm-injection-fuzzer/`)

*Pattern: Ensemble detector + LLM judge + mutator loop.*

```
payloads.py (Registry) → target.send() → detectors.evaluate() (regex, high recall)
                                         ↘ judge_attempt() (LLM, high precision)
                                           detector hit → verdict=compromised (override)
                                           near-miss (score ≥3) → _mutate() → new payload → re-test
```

* **Detectors** are a `Registry` (`detectors.RULESET`). Add one: `RULESET.register("R6-my-rule", {"pattern": r"...", "severity": "high", "desc": "..."})`.
* **Judge** prompt is in `judge.py:JUDGE_SYSTEM` — returns `{"score": 0-10, "verdict": "compromised|suspicious|safe"}`.
* **Mutator** prompt is in `runner.py:MUTATOR_SYSTEM` — returns `{"payload": "..."}`.

**SARIF/JUnit:** `report.to_sarif` / `to_junit` map `AttackResult` → CI formats. `AttackResult` is a dataclass with `to_dict()` so reporters stay dict-compatible.

### P3 — Phishing Simulator (`03-phishing-awareness-sim/generator.py`)

*Pattern: Template-governed generation with safety gate.*

```python
# templates.py defines red_flags per template
# generator.generate_email(client, template_key, template, campaign, recipient, link_url)
#   → LLM prompt includes red_flags + link_url
#   → validate_draft() checks FORBIDDEN_SNIPPETS → regenerate once → hard fail
```

Never mention "simulation" inside the email body — that's a prompt constraint, tested by `validate_draft`.

### P4 — C2 Detection Lab (`04-c2-detection-lab/analyze.py`)

*Pattern: LLM drafts detections from telemetry.*

```python
# beacon.py emits JSONL → analyze.compute_stats → prompt = build_report(stats)
# System prompt: "You are a senior detection engineer..." → must output Sigma YAML + Suricata rule
```

Add a new stat in `compute_stats` (e.g., `burstiness`) → it automatically reaches the prompt (JSON dump) and the `regularity_index` discussion.

### P5 — Pentest Report Copilot (`05-pentest-report-copilot/enrich.py`)

*Pattern: Batched enrichment + narrative synthesis.*

```python
# parsers.py → findings (dicts) → dedupe_and_rank → correlate_services
# enrich.py: _compact(finding) → prompt per batch (BATCH_SIZE=6) → ask_json → Finding.analysis
# enrich.attack_narrative() + remediation_roadmap() are second-pass LLM calls over compacted refs
```

**Correlation** enriches `finding["correlated_service"]` *before* compacting so the model sees nmap banners when narrating nuclei findings.

---

## 4. Adding a New AI Capability (Checklist)

- [ ] **Evidence first** — define the JSON your capability will see; keep it under 14k when dumped.
- [ ] **Deterministic baseline** — compute at least one number in Python and show it to the model (score, rank, count). Tests assert it.
- [ ] **System prompt** — forbid hallucination, demand citations, fix output format (Markdown sections or JSON array).
- [ ] **Structured output** — use `client.ask_json` with a schema; validate keys before merging.
- [ ] **Fallback** — every AI path has a `--no-llm` / `--stats-only` degradation that still produces an artifact. Tests cover the fallback.
- [ ] **Safety** — if your feature touches P2/P3, add a blocklist/attestation and a negative test (`validate_draft`-style).
- [ ] **Registry** — if it's an extension point (collector, detector rule), register it; don't edit the engine.
- [ ] **Contract test** — add a JSON Schema under `schemas/` and a test in `tests/test_contracts.py` if you emit machine output.

---

## 5. Local Development Loop

```bash
# Free path (no keys)
ollama pull llama3.1
export LLM_PROVIDER=ollama

# One tool, fast feedback
python -m rtai_core.cli_app recon --target lab.local --json-out /tmp/findings.json

# Full gates (what CI runs)
python scripts/dev.py ci   # ruff + compileall + pytest -p no:cacheprovider --basetemp=C:\tmp\pytest -q
python -m mypy rtai_core/  # 38 files strict; military_* is isolated via ignore_errors

# Contract check
python -m pytest tests/test_contracts.py -v
```

---

## 6. Common Pitfalls (seen in reviews)

| Pitfall | Fix |
|---|---|
| Model invents a finding | Add "cite the exact field" + show deterministic score in prompt; add `validate_draft`-style post-check |
| Prompt too long → truncated evidence silently | Slice at 14k *and* log `...TRUNCATED...` so the model knows |
| Judge fooled by paraphrase | Keep regex `RULESET` as override — detector hit forces `verdict=compromised` |
| New collector breaks `--help` when dep missing | Lazy import inside function + `_require_dns()` with `RuntimeError("pip install ...")` |
| Vendored drift | `test_meta::test_vendored_cores_match_shared_core` fails build — re-run vendor sync in `scripts/` |

---

## 7. Further Reading in This Repo

- `rtai_core/providers/base.py` — the only place HTTP is spoken; read it before adding a provider.
- `rtai_core/audit.py` — how every authorization is hash-chained (copy the pattern for new security events).
- `docs/adr/0003-deterministic-first-ai.md` — rationale for the whole philosophy.
- `future.md` §6 — AI next-gen backlog (agentic recon, distilled judge, purple-team loop).

*Build AI where it reasons, keep rules where they count — Royal-Sec standard.*
