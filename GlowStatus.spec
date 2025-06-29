# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/tray_app.py'],
    pathex=[],
    binaries=[],
    datas=[('img', 'img'), ('config', 'config')],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui', 
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',
        'pkg_resources.py2_warn',
        'requests',
        'json',
        'datetime',
        'threading',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tempfile',
        'atexit',
        'msvcrt',
        'fcntl'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GlowStatus',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowing_subsystem=False,
    icon='img/GlowStatus.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GlowStatus',
)
