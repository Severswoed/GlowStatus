# -*- mode: python ; coding: utf-8 -*-
import sys
import os
import json

# Get version from version.json directly
def get_version_from_json():
    try:
        # SPECPATH is the path to this .spec file, so the version.json is in the same directory
        version_file = os.path.join(os.path.dirname(SPECPATH) if 'SPECPATH' in globals() else os.getcwd(), 'version.json')
        with open(version_file, 'r') as f:
            version_data = json.load(f)
        
        version_str = f"{version_data['major']}.{version_data['minor']}.{version_data['patch']}"
        if version_data.get('pre'):
            version_str += f"-{version_data['pre']}"
        
        return version_data, version_str
    except Exception as e:
        print(f"Warning: Could not read version.json: {e}")
        return {"major": 2, "minor": 1, "patch": 0, "pre": ""}, "2.1.0"

# Get version information
version_info, version_string = get_version_from_json()

a = Analysis(
    ['src/tray_app.py'],
    pathex=[],
    binaries=[],
    datas=[('img', 'img'), ('config', 'config'), ('resources', 'resources')],
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
    excludes=['discord', 'discord.*'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GlowStatus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowing_subsystem=False,
    icon='img/GlowStatus.ico',
    version_info={
        'version': f"{version_info['major']}.{version_info['minor']}.{version_info['patch']}.0",
        'description': 'GlowStatus - Smart Calendar Light Control',
        'company': 'GlowStatus',
        'product': 'GlowStatus',
        'copyright': 'Copyright © 2024 GlowStatus',
        'file_version': f"{version_info['major']}.{version_info['minor']}.{version_info['patch']}.0",
        'product_version': version_string,
    }
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

app = BUNDLE(
    coll,
    name='GlowStatus.app',
    icon='img/GlowStatus.icns',
    bundle_identifier='com.glowstatus.app',
    version=version_string,
    info_plist={
        'NSHighResolutionCapable': 'True',
        'LSUIElement': '1',  # Background app (no dock icon)
        'NSNetworkAllowsArbitraryLoads': 'True',  # Allow OAuth network requests
        'NSAppleEventsUsageDescription': 'This app needs to open your web browser for Google OAuth authentication.',
        'NSCalendarsUsageDescription': 'This app accesses your calendar to display your meeting status.',
        'CFBundleShortVersionString': version_string,
        'CFBundleVersion': version_string,
        'CFBundleURLTypes': [
            {
                'CFBundleURLName': 'OAuth Redirect',
                'CFBundleURLSchemes': ['http', 'https']
            }
        ]
    },
)
