"""
PyInstaller runtime hook — runs BEFORE main.py.

Adds the PySide6 and _internal directories to the Windows DLL search
path so Qt DLLs and MSVC runtime can find each other regardless of
where PyInstaller places them.
"""

import os
import sys

if getattr(sys, 'frozen', False):
    base = sys._MEIPASS  # _internal directory

    # os.add_dll_directory() was added in Python 3.8+ and is the
    # correct way to extend DLL search on Windows 10 1607+.
    if hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(base)

        pyside6_dir = os.path.join(base, 'PySide6')
        if os.path.isdir(pyside6_dir):
            os.add_dll_directory(pyside6_dir)

        shiboken6_dir = os.path.join(base, 'shiboken6')
        if os.path.isdir(shiboken6_dir):
            os.add_dll_directory(shiboken6_dir)

    # Also prepend to PATH as a fallback for older Windows
    os.environ['PATH'] = base + os.pathsep + os.environ.get('PATH', '')
