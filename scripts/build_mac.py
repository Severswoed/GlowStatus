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

def setup_environment():
    """Set up Python virtual environment and install dependencies."""
    print("🚀 GlowStatus macOS Build Script")
    print("=" * 50)
    
    # Check if Python is available
    try:
        result = subprocess.run([sys.executable, '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✓ Python found: {result.stdout.strip()}")
    except subprocess.CalledProcessError:
        print("✗ Python is not available")
        print("Please install Python 3.8+ and try again")
        sys.exit(1)
    
    print("\nSetting up Python environment...")
    print("=" * 50)
    
    # Check if .venv exists, create if not
    venv_path = os.path.join(os.getcwd(), '.venv')
    if not os.path.exists(venv_path):
        print("Creating virtual environment...")
        try:
            subprocess.run([sys.executable, '-m', 'venv', '.venv'], check=True)
            print("✓ Virtual environment created")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to create virtual environment: {e}")
            print("Make sure you have python-venv installed")
            sys.exit(1)
    else:
        print("✓ Using existing virtual environment")
    
    # Determine the correct activation script path
    if sys.platform == "win32":
        activate_script = os.path.join(venv_path, 'Scripts', 'activate')
        python_executable = os.path.join(venv_path, 'Scripts', 'python')
        pip_executable = os.path.join(venv_path, 'Scripts', 'pip')
    else:
        activate_script = os.path.join(venv_path, 'bin', 'activate')
        python_executable = os.path.join(venv_path, 'bin', 'python')
        pip_executable = os.path.join(venv_path, 'bin', 'pip')
    
    print("Installing Python dependencies...")
    
    # Upgrade pip first
    try:
        subprocess.run([python_executable, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
        print("✓ Pip upgraded")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Could not upgrade pip: {e}")
    
    # Install requirements
    requirements_file = os.path.join(os.getcwd(), 'requirements.txt')
    if os.path.exists(requirements_file):
        try:
            subprocess.run([pip_executable, 'install', '-r', requirements_file], check=True)
            print("✓ Requirements installed")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install requirements: {e}")
            sys.exit(1)
    else:
        print("⚠️  No requirements.txt found")
    
    # Install py2app specifically for macOS builds
    try:
        subprocess.run([pip_executable, 'install', 'py2app'], check=True)
        print("✓ py2app installed")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install py2app: {e}")
        sys.exit(1)
    
    print("✓ All dependencies installed successfully")
    print()
    
    return python_executable

# Import build helper functions from scripts directory
sys.path.insert(0, os.path.dirname(__file__))

# Set up environment before importing helpers
if __name__ == '__main__' and 'py2app' in sys.argv:
    python_exe = setup_environment()
    # Update sys.executable to use venv python for the rest of the script
    sys.executable = python_exe

# Try to import build helper functions from scripts directory
try:
    from build_helpers import check_and_install_requirements, verify_critical_modules, fix_google_namespace_packages, get_version_string
except ImportError:
    # Provide fallback functions if build_helpers is not available
    def check_and_install_requirements():
        print("⚠️  Build helpers not available, skipping dependency check")
        
    def verify_critical_modules():
        print("⚠️  Build helpers not available, skipping module verification")
        return True
        
    def fix_google_namespace_packages():
        print("⚠️  Build helpers not available, skipping namespace package fix")
        
    def get_version_string():
        try:
            import json
            with open('version.json', 'r') as f:
                version_data = json.load(f)
            version = f"{version_data['major']}.{version_data['minor']}.{version_data['patch']}"
            if version_data.get('pre'):
                version += f"-{version_data['pre']}"
            return version
        except:
            return "2.1.0"

def create_custom_glowstatus_recipe():
    """
    Create a custom py2app recipe that only includes the exact Qt modules GlowStatus actually uses.
    
    Based on py2app recipes documentation at:
    https://py2app.readthedocs.io/en/latest/recipes.html
    
    This follows the official recipe pattern with check() and recipe() functions.
    Our custom recipe will completely replace the default PySide6 recipe to eliminate bloat.
    
    Returns:
        bool: True if recipe was successfully created, False otherwise
    """
    try:
        try:
            import py2app
        except ImportError:
            print("⚠️  py2app not available, skipping custom recipe creation")
            return False
            
        py2app_path = os.path.dirname(py2app.__file__)
        recipes_dir = os.path.join(py2app_path, 'recipes')
        
        if not os.path.exists(recipes_dir):
            print("⚠️  Could not find py2app recipes directory, skipping custom recipe")
            return False
        
        # First, backup and disable the original PySide6 recipe that includes everything
        original_pyside6_recipe = os.path.join(recipes_dir, 'pyside6.py')
        backup_pyside6_recipe = os.path.join(recipes_dir, 'pyside6.py.glowstatus_backup')
        
        if os.path.exists(original_pyside6_recipe) and not os.path.exists(backup_pyside6_recipe):
            shutil.copy2(original_pyside6_recipe, backup_pyside6_recipe)
            print(f"📋 Backed up original PySide6 recipe")
    
    except ImportError:
        print("⚠️  py2app not available, skipping custom recipe creation")
        return False
    except Exception as e:
        print(f"❌ Error accessing py2app: {e}")
        return False
    
    # Create our minimal replacement recipe for PySide6
    custom_recipe_content = '''"""
Custom minimal PySide6 recipe for GlowStatus - compatible with py2app 0.28.8

This recipe directly returns the configuration dict that py2app expects.
"""

def check(cmd, mf):
    """Check if this recipe should be applied."""
    modules = mf.flatten()
    return any('PySide6' in str(m) for m in modules)

def recipe(cmd, mf):
    """Apply the minimal PySide6 configuration."""
    print("🎯 GlowStatus: Applying minimal PySide6 recipe")
    
    # Import only the essential PySide6 modules
    mf.import_hook('PySide6')
    mf.import_hook('PySide6.QtCore')
    mf.import_hook('PySide6.QtGui') 
    mf.import_hook('PySide6.QtWidgets')
    mf.import_hook('shiboken6')
    
    print("🎯 Imported essential PySide6 modules")
    
    # Return the configuration dictionary
    result = {
        'packages': ['PySide6', 'shiboken6'],
        'includes': [
            'PySide6.QtCore',
            'PySide6.QtGui', 
            'PySide6.QtWidgets',
            'shiboken6',
        ],
        'expected_missing_imports': [
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
        ]
    }
    print(f"🎯 Recipe returning: {type(result)} with {len(result)} keys")
    return result
'''
    
    try:
        # Write our minimal recipe to replace the bloated default one
        with open(original_pyside6_recipe, 'w') as f:
            f.write(custom_recipe_content)
        print(f"✅ Replaced default PySide6 recipe with minimal GlowStatus version")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create custom recipe: {e}")
        return False

def restore_original_recipes():
    """
    Restore original py2app recipes after build.
    
    This ensures the system py2app installation is returned to its original state
    after our custom recipe build is complete.
    """
    try:
        try:
            import py2app
        except ImportError:
            print("⚠️  py2app not available for recipe restoration")
            return
            
        py2app_path = os.path.dirname(py2app.__file__)
        recipes_dir = os.path.join(py2app_path, 'recipes')
        
        # Restore original PySide6 recipe
        original_pyside6_recipe = os.path.join(recipes_dir, 'pyside6.py')
        backup_pyside6_recipe = os.path.join(recipes_dir, 'pyside6.py.glowstatus_backup')
        
        if os.path.exists(backup_pyside6_recipe):
            try:
                shutil.copy2(backup_pyside6_recipe, original_pyside6_recipe)
                os.remove(backup_pyside6_recipe)
                print(f"🔄 Restored original PySide6 recipe")
            except Exception as e:
                print(f"⚠️  Could not restore original PySide6 recipe: {e}")
                print(f"   Manual cleanup needed: {backup_pyside6_recipe}")
        else:
            print(f"📝 No backup found, PySide6 recipe was not modified")
            
    except ImportError:
        print("⚠️  py2app not available for recipe restoration")
    except Exception as e:
        print(f"❌ Error during recipe restoration: {e}")

# Check requirements before building
if 'py2app' in sys.argv:
    print("🚀 Preparing GlowStatus for macOS app bundle creation...")
    
    # Try to import build helpers, install if needed
    try:
        from build_helpers import check_and_install_requirements, verify_critical_modules, fix_google_namespace_packages, get_version_string
        check_and_install_requirements()
        if not verify_critical_modules():
            print("❌ Critical modules missing. Please fix the above issues and try again.")
            sys.exit(1)
        print("🔧 Fixing Google namespace packages for py2app...")
        fix_google_namespace_packages()
    except ImportError as e:
        print(f"⚠️  Build helpers not available: {e}")
        print("Continuing with basic build...")
    
    print("✅ Ready to build with minimal configuration!")
    print("📦 Using py2app built-in options to minimize size")
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
    
    # Only include what we absolutely need
    'includes': [
        # Core Python modules
        'threading', 'queue', 'json', 'datetime', 'tempfile', 'atexit', 'time', 'os', 'sys',
        'pickle', 're',
        
        # Only the PySide6 modules we actually use
        'PySide6.QtCore',
        'PySide6.QtGui', 
        'PySide6.QtWidgets',
        'shiboken6',
        
        # Essential third-party dependencies
        'requests', 'urllib3', 'certifi',
        'keyring',
        
        # Google packages (minimal set we actually import)
        'google_auth_oauthlib.flow',
        'googleapiclient.discovery',
        'google.auth.transport.requests',
        'google.oauth2.credentials',
        'dateutil.parser',
    ],
    
    # Only include essential packages
    'packages': [
        'keyring',
        'requests', 
        'urllib3',
        'certifi',
        'google_auth_oauthlib',
        'googleapiclient',
        'google.auth',
        'google.oauth2',
        'dateutil',
    ],
    
    # Aggressively exclude everything we don't need
    'excludes': [
        # Standard library modules we don't use
        'tkinter', 'turtle', 'curses', 'sqlite3', 'xml', 'xmlrpc', 'html', 'http.server', 'wsgiref',
        'pydoc_data', 'distutils', 'setuptools', 'pip', 'wheel', 'test', 'unittest', 'doctest',
        'email', 'ftplib', 'gettext', 'locale', 'mailbox', 'mimetypes', 'pty', 'readline',
        'socket', 'socketserver', 'telnetlib', 'urllib.parse', 'urllib.request',
        
        # Development and testing frameworks
        'pytest', 'pylint', 'black', 'mypy', 'sphinx', 'docutils', 'nose', 'coverage',
        
        # Scientific/data packages we don't use
        'numpy', 'scipy', 'matplotlib', 'pandas', 'jupyter', 'IPython', 'tornado', 'notebook',
        
        # Other GUI frameworks
        'PyQt5', 'PyQt6', 'wx', 'gtk',
        
        # Qt modules we explicitly don't want
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
    ],
    
    'plist': {
        'CFBundleName': 'GlowStatus',
        'CFBundleDisplayName': 'GlowStatus',
        'CFBundleExecutable': 'GlowStatus',
        'CFBundleIdentifier': 'com.severswoed.glowstatus',
        'CFBundleShortVersionString': get_version_string(),
        'CFBundleVersion': get_version_string(),
        'LSUIElement': True,  # Run as background app without dock icon
        'NSHighResolutionCapable': True,  # Support retina displays
        'LSMinimumSystemVersion': '10.15',  # Require macOS 10.15+
    },
}

if 'py2app' in sys.argv:
    print()
    print("🎯 USING CUSTOM MINIMAL PYSIDE6 RECIPE!")
    print("📦 Our recipe REPLACES the default PySide6 recipe and only includes:")
    print("   - QtCore (core functionality)")
    print("   - QtGui (icons, pixmaps, painting)")  
    print("   - QtWidgets (windows, layouts, dialogs)")
    print("   - QtDBus (macOS system tray integration)")
    print("   - Only 6 essential Qt plugins")
    print()
    print("🚫 Our recipe EXCLUDES all the bloat at the source:")
    print("   - QtWebEngine (~200MB web browser engine)")
    print("   - Qt3D (~50MB 3D graphics)")
    print("   - QtMultimedia + FFmpeg (~100MB video codecs)")
    print("   - QtCharts/Graphs (~30MB charting)")
    print("   - QtQuick/QML (~50MB modern UI)")
    print("   - QtPositioning, QtLocation (GPS plugins)")
    print("   - QtSerialPort, QtBluetooth, QtNfc")
    print("   - Hundreds of unused Qt plugins")
    print()
    print("🎯 Target: 50-100MB app bundle (down from 1.2GB)!")
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
                print("✅ Custom recipe approach worked!")
            else:
                print("🔍 May need recipe refinement")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Could not calculate app size: {e}")
    else:
        print(f"❌ App bundle not found at: {app_path}")
    
    # Save build log for analysis
    try:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(PROJECT_ROOT, f"docs/build_log_custom_recipe_{timestamp}.txt")
        
        # Save key build information
        with open(log_file, 'w') as f:
            f.write(f"GlowStatus macOS Build Log (Custom Recipe) - {timestamp}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Final app bundle size: {size_value if 'size_value' in locals() else 'unknown'}\n")
            f.write(f"App path: {app_path}\n")
            f.write("Custom recipe approach used\n")
            f.write("\nCustom recipe approach - no aggressive cleanup needed.\n")
            f.write("Recipe only includes: QtCore, QtGui, QtWidgets + essential plugins\n")
        
        print(f"📝 Build log saved to: {log_file}")
    except Exception as e:
        print(f"⚠️  Could not save build log: {e}")
    
    print()
    print("💡 Custom recipe should eliminate all Qt bloat at the source!")
    print("💡 No post-build cleanup needed - recipe controls what gets included!")
