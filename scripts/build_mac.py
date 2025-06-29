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

# Get the project root directory (parent of scripts directory)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Set up build logging
import datetime
import subprocess

def setup_build_logging():
    """Set up detailed build logging to help debug app size issues."""
    build_dir = os.path.join(PROJECT_ROOT, 'build')
    os.makedirs(build_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(build_dir, f'build_log_{timestamp}.txt')
    
    # Redirect both stdout and stderr to log file while still showing on console
    class TeeOutput:
        def __init__(self, file_path):
            self.terminal = sys.stdout
            self.log = open(file_path, 'w')
            
        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)
            self.log.flush()
            
        def flush(self):
            self.terminal.flush()
            self.log.flush()
            
    sys.stdout = TeeOutput(log_file)
    print(f"📝 Build log will be saved to: {log_file}")
    print(f"🕐 Build started at: {datetime.datetime.now()}")
    print(f"📁 Project root: {PROJECT_ROOT}")
    print()
    
    return log_file

# Set up logging if building
if 'py2app' in sys.argv:
    log_file = setup_build_logging()
    
    # Print diagnostic information
    print("🔍 Build configuration analysis:")
    print(f"   Python version: {sys.version}")
    print(f"   Python executable: {sys.executable}")
    print(f"   Site packages: {[p for p in sys.path if 'site-packages' in p]}")
    print()
    
    # Check sizes of key packages
    try:
        import PySide6
        pyside_path = os.path.dirname(PySide6.__file__)
        pyside_size = subprocess.check_output(['du', '-sh', pyside_path], text=True).split()[0]
        print(f"   PySide6 package size: {pyside_size} at {pyside_path}")
    except Exception as e:
        print(f"   PySide6 size check failed: {e}")
    
    try:
        import google
        google_path = os.path.dirname(google.__file__)
        google_size = subprocess.check_output(['du', '-sh', google_path], text=True).split()[0]
        print(f"   Google packages size: {google_size} at {google_path}")
    except Exception as e:
        print(f"   Google packages size check failed: {e}")
    
    print()

# Change to project root directory for the build process
original_cwd = os.getcwd()
os.chdir(PROJECT_ROOT)
print(f"📁 Changed working directory to: {PROJECT_ROOT}")

APP = ['src/tray_app.py']
DATA_FILES = [
    ('img', glob.glob('img/*')),
    ('config', glob.glob('config/*')),
    ('resources', ['resources/client_secret.json']),
    # Add other needed data files/folders here
]
OPTIONS = {
    'iconfile': 'img/GlowStatus.icns',
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
        # Core Python modules
        'threading',
        'queue',
        'json',
        'datetime',
        'tempfile',
        'atexit',
        # PySide6 essentials only
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'shiboken6',
        # Google auth essentials only
        'google.auth.credentials',
        'google.oauth2.credentials',
        'google_auth_oauthlib.flow',
        'googleapiclient.discovery',
        # Essential dependencies
        'requests',
        'urllib3',
        'certifi',
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
        # Large packages we don't need
        'numpy',
        'scipy',
        'matplotlib',
        'pandas',
        'jupyter',
        'IPython',
        'tornado',
        'notebook',
        # Development tools
        'pytest',
        'pylint',
        'black',
        'mypy',
        # Documentation tools
        'sphinx',
        'docutils',
        # Testing frameworks
        'nose',
        'coverage',
        # Unused GUI frameworks
        'wx',
        'Tkinter',
        'gtk',
        # Large standard library modules we don't use
        'pydoc_data',
        'multiprocessing',
        'xml',
        'xmlrpc',
        'html',
        'http.server',
        'wsgiref',
        'sqlite3',
        'curses',
        'turtle',
    ],
    'resources': DATA_FILES,
    'argv_emulation': False,
    'site_packages': False,  # Don't include entire site-packages
    'optimize': 2,  # Enable bytecode optimization
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

# Restore original working directory
os.chdir(original_cwd)

# Print build completion and log file location
if 'py2app' in sys.argv:
    print()
    print("🏁 Build completed!")
    print(f"🕐 Build finished at: {datetime.datetime.now()}")
    print(f"📝 Complete build log saved to: {log_file}")
    print()
    print("📊 To analyze app size, check the dist/ directory:")
    print(f"   ls -la {os.path.join(PROJECT_ROOT, 'dist/')}")
    print(f"   du -sh {os.path.join(PROJECT_ROOT, 'dist/GlowStatus.app')}")
    print()
    print("💡 To share the build log:")
    print(f"   cat {log_file}")
    print(f"   or open {log_file} in your text editor")
    
    # Close the log file
    if hasattr(sys.stdout, 'log'):
        sys.stdout.log.close()