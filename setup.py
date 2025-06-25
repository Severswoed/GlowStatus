from setuptools import setup

APP = ['src/tray_app.py']
DATA_FILES = [
    ('img', ['img/GlowStatus.icns', 'img/GlowStatus_tray_tp_tight.png']),
    ('resources', ['resources/client_secret.json']),
    # Add other needed data files/folders here
]
OPTIONS = {
    'iconfile': 'img/GlowStatus.icns',
    'packages': ['PySide6', 'google_auth_oauthlib', 'googleapiclient'],
    'resources': DATA_FILES,
    'plist': {
        'CFBundleName': 'GlowStatus',            # App bundle name
        'CFBundleDisplayName': 'GlowStatus',     # Display name in Dock
        'CFBundleExecutable': 'GlowStatus',      # Executable name inside .app
        'CFBundleIdentifier': 'com.severswoed.glowstatus',
        'CFBundleShortVersionString': '2.0.0',
        'CFBundleVersion': '2.0.0',
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)