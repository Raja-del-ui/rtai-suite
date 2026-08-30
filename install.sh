#!/usr/bin/env bash
# Royal-Sec rtai-suite — quick install (Linux/macOS/Kali)
# Usage: chmod +x install.sh && ./install.sh
set -euo pipefail

echo "=== Royal-Sec rtai-suite — Installation ==="
echo "Checking Python version..."
if ! python3 --version 2>/dev/null; then python --version; fi

echo "Creating virtual environment (.venv)..."
python3 -m venv .venv 2>/dev/null || python -m venv .venv

echo "Activating..."
# shellcheck disable=SC1091
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || -d ".venv/Scripts" ]]; then
  # shellcheck disable=SC1091
  source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate
else
  source .venv/bin/activate
fi

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing Royal-Sec suite (editable) with extras..."
pip install -e .[dev,recon,report,gui] || pip install -e .[recon,report] || pip install -r requirements.txt

echo "Verifying..."
python -c "import rtai_core; print('rtai_core', rtai_core.__version__)"
python verify_installation.py || echo "[warn] verify_installation.py check failed — see output"

echo ""
echo "=== Installation Complete ==="
echo "  rtai --list"
echo "  rtai --help"
echo "  rtai recon --target example.com"
echo "  rtai-gui   # or: rtai gui"
echo "  python services/api/server.py --port 9000  # set RTAI_API_TOKEN for auth"
