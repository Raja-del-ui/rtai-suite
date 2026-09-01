
# -*- mode: python ; coding: utf-8 -*-
import pathlib
ROOT = pathlib.Path('F:\\ALL PROJECTS\\RED-TEAM-PROJECTS')
block_cipher = None
a = Analysis(
    [str(ROOT / 'rtai_core' / 'gui' / 'launcher.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'rtai_core' / 'gui' / 'assets' / 'logo.png'), 'rtai_core/gui/assets'),
        (str(ROOT / 'rtai_core' / 'gui' / 'assets' / 'logo_small.png'), 'rtai_core/gui/assets'),
        (str(ROOT / 'rtai_core' / 'version.py'), 'rtai_core'),
        (str(ROOT / 'EULA.md'), '.'),
        (str(ROOT / 'LICENSE'), '.'),
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
    [],
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
