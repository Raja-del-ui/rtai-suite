# Contributing — Royal-Sec rtai-suite

## Ground rules
1. `python scripts/dev.py ci` must pass locally before any push (lint + compile + tests).
2. Every new behavior ships with a unit test; safety gates ship with a *negative* test.
3. No network access in unit tests — mark live tests `@pytest.mark.integration`.
4. All contributions require a **Developer Certificate of Origin (DCO)** sign-off: `git commit -s` adds `Signed-off-by:`. By signing off you certify the [DCO 1.1](https://developercertificate.org/).
5. For substantive features, an explicit **Contributor License Agreement (CLA)** on file with `legal@royal-sec.com` may be required before merge.

## Workflow
```powershell
pip install -e .[dev,recon,report,gui]
python scripts/dev.py ci          # local gate
git commit -s -m "feat(scope): ..."  # conventional commits + DCO sign-off
```

## Conventions
- Type hints on the public surface of `rtai_core` (mypy-gated).
- Errors raise specific `RTAIError` subclasses; CLI boundaries translate via `run_main` (`rtai_core/cli.py:45-52`, `rtai_core/exceptions.py:26-29`).
- User-facing strings ASCII-safe (Windows consoles).
- Security-relevant changes require an ADR note in `docs/adr/` and review by `@royal-sec/core-team` + `@royal-sec/legal` where law/privacy affected (see `CODEOWNERS:9-14`).
- Branding changes (Royal-Sec livery `rtai_core/gui/launcher.py:19-45`, `TRADEMARK.md`) require `legal@royal-sec.com` approval.

## Legal

By contributing you agree that your contribution is provided under the project’s `LICENSE` (MIT) + `EULA.md` for branded builds and that Royal-Sec may relicense it under future versions of the EULA. If your employer has IP rights, ensure you have permission before contributing.

## Reporting security issues

Do NOT file public issues for security flaws — see `SECURITY.md:10-14` (`security@royal-sec.com`, 24h ack, 90-day coordinated disclosure).
