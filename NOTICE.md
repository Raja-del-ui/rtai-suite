# Third-Party Notices — royal-sec-rtai-suite v4.0.0

This file lists third-party components bundled or referenced by the Software and their licences, as required for commercial distribution. Source licences are reproduced or linked. Generated in part from `rtai_core/military_sbom.py:160-214` SBOM.

## Royal-Sec Software

* `royal-sec-rtai-suite` v4.0.0 — Copyright (c) 2026 Royal-Sec Ltd — MIT + EULA (`LICENSE`, `EULA.md`).
* Trade mark “Royal-Sec” — see `TRADEMARK.md`.

## Python Dependencies (runtime, per `pyproject.toml:28-35` + per-project `requirements.txt`)

| Package | Version constraint | Import name | Licence | Upstream | Notes |
|---|---|---|---|---|---|
| `dnspython` | `>=2.6` | `dns` | **ISC** | https://www.dnspython.org | P1 `01-ai-recon-agent/requirements.txt:1-2` |
| `jinja2` | `>=3.1` | `jinja2` | **BSD-2-Clause** | https://palletsprojects.com/p/jinja/ | P5 `05-pentest-report-copilot/requirements.txt:1-2`; `rtai_core/reporting` |
| `jsonschema` | `>=4.20` | `jsonschema` | **MIT** | https://python-jsonschema.readthedocs.io | `contracts` extra; campaign/schema validation |
| `python-pptx` | `>=1.0` | `pptx` | **MIT** | https://python-pptx.readthedocs.io | `slides` extra; `tools/make_slides.py:42` |
| `PySide6` | `>=6.6` | `PySide6` | **LGPL-3.0** | https://doc.qt.io/qtforpython/ | `gui` extra; optional — alternative `PyQt6` fallback in `rtai_core/gui/launcher.py:98-153` |
| `pytest` | `>=8` (dev) | `pytest` | **MIT** | https://pytest.org | `dev` extra; test only, not distributed |
| `pytest-cov` | `>=5` (dev) | `pytest_cov` | **MIT** | https://pytest-cov.readthedocs.io | dev |
| `ruff` | `>=0.5` (dev) | `ruff` | **MIT** | https://docs.astral.sh/ruff/ | dev |
| `mypy` | `>=1.10` (dev) | `mypy` | **MIT** | https://mypy-lang.org | dev |

## Vendored / Bundled

* `rtai_core` vendored into `01-*/05-*/rtai_core/` per `docs/adr/0005-vendored-core-standalone.md:1-24`, verified by `tests/test_meta.py:23-35` + `tests/test_standalone.py:1-69`.
* `conftest.py:1-16` shadowing logic for repo-dev vs standalone — Royal-Sec.

## Fonts / Assets

* GUI `Segoe UI` references (`rtai_core/gui/launcher.py:19-45`) — system font; no redistribution.
* No other bundled fonts/images beyond Royal-Sec navy/gold QSS (`rtai_core/gui/style.py:1-19`).

## Licence Texts

* MIT (Royal-Sec): see `LICENSE:1-22`.
* ISC (dnspython): http://opensource.org/licenses/ISC
* BSD-2-Clause (Jinja2): https://opensource.org/licenses/BSD-2-Clause
* LGPL-3.0 (PySide6): https://www.gnu.org/licenses/lgpl-3.0.html — Royal-Sec links against PySide6 dynamically; no LGPL source redistribution obligation for the toolkit itself, but provide offer to supply PySide6 source on request for LGPL compliance. If you static-bundle Qt, include LGPL §6 offer.

## SBOM

Machine-readable SBOM (SPDX/CycloneDX) is produced by `rtai_core/military_sbom.py:59-68` and by `release.yml:18-19`. Published as release artefact `sbom.spdx.json` / `sbom.cyclonedx.json`. Check they match this table before each release.

---

*Update this file whenever `pyproject.toml:11-18` or per-project `requirements.txt` changes; CI `tests/test_meta.py` should assert `NOTICE.md` lists every runtime dep.*
