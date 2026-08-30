@echo off
echo === Royal-Sec rtai-suite — Installation (Windows) ===
echo Checking Python version...
python --version

echo Creating virtual environment (.venv)...
python -m venv .venv

echo Activating...
call .venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing Royal-Sec suite...
python -m pip install -e .[dev,recon,report,gui] 2>nul
if errorlevel 1 python -m pip install -e .[recon,report] 2>nul
if errorlevel 1 python -m pip install -r requirements.txt

echo Verifying...
python -c "import rtai_core; print('rtai_core', rtai_core.__version__)"
python verify_installation.py
if errorlevel 1 echo [warn] verify_installation.py check failed — see output

echo.
echo === Installation Complete ===
echo   rtai --list
echo   rtai --help
echo   rtai recon --target example.com
echo   rtai-gui
echo   python services\api\server.py --port 9000
