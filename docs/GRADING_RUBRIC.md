# Grading Rubric & Self-Assessment

Score yourself honestly before submission — professors notice the difference between
"works" and "engineered".

## Rubric (100 points)

| Category | Pts | Excellent (90-100%) | Good (70-89%) | Weak (<70%) |
|---|---|---|---|---|
| **Functionality** | 25 | All 5 tools run end-to-end from README commands; offline fallbacks work | 4 tools work; minor flags needed | Fragile, undocumented invocations |
| **AI integration depth** | 20 | Structured evidence→prompt contracts; JSON outputs validated; judge+rules ensemble | LLM used meaningfully but ad-hoc prompts | API call bolted on, unvalidated |
| **Security engineering** | 15 | Attestation gates, IP guards, blocklists, marker headers all present AND tested | Gates exist but untested | Safety is comments-only |
| **Software practice** | 15 | 91 unit tests incl. contract + negative safety tests, ruff + mypy gates, CI matrix green | Tests exist, partial coverage | No tests/CI |
| **Documentation** | 10 | Proposal, study guide, runbook, threat model complete and specific | Present but generic | Missing or thin |
| **Presentation & demo** | 15 | Timed, rehearsed, live demo with fallback, crisp Q&A | Complete but unrehearsed | Read from slides / demo fails |

## Self-Assessment Checklist

- [ ] Fresh clone → each README quickstart runs without edits
- [ ] `python scripts/dev.py ci` passes locally and on the CI badge (lint+types+tests)
- [ ] Every tool's authorization gate demonstrably blocks unauthorized use
- [ ] Can explain every line of the LLM system prompts
- [ ] Can defend why severity math is deterministic while narration is generative
- [ ] Demo rehearsed with the runbook incl. offline fallback path
- [ ] Study guide viva questions answered without notes

## Suggested Weighting for Professor Discussions

If your professor asks how you'd grade it: lead with functionality + AI integration
(45 pts), because the differentiator of this suite is *substantive* AI integration with
auditable determinism — then let the rubric walk them through the rest.

