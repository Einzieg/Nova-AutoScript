# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

import msc
import mtc
import nicegui

sys.setrecursionlimit(5000)

a = Analysis(
    ['main.py'],
    pathex=[r'C:\Users\Einzieg\PycharmProjects\NovaAH\.venv'],
    binaries=[],
    datas=[(f'{Path(nicegui.__file__).parent}', 'nicegui'),
           (f'{Path(msc.__file__).parent}', 'msc'),
           (f'{Path(mtc.__file__).parent}', 'mtc'),
           ("static", "static")],
    hiddenimports=['nicegui', 'cv2', 'msc', 'mtc'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, gen_pyc=True)

exe = EXE(
    pyz,
    a.scripts,
    name='NovaAH',
    icon='static/nova-autoScript.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NovaAutoScript-0.21.3',
)
