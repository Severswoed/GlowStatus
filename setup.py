from setuptools import setup

APP = ['src/tray_app.py']
DATA_FILES = [
    ('img', ['img/GlowStatus.icns', 'img/GlowStatus_tray_tp_tight.png']),
    ('resources', ['resources/client_secret.json']),
    # Add other needed data files/folders here
]
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'img/GlowStatus.icns',
    'packages': ['PySide6', 'google_auth_oauthlib', 'googleapiclient'],
    'resources': DATA_FILES,
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)