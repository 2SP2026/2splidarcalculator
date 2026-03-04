# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for 2SP LiDAR Calculator.

Build:  .venv/scripts/pyinstaller 2sp_lidar_calculator.spec --clean --noconfirm
Output: dist/2SP_LiDAR_Calculator/  (one-folder distribution)
"""

from pathlib import Path
from PyInstaller.utils.hooks import collect_dynamic_libs

block_cipher = None

# -- MSVC Runtime DLLs (needed on machines without VC++ Redistributable) ---
# PySide6 ships these. We place copies at BOTH the _internal root AND the
# PySide6 subdirectory so Windows DLL search finds them no matter which
# directory Qt loads from.
pyside6_dir = Path(__import__('PySide6').__file__).parent
msvc_dlls = []
for pattern in ['vcruntime*.dll', 'msvcp*.dll', 'concrt*.dll']:
    for dll in pyside6_dir.glob(pattern):
        msvc_dlls.append((str(dll), '.'))           # _internal root
        msvc_dlls.append((str(dll), 'PySide6'))     # PySide6 subdirectory

# -- App data files --------------------------------------------------------
datas = [
    ('src/data/sensors.json', 'src/data'),
]

# -- Hidden imports ---------------------------------------------------------
hiddenimports = [
    'loguru',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
]

a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=msvc_dlls,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyinstaller_runtime_hook.py'],
    excludes=[
        # Heavy packages not used at runtime
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
        # Qt modules we don't use — avoid bloating the bundle
        'PySide6.Qt3DAnimation',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DExtras',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DRender',
        'PySide6.QtBluetooth',
        'PySide6.QtCharts',
        'PySide6.QtConcurrent',
        'PySide6.QtDataVisualization',
        'PySide6.QtDesigner',
        'PySide6.QtGraphs',
        'PySide6.QtGraphsWidgets',
        'PySide6.QtHttpServer',
        'PySide6.QtLocation',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtNfc',
        'PySide6.QtOpenGL',
        'PySide6.QtOpenGLWidgets',
        'PySide6.QtPdf',
        'PySide6.QtPdfWidgets',
        'PySide6.QtPositioning',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtQuick3D',
        'PySide6.QtQuickWidgets',
        'PySide6.QtRemoteObjects',
        'PySide6.QtScxml',
        'PySide6.QtSensors',
        'PySide6.QtSerialBus',
        'PySide6.QtSerialPort',
        'PySide6.QtSpatialAudio',
        'PySide6.QtSql',
        'PySide6.QtStateMachine',
        'PySide6.QtSvg',
        'PySide6.QtSvgWidgets',
        'PySide6.QtTest',
        'PySide6.QtTextToSpeech',
        'PySide6.QtUiTools',
        'PySide6.QtWebChannel',
        'PySide6.QtWebEngine',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebSockets',
        'PySide6.QtXml',
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
