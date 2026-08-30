# Changelog

## 4.1.0 — Military-Grade v4.1.0-military (Royal-Sec)

- **FIPS 140-3** `rtai_core/military_fips.py` `RTAI_FIPS=1` / `RTAI_FIPS_STRICT=1` approved-hash/cipher gating + `audit.py:28-37` FIPS-aware `_digest()` + `services/api/server.py --fips` + `Dockerfile` FIPS status + `release.yml` FIPS dry-run
- **HSM** `rtai_core/military_hsm.py` Vault→TPM NVRAM→PKCS#11→file→env chain + `RTAI_HSM_REQUIRED=1` fail-closed + `services/api/server.py:500-506` `get_secret()` for `RTAI_API_TOKEN` + `packaging/logrotate` 600 perms
- **mTLS/SPIFFE** `services/api/server.py:395-462` `--tls-cert/--tls-key/--tls-ca/--spiffe-id` via `military_mtls.py:MTLSContextManager` + `docker-compose.yml` `audit_log:/var/log/royal-sec` + `certs:/policies` mounts
- **OPA RBAC** `rtai_core/military_opa.py` 4 bundles + `services/api/server.py:268-310` `_opa_allowed()` zero_trust + `rtai_core/cli_app.py:33-90` per-tool `RTAI_HOME` + dispatch audit + `RTAI_OPA_POLICY` / `RTAI_SCOPES`
- **WORM+SIEM** `rtai_core/audit.py:93-115` `RTAI_AUDIT_WORM=1` `chattr +a` + `RTAI_SIEM_URL` POST + `packaging/logrotate/rtai-audit` + `docker-compose.yml` `audit_log` volume
- **SLSA L4** `release.yml:16-40` `cyclonedx-bom` + `scripts/sbom_enforce.py` + `slsa-github-generator` + `cosign sign-blob` `SHA256SUMS.sig` + `Dockerfile` `cryptography`
- **STIG/TLA/STIX** `scripts/stig_enforce.py` + `scripts/tla_verify.py` + `05-pentest-report-copilot/copilot.py:120-150` `--emit-stix`/`--emit-attack-navigator`/`--classification` OPA + `ci.yml` stig/tla/sbom/fips gates + gap `MG-16..MG-20` in `docs/MILITARY_GRADE_GAP_ANALYSIS.md:15-26` → **ALL CLOSED**

## 4.0.0 — Military-Grade Release

- **Hash-chained audit log** (`rtai_core/audit.py`): sha256(prev+payload) chain,
  verify() pinpoints the exact tampered line; wired into P2/P3 authorization
  attestations and API auth-failure/rate-limit events (`RTAI_AUDIT_LOG` env).
- **Async job orchestration** in rtai-api: `POST /v1/recon/async` -> 202 + job id,
  worker pool, `GET /v1/jobs[/{id}]`, optional SQLite job history (`--db`).
- **Security headers** on every API response (nosniff, DENY, no-store, no-referrer).
- **OpenAPI contract** served at `/openapi.json`.
- **JUnit XML export** for fuzzer results (`--junit`) - compromised=failure for CI gates.
- **Styled HTML reports**: P5 `--format html` (severity badges, cards, roadmap),
  P3 `metrics.py --html` click-rate dashboard with CSS bars.
- **Performance harness**: `scripts/bench.py` ops/s for detectors/parsers/scoring.
- **Governance & docs site**: CODE_OF_CONDUCT, mkdocs.yml + dispatchable Pages workflow.
- **Meta guards**: version single-source test, changelog-hygiene test, and a
  vendored-core byte-identity test that fails loudly on drift (ADR-0005 mitigation).

## 3.3.0 — Auditability & Async Platform Release

- **Hash-chained audit log** (`rtai_core/audit.py`): sha256(prev+payload) chain,
  verify() pinpoints the first tampered line; wired into P2/P3 authorization
  attestations and API auth-failure/rate-limit events (`RTAI_AUDIT_LOG` env).
- **Async job orchestration** in rtai-api: `POST /v1/recon/async` -> 202 + job id,
  worker pool, `GET /v1/jobs[/{id}]`, optional SQLite job history (`--db`).
- **Security headers** on every API response (nosniff, DENY, no-store, no-referrer).
- **OpenAPI contract** served at `/openapi.json`.
- **JUnit XML export** for fuzzer results (`--junit`) - compromised=failure for CI gates.
- **Styled HTML reports**: P5 `--format html` (severity badges, cards); P3
  `metrics.py --html` click-rate dashboard with CSS bars.
- **Performance harness**: `scripts/bench.py` (detectors/parsers/scoring ops/s).
- **Governance & docs site**: CODE_OF_CONDUCT, mkdocs.yml + dispatchable Pages workflow.
- **Meta guards**: version single-source test, changelog-hygiene test, and a
  vendored-core byte-identity test that fails loudly on drift (ADR-0005 mitigation).

## 3.2.1 — Standalone & Dual-OS Release

- **Per-project standalone operation**: every project now vendors its own
  `rtai_core` copy — zip any single folder and it runs with nothing but Python ≥3.11.
- **Cross-platform hardening**: SO_REUSEADDR on all HTTP servers (listener, landing,
  API); lazy optional-dependency guards (dnspython, jinja2) raise actionable install
  messages instead of tracebacks.
- Dual-OS (Windows + Kali/Debian) setup-and-run tables added to every README;
  Kali PEP-668 venv flow documented.
- New `tests/test_standalone.py`: subprocess launch regression for all 7 mains +
  friendly-missing-dependency behavior test.
- Root conftest priority fix: shared core wins in repo-dev mode; vendored cores win
  in standalone mode. ADR-0005 records the decision.

## 3.2.0 — Platform Release

- Fixed during final verification battery: unified-CLI sibling imports under runpy
  (script-dir path injection), string `SystemExit` codes crashing the dispatcher
  (mapped to exit 70), version single-source drift (core vs pyproject).
- **REST microservice** (`services/api/server.py`): bearer auth, per-IP sliding-window
  rate limiting, `/health` `/version` `/metrics` (Prometheus exposition),
  `POST /v1/recon`, `POST /v1/payloads/validate`; active recon requires an explicit
  authorization header.
- **Observability**: thread-safe metrics registry with Prometheus text format;
  request counters and uptime exposed at `/metrics`.
- **Unified product CLI**: `rtai <tool>` dispatcher (9 subcommands) registered as a
  console script; repo auto-discovery via upward scan or `RTAI_HOME`.
- **Containers**: multi-stage Dockerfile (non-root user, HEALTHCHECK), docker-compose
  with optional Ollama profile, `.dockerignore`.
- **Schema contracts**: JSON Schemas for recon bundles and findings bundles +
  jsonschema contract tests binding parsers/emitters to published formats.
- **Type-check gate**: mypy clean across rtai_core (18 files); dedicated CI job.
  Fixed real defects surfaced by typing (union-attr in validation, provider send
  signature, retry narrowing).
- **Release engineering**: tag-triggered sdist/wheel build workflow with clean-env
  smoke test; Dependabot (pip/actions/docker).
- **Governance**: CONTRIBUTING, CODEOWNERS, PR/issue templates, ADR-0001..0004.
- Dev conveniences: Makefile targets, `.env.example`, `requirements-dev.txt`,
  pytest `integration` marker registration.

## 3.1.0 — Industrial Architecture Release

- **rtai_core shared library**: exception hierarchy w/ exit-code mapping, structured
  logging (console + JSONL), layered config engine (defaults<file<env<CLI) with
  auto-dataclass subclasses, plugin Registry, RetryPolicy (injectable clock),
  JsonlStore + SqliteEventStore persistence, provider abstraction
  (ChatProvider ABC -> OpenAI-compatible / Anthropic / Ollama) with factory +
  autodetect, Severity/Finding models, SARIF emitter.
- All five projects migrated onto rtai_core via deprecation shims (`llm_client.py`
  re-exports core providers; public API unchanged).
- P1: collector registry, machine-readable `--json-out` bundle, typed error funnel.
- P2: AttackResult dataclass, detector rule registry, optional SQLite run log (`--db`).
- P3: CampaignConfig schema validation layered on existing gates.
- P4: BeaconProfile dataclass + validation, structured logging end-to-end,
  listener mirrors telemetry into SQLite (`--db`).
- P5: severity taxonomy via core enum, `--emit-json` findings bundle.
- Tooling: `scripts/dev.py` task runner (test/lint/compile/slides/ci), ruff gate
  (caught a latent NameError in sources.py during rollout), pre-commit config,
  .editorconfig, SECURITY.md.
- CI v2: dedicated lint job; test matrix runs pytest-cov over rtai_core.
- Packaging: `pip install -e .` now ships rtai_core.

## 3.0.0 — Industrial Release

- Packaging: `pyproject.toml`, optional-dependency groups (`recon`, `report`, `dev`)
- CI: GitHub Actions matrix (Ubuntu/Windows × Python 3.11/3.13): compileall + pytest
- Test suite: 33 offline unit tests across all five projects
- Documentation suite: PROJECT_PROPOSAL, STUDY_GUIDE (incl. viva Q&A),
  GRADING_RUBRIC, DEMO_RUNBOOK, SECURITY_AND_ETHICS (STRIDE + legal)
- Presentation: 19-slide deck generated by `tools/make_slides.py`
- LICENSE (MIT + educational notice), root conftest, coverage config

## 2.0.0 — Feature Wave

- P1: parallel collectors, TLS/Wayback/live-subdomain collectors, deterministic
  exposure scoring, baseline diffing
- P2: custom payload files, multi-turn chains, rate limiting, known-system fuzzy
  leak detection, SARIF export
- P3: tokenized click tracking + landing server + metrics dashboard,
  multi-template campaigns
- P4: timing presets, schedule-aware beaconing, kill switch, encoded tasks,
  advanced interval statistics, run comparison
- P5: Nessus parser, severity overrides, cross-tool correlation,
  Attack Narrative + remediation roadmap sections

## 1.0.0 — Initial Suite

- Five AI-integrated tools with shared provider-agnostic LLM client
  (OpenAI / Anthropic / Ollama), authorization gates, per-project READMEs.
