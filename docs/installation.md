# Installation — Royal-Sec rtai-suite v4.0.0

## Quick Start (Root — Recommended)

```bash
# Linux / macOS / Kali
chmod +x install.sh && ./install.sh
# Windows
install.bat
# Verify
python verify_installation.py
python -m pytest -q   # 91 tests
```

`install.sh` / `install.bat` (`Makefile:3`) install `pip install -e .[dev,recon,report,gui]` then run `verify_installation.py`. For minimal: `pip install -r requirements.txt`.

## One-Line Editable (Repo-Dev)

```bash
pip install -e .[dev,recon,report,gui]  # pyproject.toml:28-35
rtai --list          # rtai_core/cli_app.py:19-30
rtai-gui             # pyproject.toml:45-47 -> rtai_core.gui.launcher:main
```

## Standalone per Project

Each `01-*/05-*` vendors `rtai_core/` (verified by `tests/test_meta.py:23-35` + `tests/test_standalone.py:1-69`):

```bash
pip install -r 01-ai-recon-agent/requirements.txt  # dnspython>=2.6
python 01-ai-recon-agent/recon_agent.py --target example.com
python 01-ai-recon-agent/recon_agent.py --target example.com --include-http  # requires I AM AUTHORIZED
```

## Air-Gap Bundle

```bash
python -c "from rtai_core.military_airgap import AirGapBundleGenerator; from pathlib import Path; AirGapBundleGenerator(Path('.')).create_bundle(Path('.'))"
tar -xzf rtai-suite-4.0.0-airgap.tar.gz && cd rtai-suite-4.0.0 && ./install.sh
# Bundle logic fixed: rtai_core/military_airgap.py:53-58 (dst not dst/proj), 141/240/322 (bundle_dir), 198 (pcr_policy), 410-417 (bundle_dir.rglob)
```

## Docker

```bash
docker build -t rtai-suite:latest .   # Dockerfile:15-21 now copies services/schemas
docker compose up api                  # docker-compose.yml:6-13 healthcheck, require-auth opt-in
# Fail-closed commercial:
RTAI_API_TOKEN=$(openssl rand -hex 32) RTAI_REQUIRE_AUTH=1 docker compose up api
curl -H "Authorization: Bearer $RTAI_API_TOKEN" http://127.0.0.1:9000/health
```

## Environment

Copy `.env.example:1-22` → `.env` (git-ignored). For commercial, set `RTAI_API_TOKEN`, `RTAI_REQUIRE_AUTH=1`, `RTAI_ATTEST_KEY` HMAC per `AUP.md`, `PRIVACY.md`.

## Verification

* `verify_project.py:1-111` — compile + pytest + CLI + GUI wiring (fixed G5.1 `MainWindow` → functional `launcher.py:98-153`)
* `verify_installation.py` — runtime import + smoke `--help` + legal file presence
* `SECURITY.md:10-14` disclosure, `NOTICE.md` third-party attributions

## Troubleshooting

* Missing `dnspython`: `sources._DNS_OK=False` yields actionable `pip install dnspython` (`tests/test_standalone.py:48-69`).
* `RTAI_API_TOKEN not set — OPEN` warning (`services/api/server.py:381-404`) → set token for commercial.
* `refusing non-lab target(s): ... loopback/private only` (`rtai_core/validation.py:38-43`) → ensure `--host 127.0.0.1` or `--allow-public` with audit.
