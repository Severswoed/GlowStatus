# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import copy_metadata

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(SPEC))

# Define paths
src_dir = os.path.join(current_dir, 'src')
img_dir = os.path.join(current_dir, 'img')
resources_dir = os.path.join(current_dir, 'resources')
config_dir = os.path.join(current_dir, 'config')


# Collect all metadata for Google packages
datas = []
datas += copy_metadata('google-auth')
datas += copy_metadata('google-auth-oauthlib')
datas += copy_metadata('google-api-python-client')
datas += copy_metadata('google-api-core')
datas += copy_metadata('googleapis-common-protos')
datas += copy_metadata('httplib2')
datas += copy_metadata('oauth2client')
datas += copy_metadata('Pillow')
datas += copy_metadata('requests')
datas += copy_metadata('urllib3')

# Add data directories
datas += [(img_dir, 'img')]
datas += [(resources_dir, 'resources')]

# Create config directory in the bundle if it exists
if os.path.exists(config_dir):
    datas += [(config_dir, 'config')]



# --- Minimal PySide6/Qt plugin inclusion for onefile mode ---
from PyInstaller.utils.hooks import collect_data_files
import PySide6
import glob

# Only include the essential Qt platform plugin (windows)
datas += collect_data_files("PySide6", subdir="Qt/plugins/platforms")
datas += collect_data_files("PySide6", subdir="Qt/plugins/imageformats")

# Only include the main Qt6Core.dll and Qt6Gui.dll (needed for most PySide6 apps)
qt_bin = os.path.join(os.path.dirname(PySide6.__file__), "Qt", "bin")
if os.path.exists(qt_bin):
    for dll in glob.glob(os.path.join(qt_bin, "Qt6Core.dll")):
        datas.append((dll, os.path.join("PySide6", "Qt", "bin")))
    for dll in glob.glob(os.path.join(qt_bin, "Qt6Gui.dll")):
        datas.append((dll, os.path.join("PySide6", "Qt", "bin")))

# Hidden imports - only essential for PySide6 minimal test
hiddenimports = [
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
]

# Analysis configuration
a = Analysis(
    [os.path.join(src_dir, 'tray_app.py')],
    pathex=[current_dir, src_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate entries and optimize
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create the executable - SINGLE FILE MODE
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GlowStatus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX compression for compatibility
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(img_dir, 'GlowStatus.ico') if os.path.exists(os.path.join(img_dir, 'GlowStatus.ico')) else None,
    version=None,
    uac_admin=False,
    uac_uiaccess=False,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    hide_console='hide-late',  # Hide console after initialization
    onefile=True
)