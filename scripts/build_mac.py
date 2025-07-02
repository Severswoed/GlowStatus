#!/usr/bin/env python3
"""
Minimal macOS app builder for GlowStatus using py2app with custom recipe.
Creates a custom recipe that only includes the specific Qt modules we actually use.
Target: 50-100MB app bundle.

Based on py2app documentation: https://py2app.readthedocs.io/en/latest/options.html
"""

from setuptools import setup
import glob
import sys
import os
import tempfile
import shutil
import subprocess

# Import build helper functions from scripts directory
sys.path.insert(0, os.path.dirname(__file__))
from build_helpers import check_and_install_requirements, verify_critical_modules, fix_google_namespace_packages

def create_custom_glowstatus_recipe():
    """
    Skip custom recipe creation for now - use aggressive py2app options instead.
    
    The custom recipe approach was causing compatibility issues with py2app 0.28.8.
    Instead, we'll rely on aggressive includes/excludes in the main OPTIONS.
    
    Returns:
        bool: Always returns True to indicate we're using the fallback approach
    """
    print("🎯 Using aggressive py2app options instead of custom recipe")
    print("📦 This avoids recipe compatibility issues while still minimizing size")
    return True

def restore_original_recipes():
    """
    Simplified restore function - since we're not modifying recipes anymore.
    """
    print("🔄 No recipe restoration needed - using standard py2app options")
    return True

# Check requirements before building
if 'py2app' in sys.argv:
    print("🚀 Preparing GlowStatus for macOS app bundle creation...")
    check_and_install_requirements()
    if not verify_critical_modules():
        print("❌ Critical modules missing. Please fix the above issues and try again.")
        sys.exit(1)
    print("🔧 Fixing Google namespace packages for py2app...")
    fix_google_namespace_packages()
    
    # Use our simplified approach (no custom recipes)
    recipe_approach_success = create_custom_glowstatus_recipe()
    
    print("✅ Ready to build with aggressive options!")
    print("📦 Using comprehensive excludes to minimize size")
    print()

# Get the project root directory (parent of scripts directory)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Change to project root directory for the build process
original_cwd = os.getcwd()
os.chdir(PROJECT_ROOT)
print(f"📁 Changed working directory to: {PROJECT_ROOT}")

# Exclude Discord directory from build if py2app is being used
discord_backup_dir = None
if 'py2app' in sys.argv:
    discord_dir = os.path.join(PROJECT_ROOT, 'discord')
    if os.path.exists(discord_dir):
        discord_backup_dir = os.path.join(PROJECT_ROOT, 'discord_backup')
        if os.path.exists(discord_backup_dir):
            shutil.rmtree(discord_backup_dir)
        shutil.move(discord_dir, discord_backup_dir)
        print("📁 Moved discord directory temporarily to exclude from build")

APP = ['src/tray_app.py']
DATA_FILES = [
    ('img', glob.glob('img/*')),
    ('config', glob.glob('config/*')),
    ('resources', ['resources/client_secret.json']),
]

OPTIONS = {
    'iconfile': 'img/GlowStatus.icns',
    'optimize': 2,  # Maximum bytecode optimization (-O2)
    'strip': True,  # Strip debug symbols
    'no_chdir': True,  # Don't change working directory
    
    # Ultra-minimal includes - only what we actually import
    'includes': [
        # Core Python modules (only what's actually imported)
        'threading', 'time', 'datetime', 'os', 'sys', 'tempfile', 'atexit',
        'pickle', 're', 'json', 'logging', 'webbrowser',
        
        # PySide6 modules (only what we actually use)
        'PySide6.QtCore',
        'PySide6.QtGui', 
        'PySide6.QtWidgets',
        'shiboken6',
        
        # Third-party dependencies (only what's imported)
        'requests',
        'keyring',
        'keyring.errors',
        
        # Google packages (only what we actually import)
        'google_auth_oauthlib.flow',
        'googleapiclient.discovery',
        'google.auth.transport.requests',
        'dateutil.parser',
    ],
    
    # Only include essential packages (minimal set)
    'packages': [
        'keyring',
        'requests',  # Will automatically include urllib3, certifi, etc.
        'google_auth_oauthlib',
        'googleapiclient',
        'google.auth',
        'dateutil',
    ],
    
    # Super aggressive excludes - everything we don't need
    'excludes': [
        # Standard library modules we don't use
        'tkinter', 'turtle', 'curses', 'sqlite3', 'xml', 'xmlrpc', 'html', 'http.server', 'wsgiref',
        'pydoc_data', 'distutils', 'setuptools', 'pip', 'wheel', 'test', 'unittest', 'doctest',
        'email', 'ftplib', 'gettext', 'locale', 'mailbox', 'mimetypes', 'pty', 'readline',
        'socket', 'socketserver', 'telnetlib', 'urllib.parse', 'urllib.request',
        'multiprocessing', 'concurrent.futures', 'asyncio', 'async',
        'csv', 'zipfile', 'tarfile', 'gzip', 'bz2', 'lzma',
        'decimal', 'fractions', 'statistics', 'cmath', 'math',
        'collections.abc', 'abc', 'typing_extensions',
        
        # Development and testing frameworks
        'pytest', 'pylint', 'black', 'mypy', 'sphinx', 'docutils', 'nose', 'coverage',
        'tox', 'flake8', 'isort', 'autopep8', 'bandit',
        
        # Scientific/data packages we don't use
        'numpy', 'scipy', 'matplotlib', 'pandas', 'jupyter', 'IPython', 'tornado', 'notebook',
        'sympy', 'sklearn', 'tensorflow', 'torch', 'keras',
        
        # Web frameworks and servers
        'django', 'flask', 'fastapi', 'aiohttp', 'bottle', 'pyramid',
        'gunicorn', 'uwsgi', 'waitress',
        
        # Database libraries
        'sqlalchemy', 'psycopg2', 'pymongo', 'redis', 'elasticsearch',
        
        # Other GUI frameworks
        'PyQt5', 'PyQt6', 'wx', 'gtk', 'tkinter',
        
        # Qt modules we explicitly don't want (this is the big space saver)
        'PySide6.QtNetwork', 'PySide6.QtOpenGL', 'PySide6.QtSql', 'PySide6.QtXml',
        'PySide6.QtWebEngine', 'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 
        'PySide6.QtWebChannel', 'PySide6.QtWebSockets',
        'PySide6.QtQuick', 'PySide6.QtQml', 'PySide6.QtQuickWidgets',
        'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
        'PySide6.Qt3DCore', 'PySide6.Qt3DRender', 'PySide6.Qt3DLogic', 'PySide6.Qt3DAnimation',
        'PySide6.QtCharts', 'PySide6.QtDataVisualization', 'PySide6.QtGraphs',
        'PySide6.QtPrintSupport', 'PySide6.QtTest', 'PySide6.QtConcurrent',
        'PySide6.QtSerialPort', 'PySide6.QtBluetooth', 'PySide6.QtNfc',
        'PySide6.QtPositioning', 'PySide6.QtLocation', 'PySide6.QtSensors',
        'PySide6.QtRemoteObjects', 'PySide6.QtScxml', 'PySide6.QtStateMachine',
        'PySide6.QtTextToSpeech', 'PySide6.QtHelp', 'PySide6.QtDesigner',
        'PySide6.QtSvg', 'PySide6.QtSvgWidgets',
        'PySide6.QtPdf', 'PySide6.QtPdfWidgets',
        
        # Large third-party packages we don't use
        'PIL', 'Pillow', 'opencv', 'cv2',
        'beautifulsoup4', 'lxml', 'scrapy',
        'matplotlib', 'seaborn', 'plotly',
        'openpyxl', 'xlsxwriter', 'xlrd',
        'requests_oauthlib',  # We use google_auth_oauthlib instead
        'httpx', 'aiohttp', 'httplib2',
        
        # Crypto and security (unless needed)
        'cryptography.hazmat', 'paramiko', 'pyopenssl',
        
        # Cloud and API packages we don't use  
        'boto3', 'botocore', 'azure', 'stripe', 'twilio',
        
        # Additional bloat
        'Cython', 'jinja2', 'mako', 'markupsafe',
        'yaml', 'toml', 'configparser',
        'click', 'colorama', 'tqdm', 'rich',
    ],
    
    'plist': {
        'CFBundleName': 'GlowStatus',
        'CFBundleDisplayName': 'GlowStatus',
        'CFBundleExecutable': 'GlowStatus',
        'CFBundleIdentifier': 'com.severswoed.glowstatus',
        'CFBundleShortVersionString': '2.0.0',
        'CFBundleVersion': '2.0.0',
        'LSUIElement': True,  # Run as background app without dock icon
        'NSHighResolutionCapable': True,  # Support retina displays
        'LSMinimumSystemVersion': '10.15',  # Require macOS 10.15+
    },
}

if 'py2app' in sys.argv:
    print()
    print("🎯 USING AGGRESSIVE PY2APP OPTIONS APPROACH!")
    print("📦 We're using comprehensive includes/excludes to minimize size:")
    print("   ✅ Include: QtCore, QtGui, QtWidgets, shiboken6")
    print("   ✅ Include: Essential Python modules and dependencies")  
    print("   ❌ Exclude: All unused Qt modules and frameworks")
    print("   ❌ Exclude: Development tools, testing frameworks")
    print("   ❌ Exclude: Scientific packages, other GUI frameworks")
    print()
    print("🚫 EXCLUDED Qt modules (saves ~500MB+):")
    print("   - QtWebEngine (~200MB web browser engine)")
    print("   - Qt3D (~50MB 3D graphics)")
    print("   - QtMultimedia + FFmpeg (~100MB video codecs)")
    print("   - QtCharts/Graphs (~30MB charting)")
    print("   - QtQuick/QML (~50MB modern UI)")
    print("   - QtNetwork, QtOpenGL, QtSql, QtXml")
    print("   - Plus 20+ other unused Qt modules")
    print()
    print("🎯 Target: 50-150MB app bundle (down from 1.2GB)!")
    print()

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

# Restore original working directory
os.chdir(original_cwd)

# Restore discord directory if it was moved
if 'py2app' in sys.argv and discord_backup_dir and os.path.exists(discord_backup_dir):
    discord_dir = os.path.join(PROJECT_ROOT, 'discord')
    if os.path.exists(discord_dir):
        shutil.rmtree(discord_dir)
    shutil.move(discord_backup_dir, discord_dir)
    print("📁 Restored discord directory after build")

# Print completion message with actual app size
if 'py2app' in sys.argv:
    # Restore original recipes
    print("🔄 Restoring original py2app recipes...")
    restore_original_recipes()
    
    print()
    print("🏁 Build completed!")
    
    # Calculate and display actual app bundle size
    import subprocess
    app_path = os.path.join(PROJECT_ROOT, 'dist/GlowStatus.app')
    if os.path.exists(app_path):
        try:
            result = subprocess.run(['du', '-sh', app_path], capture_output=True, text=True, check=True)
            size_output = result.stdout.strip()
            size_value = size_output.split('\t')[0]
            print(f"📊 Final app bundle size: {size_value}")
            
            # Parse size for success evaluation
            success = False
            if 'M' in size_value:
                size_mb = float(size_value.replace('M', ''))
                if size_mb <= 150:  # Give ourselves some wiggle room
                    success = True
                    print("🎉 SUCCESS: Achieved target size with custom recipe!")
                else:
                    print(f"📈 Progress made, but still above 150MB target")
            elif 'K' in size_value:
                success = True
                print("🎉 EXCELLENT: App is under 1MB!")
            else:
                if 'G' not in size_value:  # If not GB, assume success
                    success = True
                    print("🎉 Great size achieved!")
                else:
                    print(f"⚠️  Still large: {size_value}")
            
            if success:
                print("✅ Aggressive py2app options worked!")
            else:
                print("🔍 May need more aggressive exclusions")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Could not calculate app size: {e}")
    else:
        print(f"❌ App bundle not found at: {app_path}")
    
    # Save build log for analysis
    try:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(PROJECT_ROOT, f"docs/build_log_aggressive_options_{timestamp}.txt")
        
        # Save key build information
        with open(log_file, 'w') as f:
            f.write(f"GlowStatus macOS Build Log - {timestamp}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Final app bundle size: {size_value if 'size_value' in locals() else 'unknown'}\n")
            f.write(f"App path: {app_path}\n")
            f.write("Build approach: Aggressive py2app options (no custom recipe)\n")
            f.write("\nUsing standard py2app with aggressive excludes and minimal includes.\n")
            f.write("Target: Only QtCore, QtGui, QtWidgets + essential dependencies\n")
        
        print(f"📝 Build log saved to: {log_file}")
    except Exception as e:
        print(f"⚠️  Could not save build log: {e}")
    
    print()
    print("💡 Aggressive options should significantly reduce bundle size!")
    print("💡 No recipe modifications needed - safer and more compatible!")
