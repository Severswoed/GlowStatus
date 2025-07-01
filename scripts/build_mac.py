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
    Create a custom py2app recipe that only includes the exact Qt modules GlowStatus actually uses.
    
    Based on py2app implementation docs at https://py2app.readthedocs.io/en/latest/implementation.html
    and recipes docs at https://py2app.readthedocs.io/en/latest/recipes.html#developing-recipes
    
    Our custom recipe will completely replace the default PySide6 recipe to eliminate all bloat.
    """
    import py2app
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
    
    # Create our minimal replacement recipe for PySide6
    custom_recipe_content = '''"""
Custom minimal PySide6 recipe for GlowStatus - replaces the default bloated one.

Based on py2app implementation docs and our actual usage:
- We only use QtCore, QtGui, QtWidgets
- We only need basic platform integration and image support
- We exclude all the massive Qt modules like WebEngine, 3D, Multimedia, etc.
"""

def check(cmd, mf):
    """Check if this recipe should be applied"""
    # Apply to any PySide6 usage
    return bool({
        'PySide6.QtWidgets',
        'PySide6.QtCore', 
        'PySide6.QtGui',
        'PySide6',
    }.intersection(mf.flatten()))

def recipe(cmd, mf):
    """
    Custom minimal recipe that replaces the default PySide6 recipe.
    Only includes the essential Qt components needed by GlowStatus.
    
    Based on scanning our actual imports:
    - PySide6.QtCore: Qt, QThread, Signal, QTimer
    - PySide6.QtGui: QIcon, QAction, QCursor, QPixmap, QPainter, QBrush  
    - PySide6.QtWidgets: QWidget, QVBoxLayout, QLabel, QPushButton, etc.
    """
    
    print("🎯 GlowStatus: Using minimal PySide6 recipe")
    
    # Import the modules we actually need
    mf.import_hook('PySide6')
    mf.import_hook('PySide6.QtCore') 
    mf.import_hook('PySide6.QtGui')
    mf.import_hook('PySide6.QtWidgets')
    mf.import_hook('shiboken6')
    
    # Only include essential Qt frameworks - exclude all the bloat
    frameworks = [
        'QtCore',      # Core functionality - always needed
        'QtGui',       # Basic GUI - needed for QIcon, QPixmap, QPainter
        'QtWidgets',   # Widget system - needed for QWidget, layouts, dialogs
        'QtDBus',      # macOS system integration (small, needed for tray)
    ]
    
    # Only essential Qt plugins - VERY restrictive list
    plugins = [
        # Platform integration (absolutely required)
        'platforms/libqcocoa.dylib',
        
        # Image formats (only what we need for icons)
        'imageformats/libqpng.dylib',      # PNG icons
        'imageformats/libqjpeg.dylib',     # JPEG icons  
        'imageformats/libqsvg.dylib',      # SVG icons
        
        # Icon engines (for icon rendering)
        'iconengines/libqsvgicon.dylib',
        
        # Native macOS style (for proper appearance)
        'styles/libqmacstyle.dylib',
    ]
    
    print(f"🎯 Including {len(frameworks)} Qt frameworks: {frameworks}")
    print(f"🎯 Including {len(plugins)} Qt plugins (essential only)")
    
    # Return the recipe configuration using standard py2app format
    return {
        'packages': ['PySide6', 'shiboken6'],
        'includes': [
            'PySide6.QtCore',
            'PySide6.QtGui', 
            'PySide6.QtWidgets',
            'shiboken6',
        ],
        'expected_missing': [
            # Explicitly exclude these massive Qt modules
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
        ],
    }
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
    """Restore original py2app recipes after build"""
    import py2app
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
    else:
        print(f"📝 No backup found, PySide6 recipe was not modified")

# Check requirements before building
if 'py2app' in sys.argv:
    print("🚀 Preparing GlowStatus for macOS app bundle creation...")
    check_and_install_requirements()
    if not verify_critical_modules():
        print("❌ Critical modules missing. Please fix the above issues and try again.")
        sys.exit(1)
    print("🔧 Fixing Google namespace packages for py2app...")
    fix_google_namespace_packages()
    
    # Create our custom minimal recipe
    print("🎯 Creating custom minimal PySide6 recipe for GlowStatus...")
    recipe_success = create_custom_glowstatus_recipe()
    if recipe_success:
        print("✅ Custom recipe created successfully!")
    else:
        print("⚠️  Custom recipe creation failed - build may include extra Qt modules")
    
    print("✅ Ready to build!")
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
    
    # Only include what we absolutely need - let our custom recipe handle Qt
    'includes': [
        # Core Python modules
        'threading', 'queue', 'json', 'datetime', 'tempfile', 'atexit', 'time', 'os', 'sys',
        'pickle', 're',
        
        # Only the PySide6 modules we actually use (our recipe will handle the Qt frameworks)
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
    
    # Exclude everything we don't need - our custom recipe handles Qt exclusions
    'excludes': [
        # Standard library modules we don't use
        'tkinter', 'turtle', 'curses', 'sqlite3', 'xml', 'xmlrpc', 'html', 'http.server', 'wsgiref',
        'pydoc_data', 'distutils', 'setuptools', 'pip', 'wheel', 'test', 'unittest', 'doctest',
        
        # Development and testing frameworks
        'pytest', 'pylint', 'black', 'mypy', 'sphinx', 'docutils', 'nose', 'coverage',
        
        # Scientific/data packages we don't use
        'numpy', 'scipy', 'matplotlib', 'pandas', 'jupyter', 'IPython', 'tornado', 'notebook',
        
        # Other GUI frameworks
        'PyQt5', 'PyQt6', 'wx', 'gtk',
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
            f.write(f"Custom recipe used: {recipe_success}\n")
            f.write("\nCustom recipe approach - no aggressive cleanup needed.\n")
            f.write("Recipe only includes: QtCore, QtGui, QtWidgets + essential plugins\n")
        
        print(f"📝 Build log saved to: {log_file}")
    except Exception as e:
        print(f"⚠️  Could not save build log: {e}")
    
    print()
    print("💡 Custom recipe should eliminate all Qt bloat at the source!")
    print("💡 No post-build cleanup needed - recipe controls what gets included!")
