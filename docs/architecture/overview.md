# Architecture Overview — Royal-Sec rtai-suite

Five tools on one engineered core. See `BOOK.md:113-200` and `README.md:51-72` for full diagram.

- **Front doors:** `rtai` CLI (`rtai_core/cli_app.py:19-30`), `rtai-gui` (`rtai_core/gui/launcher.py:19-45`), REST API (`services/api/server.py:1-398`)
- **Core:** `rtai_core/{audit,validation,config,storage,providers,retry,models,metrics,logging_utils}` + `military_*` extensions
- **Projects:** `01-ai-recon-agent` (passive+http), `02-llm-injection-fuzzer`, `03-phishing-awareness-sim`, `04-c2-detection-lab`, `05-pentest-report-copilot`
- **Contracts:** `schemas/*.schema.json` + `tests/test_contracts.py`
- **Deployment:** `Dockerfile:1-29`, `docker-compose.yml:1-25`, `rtai_core/military_airgap.py:27-148`
