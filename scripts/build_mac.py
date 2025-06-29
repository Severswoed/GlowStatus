#!/usr/bin/env python3
"""
Ultra-minimal macOS app builder for GlowStatus using py2app.
Optimized to avoid the massive PySide6 bloat.
Target: 50-100MB app bundle (not 1.35GB).

CRITICAL FIX: Completely bypass py2app's PySide6 recipe system that auto-includes all Qt modules.
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

def create_minimal_pyside6_recipe():
    """
    Create a custom minimal PySide6 recipe that overrides py2app's bloated default recipe.
    This prevents py2app from auto-including all Qt modules.
    """
    # Find py2app's recipe directory
    import py2app
    py2app_path = os.path.dirname(py2app.__file__)
    recipes_dir = os.path.join(py2app_path, 'recipes')
    
    if not os.path.exists(recipes_dir):
        print("⚠️  Could not find py2app recipes directory, skipping recipe override")
        return False
    
    # Create a minimal PySide6 recipe that does nothing
    pyside6_recipe_path = os.path.join(recipes_dir, 'pyside6.py')
    
    # Backup original recipe if it exists
    if os.path.exists(pyside6_recipe_path):
        backup_path = pyside6_recipe_path + '.original_backup'
        if not os.path.exists(backup_path):
            shutil.copy2(pyside6_recipe_path, backup_path)
            print(f"📋 Backed up original PySide6 recipe to: {backup_path}")
    
    # Create our minimal recipe that doesn't auto-include everything
    minimal_recipe = '''"""
Minimal PySide6 recipe for py2app - prevents auto-inclusion of all Qt modules.
Only includes what we explicitly specify in the build script.
"""

def check(cmd, mf):
    """Check if PySide6 is used - we handle this manually"""
    # Return False to prevent this recipe from running automatically
    return False

def recipe(cmd, mf):
    """Minimal recipe that does nothing - we handle PySide6 includes manually"""
    # Do nothing - let our explicit includes/excludes handle everything
    pass
'''
    
    try:
        with open(pyside6_recipe_path, 'w') as f:
            f.write(minimal_recipe)
        print(f"✅ Created minimal PySide6 recipe at: {pyside6_recipe_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create minimal recipe: {e}")
        return False

def analyze_qt_frameworks(app_path):
    """
    Analyze what Qt frameworks are included in the app bundle and their sizes.
    This helps identify what's causing the bloat.
    """
    frameworks_path = os.path.join(app_path, 'Contents', 'Frameworks')
    if not os.path.exists(frameworks_path):
        print("📁 No Frameworks directory found")
        return
    
    print("🔍 Analyzing Qt frameworks in app bundle:")
    total_qt_size = 0
    
    for item in os.listdir(frameworks_path):
        if item.startswith('Qt') and item.endswith('.framework'):
            framework_path = os.path.join(frameworks_path, item)
            try:
                result = subprocess.run(['du', '-sm', framework_path], capture_output=True, text=True)
                if result.returncode == 0:
                    size_mb = int(result.stdout.split('\t')[0])
                    total_qt_size += size_mb
                    if size_mb > 10:  # Only show frameworks larger than 10MB
                        print(f"   📦 {item}: {size_mb}MB")
            except:
                print(f"   📦 {item}: [size unknown]")
    
    if total_qt_size > 0:
        print(f"📊 Total Qt frameworks size: {total_qt_size}MB")
    else:
        print("✅ No large Qt frameworks found!")

def manual_qt_cleanup(app_path):
    """
    Manual cleanup of unwanted Qt frameworks as a backup if recipe override doesn't work perfectly.
    This removes large Qt frameworks that we definitely don't need.
    """
    frameworks_path = os.path.join(app_path, 'Contents', 'Frameworks')
    if not os.path.exists(frameworks_path):
        print("📁 No Frameworks directory found - skipping manual cleanup")
        return False
    
    # List of Qt frameworks to remove (we only need Core, Gui, Widgets)
    unwanted_frameworks = [
        'QtWebEngine', 'QtWebEngineCore', 'QtWebEngineWidgets', 'QtWebEngineQuick',
        'QtWebView', 'QtWebSockets', 'QtWebChannel',
        'Qt3DCore', 'Qt3DRender', 'Qt3DInput', 'Qt3DLogic', 'Qt3DExtras', 'Qt3DAnimation',
        'QtQuick', 'QtQuickControls2', 'QtQuickWidgets', 'QtQuickParticles',
        'QtQml', 'QtQmlCore', 'QtQmlNetwork', 'QtQmlModels',
        'QtMultimedia', 'QtMultimediaWidgets', 'QtSpatialAudio',
        'QtCharts', 'QtDataVisualization', 'QtGraphs',
        'QtNetwork', 'QtOpenGL', 'QtSql', 'QtXml', 'QtTest', 'QtConcurrent',
        'QtBluetooth', 'QtNfc', 'QtPositioning', 'QtLocation', 'QtSensors',
        'QtDesigner', 'QtUiTools', 'QtSvg', 'QtPrintSupport',
    ]
    
    removed_count = 0
    removed_size = 0
    
    for framework in unwanted_frameworks:
        framework_path = os.path.join(frameworks_path, f'{framework}.framework')
        if os.path.exists(framework_path):
            try:
                # Get size before removal
                result = subprocess.run(['du', '-sm', framework_path], capture_output=True, text=True)
                if result.returncode == 0:
                    size_mb = int(result.stdout.split('\t')[0])
                    removed_size += size_mb
                
                shutil.rmtree(framework_path)
                removed_count += 1
                print(f"🗑️  Removed {framework}.framework ({size_mb}MB)")
            except Exception as e:
                print(f"⚠️  Could not remove {framework}: {e}")
    
    if removed_count > 0:
        print(f"✅ Manual cleanup complete: Removed {removed_count} frameworks (~{removed_size}MB)")
        return True
    else:
        print("📝 No unwanted frameworks found - recipe override may have worked!")
        return False

def restore_original_pyside6_recipe():
    """Restore the original PySide6 recipe after build"""
    import py2app
    py2app_path = os.path.dirname(py2app.__file__)
    recipes_dir = os.path.join(py2app_path, 'recipes')
    
    pyside6_recipe_path = os.path.join(recipes_dir, 'pyside6.py')
    backup_path = pyside6_recipe_path + '.original_backup'
    
    if os.path.exists(backup_path):
        try:
            shutil.copy2(backup_path, pyside6_recipe_path)
            print(f"🔄 Restored original PySide6 recipe from backup")
        except Exception as e:
            print(f"⚠️  Could not restore original recipe: {e}")
    elif os.path.exists(pyside6_recipe_path):
        try:
            os.remove(pyside6_recipe_path)
            print(f"🗑️  Removed minimal PySide6 recipe")
        except Exception as e:
            print(f"⚠️  Could not remove minimal recipe: {e}")

# Check requirements before building
if 'py2app' in sys.argv:
    print("🚀 Preparing GlowStatus for macOS app bundle creation...")
    check_and_install_requirements()
    if not verify_critical_modules():
        print("❌ Critical modules missing. Please fix the above issues and try again.")
        sys.exit(1)
    print("🔧 Fixing Google namespace packages for py2app...")
    fix_google_namespace_packages()
    
    # CRITICAL: Override py2app's bloated PySide6 recipe
    print("🔥 OVERRIDING py2app's PySide6 recipe to prevent auto-inclusion of all Qt modules...")
    recipe_success = create_minimal_pyside6_recipe()
    if recipe_success:
        print("✅ PySide6 recipe override successful!")
    else:
        print("⚠️  Recipe override failed - will rely on aggressive excludes")
    
    print("✅ Ready to build!")
    print()

# Get the project root directory (parent of scripts directory)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Change to project root directory for the build process
original_cwd = os.getcwd()
os.chdir(PROJECT_ROOT)
print(f"📁 Changed working directory to: {PROJECT_ROOT}")

APP = ['src/tray_app.py']
DATA_FILES = [
    ('img', glob.glob('img/*')),
    ('config', glob.glob('config/*')),
    ('resources', ['resources/client_secret.json']),
]

OPTIONS = {
    'iconfile': 'img/GlowStatus.icns',
    
    # CRITICAL SIZE OPTIMIZATIONS
    'argv_emulation': False,
    'site_packages': False,  # Don't include entire site-packages
    'optimize': 2,  # Maximum bytecode optimization
    'strip': True,  # Strip debug symbols
    'compressed': True,  # Compress the bundle
    'no_chdir': True,  # Don't change working directory
    
    # Only include what we absolutely need
    'includes': [
        # Core Python modules only
        'threading', 'queue', 'json', 'datetime', 'tempfile', 'atexit', 'time', 'os', 'sys',
        
        # ONLY the PySide6 modules we actually use
        'PySide6.QtCore',
        'PySide6.QtGui', 
        'PySide6.QtWidgets',
        'shiboken6',
        
        # Only essential dependencies
        'requests', 'urllib3', 'certifi',
        'keyring',
        
        # Google packages (minimal)
        'google_auth_oauthlib.flow',
        'googleapiclient.discovery',
        'google.auth.transport.requests',
        'google.oauth2.credentials',
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
    ],
    
    # ULTRA AGGRESSIVE EXCLUSIONS: Everything we don't need  
    'excludes': [
        # Remove all other PySide6 modules - we only need Core, Gui, Widgets
        'PySide6.QtNetwork', 'PySide6.QtOpenGL', 'PySide6.QtSql', 'PySide6.QtXml',
        'PySide6.QtTest', 'PySide6.QtConcurrent', 'PySide6.QtDBus', 'PySide6.QtHelp',
        'PySide6.QtPrintSupport', 'PySide6.QtSvg', 'PySide6.QtSvgWidgets',
        
        # MASSIVE PySide6 components we definitely don't need
        'PySide6.QtWebEngine', 'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngineQuick',
        'PySide6.QtWebView', 'PySide6.QtWebSockets', 'PySide6.QtWebChannel', 'PySide6.QtWebChannelQuick',
        
        # All Qt3D frameworks
        'PySide6.Qt3D', 'PySide6.Qt3DCore', 'PySide6.Qt3DRender', 'PySide6.Qt3DInput', 'PySide6.Qt3DLogic', 
        'PySide6.Qt3DExtras', 'PySide6.Qt3DAnimation', 'PySide6.Qt3DQuick', 'PySide6.Qt3DQuickRender',
        'PySide6.Qt3DQuickInput', 'PySide6.Qt3DQuickExtras', 'PySide6.Qt3DQuickAnimation', 'PySide6.Qt3DQuickScene2D',
        
        # All QtQuick3D frameworks  
        'PySide6.QtQuick3D', 'PySide6.QtQuick3DRuntimeRender', 'PySide6.QtQuick3DUtils', 'PySide6.QtQuick3DHelpers',
        'PySide6.QtQuick3DEffects', 'PySide6.QtQuick3DParticles', 'PySide6.QtQuick3DAssetImport', 'PySide6.QtQuick3DAssetUtils',
        'PySide6.QtQuick3DGlslParser', 'PySide6.QtQuick3DHelpersImpl', 'PySide6.QtQuick3DIblBaker', 'PySide6.QtQuick3DSpatialAudio',
        'PySide6.QtQuick3DParticleEffects', 'PySide6.QtQuick3DXr',
        
        # All multimedia frameworks
        'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets', 'PySide6.QtMultimediaQuick', 'PySide6.QtSpatialAudio',
        
        # All charting/visualization frameworks
        'PySide6.QtCharts', 'PySide6.QtChartsQml', 'PySide6.QtDataVisualization', 'PySide6.QtDataVisualizationQml',
        'PySide6.QtGraphs', 'PySide6.QtGraphsWidgets',
        
        # All QML/Quick frameworks (we only use QtWidgets)
        'PySide6.QtQuick', 'PySide6.QtQuickControls2', 'PySide6.QtQuickWidgets', 'PySide6.QtQuickTemplates2',
        'PySide6.QtQuickLayouts', 'PySide6.QtQuickParticles', 'PySide6.QtQuickShapes', 'PySide6.QtQuickTest',
        'PySide6.QtQuickEffects', 'PySide6.QtQuickTimeline', 'PySide6.QtQuickTimelineBlendTrees', 'PySide6.QtQuickVectorImage',
        'PySide6.QtQuickVectorImageGenerator', 'PySide6.QtQuickDialogs2', 'PySide6.QtQuickDialogs2Utils', 'PySide6.QtQuickDialogs2QuickImpl',
        
        # All style implementations
        'PySide6.QtQuickControls2Basic', 'PySide6.QtQuickControls2BasicStyleImpl', 'PySide6.QtQuickControls2Fusion',
        'PySide6.QtQuickControls2FusionStyleImpl', 'PySide6.QtQuickControls2Imagine', 'PySide6.QtQuickControls2ImagineStyleImpl',
        'PySide6.QtQuickControls2Material', 'PySide6.QtQuickControls2MaterialStyleImpl', 'PySide6.QtQuickControls2Universal',
        'PySide6.QtQuickControls2UniversalStyleImpl', 'PySide6.QtQuickControls2MacOSStyleImpl', 'PySide6.QtQuickControls2IOSStyleImpl',
        'PySide6.QtQuickControls2FluentWinUI3StyleImpl', 'PySide6.QtQuickControls2Impl',
        
        # All QML framework components
        'PySide6.QtQml', 'PySide6.QtQmlCore', 'PySide6.QtQmlNetwork', 'PySide6.QtQmlModels', 'PySide6.QtQmlWorkerScript',
        'PySide6.QtQmlCompiler', 'PySide6.QtQmlMeta', 'PySide6.QtQmlLocalStorage', 'PySide6.QtQmlXmlListModel',
        
        # Designer and development tools
        'PySide6.QtDesigner', 'PySide6.QtDesignerComponents', 'PySide6.QtUiTools',
        
        # Hardware/connectivity we don't use
        'PySide6.QtBluetooth', 'PySide6.QtNfc', 'PySide6.QtPositioning', 'PySide6.QtPositioningQuick',
        'PySide6.QtLocation', 'PySide6.QtSensors', 'PySide6.QtSensorsQuick', 'PySide6.QtSerialPort', 'PySide6.QtSerialBus',
        
        # Advanced features we don't use
        'PySide6.QtNetworkAuth', 'PySide6.QtRemoteObjects', 'PySide6.QtRemoteObjectsQml', 'PySide6.QtScxml', 'PySide6.QtScxmlQml',
        'PySide6.QtStateMachine', 'PySide6.QtStateMachineQml', 'PySide6.QtTextToSpeech', 'PySide6.QtVirtualKeyboard',
        'PySide6.QtVirtualKeyboardQml', 'PySide6.QtVirtualKeyboardSettings', 'PySide6.QtPdf', 'PySide6.QtPdfWidgets',
        'PySide6.QtPdfQuick', 'PySide6.QtHttpServer', 'PySide6.QtShaderTools',
        
        # All Labs components (experimental)
        'PySide6.QtLabsPlatform', 'PySide6.QtLabsAnimation', 'PySide6.QtLabsFolderListModel', 'PySide6.QtLabsQmlModels',
        'PySide6.QtLabsSettings', 'PySide6.QtLabsSharedImage', 'PySide6.QtLabsWavefrontMesh',
        
        # Standard library modules we don't use
        'tkinter', 'turtle', 'curses', 'sqlite3', 'multiprocessing', 'xml', 'xmlrpc', 'html', 'http.server', 'wsgiref',
        'pydoc_data', 'distutils', 'setuptools', 'pip', 'wheel', 'test', 'unittest', 'doctest',
        
        # Development and testing frameworks
        'pytest', 'pylint', 'black', 'mypy', 'sphinx', 'docutils', 'nose', 'coverage',
        
        # Scientific/data packages we don't use
        'numpy', 'scipy', 'matplotlib', 'pandas', 'jupyter', 'IPython', 'tornado', 'notebook',
        
        # Other GUI frameworks
        'PyQt5', 'PyQt6', 'wx', 'gtk',
        
        # FFmpeg and multimedia codecs (these are HUGE)
        'libavcodec', 'libavformat', 'libavutil', 'libswscale', 'libswresample',
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
    print("🚫 USING CUSTOM MINIMAL PySide6 RECIPE - no auto-bloat!")
    print("📦 Only including essential PySide6 components:")
    print("   - PySide6.QtCore (core functionality)")
    print("   - PySide6.QtGui (GUI basics)")  
    print("   - PySide6.QtWidgets (widgets for tray)")
    print("   - shiboken6 (Python-Qt bridge)")
    print()
    print("🔥 EXCLUDING massive components:")
    print("   - QtWebEngine (~200MB web browser)")
    print("   - Qt3D (~50MB 3D graphics)")
    print("   - QtMultimedia + FFmpeg (~100MB codecs)")
    print("   - QtCharts/Graphs (~30MB charting)")
    print("   - QtQuick/QML (~50MB modern UI)")
    print("   - All style implementations (~20MB)")
    print()
    print("🔧 Key optimization: Custom recipe override + aggressive excludes!")
    print()

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

# Restore original working directory
os.chdir(original_cwd)

# Print completion message with actual app size
if 'py2app' in sys.argv:
    # Restore original PySide6 recipe
    print("🔄 Restoring original py2app PySide6 recipe...")
    restore_original_pyside6_recipe()
    
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
            print(f"📊 Initial app bundle size: {size_value}")
            
            # Analyze what's included before cleanup
            analyze_qt_frameworks(app_path)
            
            # Check if we need manual cleanup
            needs_cleanup = False
            if 'G' in size_value:
                size_gb = float(size_value.replace('G', ''))
                if size_gb > 0.5:  # If larger than 500MB, try manual cleanup
                    needs_cleanup = True
            elif 'M' in size_value:
                size_mb = float(size_value.replace('M', ''))
                if size_mb > 200:  # If larger than 200MB, try manual cleanup
                    needs_cleanup = True
            
            # Perform manual cleanup if needed
            if needs_cleanup:
                print("🧹 Size still large - attempting manual Qt framework cleanup...")
                cleanup_success = manual_qt_cleanup(app_path)
                
                if cleanup_success:
                    # Recalculate size after cleanup
                    result = subprocess.run(['du', '-sh', app_path], capture_output=True, text=True, check=True)
                    new_size_output = result.stdout.strip()
                    new_size_value = new_size_output.split('\t')[0]
                    print(f"📊 Final app bundle size after cleanup: {new_size_value}")
                    size_value = new_size_value
            
            # Parse final size for comparison
            if 'G' in size_value:
                size_gb = float(size_value.replace('G', ''))
                if size_gb > 1.0:
                    print(f"⚠️  WARNING: App is still {size_value} - target is 50-100MB!")
                    print("🔍 May need deeper Qt library investigation or alternative approach")
                else:
                    print("✅ Good progress!")
            elif 'M' in size_value:
                size_mb = float(size_value.replace('M', ''))
                if size_mb <= 100:
                    print("🎉 SUCCESS: Achieved target size!")
                else:
                    print(f"📈 Progress made, but still above 100MB target")
            else:
                print("🎉 Excellent size!")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Could not calculate app size: {e}")
    else:
        print(f"❌ App bundle not found at: {app_path}")
    
    # Save build log for analysis
    try:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(PROJECT_ROOT, f"docs/build_log_{timestamp}.txt")
        
        # Save key build information
        with open(log_file, 'w') as f:
            f.write(f"GlowStatus macOS Build Log - {timestamp}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Final app bundle size: {size_value}\n")
            f.write(f"App path: {app_path}\n")
            f.write(f"Recipe override used: {recipe_success}\n")
            f.write(f"Manual cleanup performed: {cleanup_success if 'cleanup_success' in locals() else False}\n")
            f.write("\nBuild completed successfully.\n")
        
        print(f"📝 Build log saved to: {log_file}")
    except Exception as e:
        print(f"⚠️  Could not save build log: {e}")
    
    print()
