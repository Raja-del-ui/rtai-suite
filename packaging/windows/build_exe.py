"""Build Windows exe — one-file installer for Royal-Sec Tactical Console.

Usage:
  python packaging/windows/build_exe.py            # dry-run (checks PyInstaller)
  python packaging/windows/build_exe.py --build    # actually builds dist/Royal-Sec-rtai-suite-Setup.exe
  python packaging/windows/build_exe.py --installer # also builds Inno Setup installer if ISCC.exe found

Output:
  dist/Royal-Sec-rtai-suite.exe              (one-file GUI, ~80MB)
  dist/Royal-Sec-rtai-suite-Setup.exe        (Inno Setup installer, if built)
  dist/SHA256SUMS + SHA256SUMS.sig (cosign if available)
"""
import argparse
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DIST = ROOT / "dist"
SPEC_GUI = ROOT / "packaging" / "windows" / "rtai-gui.spec"
ISS = ROOT / "packaging" / "windows" / "installer.iss"

PYINSTALLER_SPEC = r'''
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None
a = Analysis(
    ['rtai_core/gui/launcher.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        ('rtai_core/gui/assets/logo.png', 'rtai_core/gui/assets'),
        ('rtai_core/gui/assets/logo_small.png', 'rtai_core/gui/assets'),
        ('rtai_core/version.py', 'rtai_core'),
        ('EULA.md', '.'),
        ('LICENSE', '.'),
    ],
    hiddenimports=['rtai_core.gui.mission_gui','rtai_core.gui.stix_gui','rtai_core.gui.weaponize_gui','rtai_core.gui.persist_gui','rtai_core.gui.apt_gui','rtai_core.gui.killchain_gui','rtai_core.mission','rtai_core.military_fips','rtai_core.military_hsm'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='Royal-Sec-rtai-suite.exe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(ROOT / 'assets' / 'logo.ico') if (ROOT / 'assets' / 'logo.ico').exists() else None,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=True, name='Royal-Sec-rtai-suite')
'''

INNO_ISS = r'''
; Inno Setup script — Royal-Sec Tactical Console
#define MyAppName "Royal-Sec rtai-suite"
#define MyAppVersion "4.1.0-military"
#define MyAppPublisher "Royal-Sec Ltd"
#define MyAppURL "https://royal-sec.com"
#define MyAppExeName "Royal-Sec-rtai-suite.exe"

[Setup]
AppId={{8E4A9F2C-7B5D-4E2A-9F8C-123456789ABC}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={pf}\Royal-Sec\rtai-suite
DefaultGroupName=Royal-Sec
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=Royal-Sec-rtai-suite-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\..\assets\logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\Royal-Sec-rtai-suite.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\EULA.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  MsgBox('Royal-Sec Tactical Console will be installed.' + #13#10 + 'First launch will prompt to set a GUI password (PBKDF2, audit-logged).', mbInformation, MB_OK);
  Result := True;
end;
'''

def ensure_spec():
    SPEC_GUI.parent.mkdir(parents=True, exist_ok=True)
    if not SPEC_GUI.exists():
        SPEC_GUI.write_text(PYINSTALLER_SPEC.replace("ROOT", repr(str(ROOT))), encoding="utf-8")
        print(f"[+] wrote {SPEC_GUI}")
    if not ISS.exists():
        ISS.write_text(INNO_ISS, encoding="utf-8")
        print(f"[+] wrote {ISS}")
    # also ensure assets/logo.ico exists (convert png if needed)
    ico = ROOT / "assets" / "logo.ico"
    png = ROOT / "rtai_core" / "gui" / "assets" / "logo.png"
    if not ico.exists() and png.exists():
        try:
            from PIL import Image
            im = Image.open(png)
            im = im.resize((256,256), Image.LANCZOS)
            im.save(ico, sizes=[(256,256),(48,48),(32,32),(16,16)])
            print(f"[+] converted {png} -> {ico}")
        except Exception as e:
            print(f"[warn] no ico: {e}")

def main():
    p = argparse.ArgumentParser(description="Build Royal-Sec Windows exe")
    p.add_argument("--build", action="store_true", help="actually run PyInstaller")
    p.add_argument("--installer", action="store_true", help="also run Inno Setup ISCC")
    args = p.parse_args()
    ensure_spec()
    print("=== Royal-Sec exe builder ===")
    print(f"ROOT: {ROOT}")
    print(f"SPEC: {SPEC_GUI}")
    # Check PyInstaller
    try:
        import PyInstaller
        print(f"[OK] PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("[x] PyInstaller not installed: pip install pyinstaller")
        print("    Dry-run: would run: pyinstaller packaging/windows/rtai-gui.spec --noconfirm --clean")
        if not args.build:
            print("[dry-run] done (no build)")
            return 0
        return 1
    if not args.build:
        print("[dry-run] PyInstaller spec ready. Run with --build to actually build.")
        print(f"  pyinstaller {SPEC_GUI} --noconfirm --clean")
        print(f"  Output: dist/Royal-Sec-rtai-suite.exe")
        if args.installer:
            print(f"  Inno Setup: ISCC {ISS}")
        return 0
    # Build
    cmd = [sys.executable, "-m", "PyInstaller", str(SPEC_GUI), "--noconfirm", "--clean"]
    print(f"[*] running: {' '.join(cmd)}")
    rc = subprocess.call(cmd, cwd=str(ROOT))
    if rc != 0:
        print(f"[x] PyInstaller failed {rc}")
        return rc
    print(f"[+] exe -> {DIST / 'Royal-Sec-rtai-suite.exe'}")
    # SHA256
    try:
        import hashlib
        exe = DIST / "Royal-Sec-rtai-suite.exe"
        if exe.exists():
            h = hashlib.sha256(exe.read_bytes()).hexdigest()
            (DIST / "SHA256SUMS").write_text(f"{h}  Royal-Sec-rtai-suite.exe\n")
            print(f"[+] SHA256: {h}")
            # cosign if available
            try:
                subprocess.run(["cosign", "sign-blob", "--yes", "--output-signature", str(DIST / "SHA256SUMS.sig"), str(DIST / "SHA256SUMS")], check=False, timeout=10)
            except Exception:
                pass
    except Exception as e:
        print(f"[warn] hash: {e}")
    if args.installer:
        # Find ISCC
        import shutil
        iscc = shutil.which("ISCC") or pathlib.Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe")
        if isinstance(iscc, pathlib.Path) and not iscc.exists():
            iscc = None
        if not iscc:
            print("[x] ISCC not found — install Inno Setup 6 from https://jrsoftware.org/isdl.php")
            return 0
        cmd = [str(iscc), str(ISS)]
        print(f"[*] running Inno Setup: {' '.join(cmd)}")
        rc = subprocess.call(cmd, cwd=str(ISS.parent))
        print(f"[+] installer -> {DIST / 'Royal-Sec-rtai-suite-Setup.exe'} rc={rc}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
