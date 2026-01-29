# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

import msc
import mtc
import nicegui
import rapidocr_onnxruntime

sys.setrecursionlimit(5000)

# -- rapidocr ONNX runtime model files inclusion --
block_cipher = None

rapidocr_package_name = 'rapidocr_onnxruntime'
rapidocr_dir = Path(rapidocr_onnxruntime.__file__).resolve().parent

onnx_paths = list(rapidocr_dir.rglob('*.onnx'))
yaml_paths = list(rapidocr_dir.rglob('*.yaml'))

onnx_add_data = [(str(v.parent), f'{rapidocr_package_name}/{v.parent.name}')
                 for v in onnx_paths]

yaml_add_data = []
for v in yaml_paths:
    if rapidocr_package_name == v.parent.name:
        yaml_add_data.append((str(v.parent / '*.yaml'), rapidocr_package_name))
    else:
        yaml_add_data.append(
            (str(v.parent / '*.yaml'), f'{rapidocr_package_name}/{v.parent.name}'))

rapidocr_data = list(set(yaml_add_data + onnx_add_data))
# -- end rapidocr ONNX runtime model files inclusion --

# -- 其他需要额外引入的包
models = [
    (f'{Path(nicegui.__file__).parent}', 'nicegui'),
    (f'{Path(msc.__file__).parent}', 'msc'),
    (f'{Path(mtc.__file__).parent}', 'mtc'),
    ("static", "static")
]
# -- --
datas = rapidocr_data + models


# -- 需要显式引入的包
hiddenimports = ['nicegui', 'cv2', 'msc', 'mtc']
# -- --

a = Analysis(
    ['main.py'],
    pathex=[sys.prefix],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='NovaAutoScript',
)
