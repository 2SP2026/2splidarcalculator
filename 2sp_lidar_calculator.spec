# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for 2SP LiDAR Calculator.

Build:  .venv/scripts/pyinstaller 2sp_lidar_calculator.spec
Output: dist/2SP_LiDAR_Calculator/  (one-folder distribution)
"""

import sys
from pathlib import Path

block_cipher = None

# -- Data files to bundle alongside the app --------------------------------
# sensors.json is the sensor database — bundled as a seed copy.
# On first launch, the frozen app copies it to a writable location
# next to the exe so users can add/edit/import sensors.
datas = [
    ('src/data/sensors.json', 'src/data'),
]

# -- Hidden imports that PyInstaller sometimes misses ----------------------
hiddenimports = [
    'loguru',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
]

a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy packages not needed at runtime
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'tkinter',
        '_tkinter',
        'unittest',
        'pytest',
        'setuptools',
        'pip',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,       # one-folder mode
    name='2SP_LiDAR_Calculator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,               # no console window — GUI app
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
    name='2SP_LiDAR_Calculator',
)
