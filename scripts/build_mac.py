from setuptools import setup
import glob
import sys
import os

# Import build helper functions from scripts directory
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from build_helpers import check_and_install_requirements, verify_critical_modules, fix_google_namespace_packages

# Check requirements before building
if 'py2app' in sys.argv:
    print("🚀 Preparing GlowStatus for macOS app bundle creation...")
    check_and_install_requirements()
    if not verify_critical_modules():
        print("❌ Critical modules missing. Please fix the above issues and try again.")
        sys.exit(1)
    print("🔧 Fixing Google namespace packages for py2app...")
    fix_google_namespace_packages()
    print("✅ Ready to build!")
    print()

APP = ['../src/tray_app.py']
DATA_FILES = [
    ('img', glob.glob('../img/*')),  # Bundle all files in img/
    ('config', glob.glob('../config/*')),
    ('resources', ['../resources/client_secret.json']),
    # Add other needed data files/folders here
]
OPTIONS = {
    'iconfile': '../img/GlowStatus.icns',
    'packages': [
        'PySide6',
        'keyring',
        'keyrings.alt', 
        'requests',
        'dateutil',
        # Google packages
        'google_auth_oauthlib',
        'googleapiclient',
    ],
    'includes': [
        'threading',
        'queue',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',
        'shiboken6',
        # Google auth and API modules - explicitly include all submodules
        'google',
        'google.auth',
        'google.auth.base',
        'google.auth.credentials',
        'google.auth.exceptions',
        'google.auth.transport',
        'google.auth.transport.requests',
        'google.auth.transport._http_client',
        'google.oauth2',
        'google.oauth2.credentials',
        'google_auth_oauthlib',
        'google_auth_oauthlib.flow',
        'googleapiclient',
        'googleapiclient.discovery',
        'googleapiclient.errors',
        'googleapiclient._apis',
        'googleapiclient.http',
        'googleapiclient.model',
        # Additional dependencies
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
    ],
    'excludes': [
        'tkinter',
        'PyQt5',
        'PyQt6',
        'test',
        'unittest',
        'distutils',
        'setuptools',
        'pip',
        'wheel',
    ],
    'resources': DATA_FILES,
    'argv_emulation': False,
    'site_packages': True,
    'optimize': 0,  # Don't optimize bytecode to avoid issues
    'plist': {
        'CFBundleName': 'GlowStatus',
        'CFBundleDisplayName': 'GlowStatus',
        'CFBundleExecutable': 'GlowStatus',
        'CFBundleIdentifier': 'com.severswoed.glowstatus',
        'CFBundleShortVersionString': '2.0.0',
        'CFBundleVersion': '2.0.0',
        'LSUIElement': True,  # Run as background app without dock icon
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)