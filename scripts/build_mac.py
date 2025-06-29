#!/usr/bin/env python3
"""
Ultra-minimal macOS app builder for GlowStatus using py2app.
Optimized to avoid the massive PySide6 bloat.
Target: 50-100MB app bundle (not 1.35GB).
"""

from setuptools import setup
import glob
import sys
import os

# Import build helper functions from scripts directory
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
    print("🚫 DISABLING py2app PySide6 auto-recipe to prevent massive bloat!")
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
    print("🔧 Key optimization: Aggressive excludes + minimal includes to override PySide6 recipe!")
    print()

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

# Restore original working directory
os.chdir(original_cwd)

# Print completion message
if 'py2app' in sys.argv:
    print()
    print("🏁 Build completed!")
    print(f"📊 Check your app size:")
    print(f"   du -sh {os.path.join(PROJECT_ROOT, 'dist/GlowStatus.app')}")
    print()
    print("🎉 Should be much smaller than 1.35GB!")
