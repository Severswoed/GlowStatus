from setuptools import setup
import glob
import subprocess
import sys
import os

def check_and_install_requirements():
    """Check if requirements are installed and install them if needed."""
    requirements_file = 'requirements.txt'
    
    if not os.path.exists(requirements_file):
        print(f"Warning: {requirements_file} not found, skipping dependency check")
        return
    
    print("Checking and installing requirements...")
    
    try:
        # Try pip3 first, then pip
        pip_cmd = 'pip3' if subprocess.run(['which', 'pip3'], capture_output=True).returncode == 0 else 'pip'
        
        # Install requirements
        result = subprocess.run([
            pip_cmd, 'install', '-r', requirements_file
        ], check=True, capture_output=True, text=True)
        
        print("✓ Requirements installed successfully")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        print(f"\n💡 Please run manually: {pip_cmd} install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error checking requirements: {e}")
        print(f"💡 Please run manually: {pip_cmd} install -r requirements.txt")

def verify_critical_modules():
    """Verify that critical modules can be imported."""
    print("🔍 Verifying critical modules...")
    critical_modules = [
        'PySide6.QtWidgets',
        'PySide6.QtCore', 
        'PySide6.QtGui',
        'keyring',
        'google.auth',
        'google_auth_oauthlib',
        'googleapiclient',
        'requests',
        'dateutil'
    ]
    
    failed_modules = []
    for module in critical_modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            failed_modules.append(module.split('.')[0])
    
    if failed_modules:
        unique_failed = list(set(failed_modules))
        pip_cmd = 'pip3' if subprocess.run(['which', 'pip3'], capture_output=True).returncode == 0 else 'pip'
        print(f"\n💡 Try installing missing modules: {pip_cmd} install {' '.join(unique_failed)}")
        return False
    
    print("✓ All critical modules verified")
    return True

# Check requirements before building
if 'py2app' in sys.argv:
    print("🚀 Preparing GlowStatus for macOS app bundle creation...")
    check_and_install_requirements()
    if not verify_critical_modules():
        print("❌ Critical modules missing. Please fix the above issues and try again.")
        sys.exit(1)
    print("✅ Ready to build!")
    print()

APP = ['src/tray_app.py']
DATA_FILES = [
    ('img', glob.glob('img/*')),  # Bundle all files in img/
    ('config', glob.glob('config/*')),
    ('resources', ['resources/client_secret.json']),
    # Add other needed data files/folders here
]
OPTIONS = {
    'iconfile': 'img/GlowStatus.icns',
    'packages': [
        'PySide6',
        'google_auth_oauthlib',
        'googleapiclient',
        'google.auth',
        'google.oauth2',
        'keyring',
        'keyrings.alt',
        'requests',
        'dateutil',
    ],
    'includes': [
        'threading',
        'queue',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',
        'shiboken6',
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
    'plist': {
        'CFBundleName': 'GlowStatus',
        'CFBundleDisplayName': 'GlowStatus',
        'CFBundleExecutable': 'GlowStatus',
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