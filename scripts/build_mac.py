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
            self.closed = False
            
        def write(self, message):
            self.terminal.write(message)
            if not self.closed:
                self.log.write(message)
                self.log.flush()
            
        def flush(self):
            self.terminal.flush()
            if not self.closed:
                self.log.flush()
        
        def close(self):
            if not self.closed:
                self.log.close()
                self.closed = True
                
    # Store the original stdout and the TeeOutput instance globally
    global original_stdout, tee_output
    original_stdout = sys.stdout
    tee_output = TeeOutput(log_file)
    sys.stdout = tee_output
    
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
        # Try different google package imports to find what's available
        google_found = False
        for module in ['google.auth', 'google_auth_oauthlib', 'googleapiclient']:
            try:
                imported_module = __import__(module)
                google_path = os.path.dirname(imported_module.__file__)
                google_size = subprocess.check_output(['du', '-sh', google_path], text=True).split()[0]
                print(f"   {module} package size: {google_size} at {google_path}")
                google_found = True
                break
            except ImportError:
                continue
        
        if not google_found:
            print("   Google packages: Not found or not installed")
    except Exception as e:
        print(f"   Google packages size check failed: {e}")
    
    print()

# Initialize global variables for logging
original_stdout = None
tee_output = None

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
        # Only essential PySide6 components
        'PySide6.QtCore',
        'PySide6.QtGui', 
        'PySide6.QtWidgets',
        'shiboken6',
        # Essential for tray functionality
        'keyring',
        'keyrings.alt', 
        'requests',
        'dateutil',
        # Google packages (only if available)
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
        # Only essential PySide6 modules
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'shiboken6',
        # Google auth essentials only (if available)
        'google_auth_oauthlib.flow',
        'googleapiclient.discovery',
        # Essential dependencies
        'requests',
        'urllib3',
        'certifi',
    ],
    'excludes': [
        # GUI frameworks we don't use
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
        # MASSIVE PySide6 components we don't need
        'PySide6.QtWebEngine',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineQuick',
        'PySide6.QtWebView',
        'PySide6.QtWebSockets',
        'PySide6.QtWebChannel',
        'PySide6.Qt3D',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DRender',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DExtras',
        'PySide6.Qt3DAnimation',
        'PySide6.QtQuick3D',
        'PySide6.QtQuick3DRuntimeRender',
        'PySide6.QtQuick3DUtils',
        'PySide6.QtQuick3DHelpers',
        'PySide6.QtQuick3DEffects',
        'PySide6.QtQuick3DParticles',
        'PySide6.QtQuick3DAssetImport',
        'PySide6.QtQuick3DAssetUtils',
        'PySide6.QtQuick3DGlslParser',
        'PySide6.QtQuick3DHelpersImpl',
        'PySide6.QtQuick3DIblBaker',
        'PySide6.QtQuick3DSpatialAudio',
        'PySide6.QtQuick3DParticleEffects',
        'PySide6.QtQuick3DXr',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtMultimediaQuick',
        'PySide6.QtCharts',
        'PySide6.QtChartsQml',
        'PySide6.QtDataVisualization',
        'PySide6.QtDataVisualizationQml',
        'PySide6.QtGraphs',
        'PySide6.QtGraphsWidgets',
        'PySide6.QtQuick',
        'PySide6.QtQuickControls2',
        'PySide6.QtQuickWidgets',
        'PySide6.QtQuickTemplates2',
        'PySide6.QtQuickLayouts',
        'PySide6.QtQuickParticles',
        'PySide6.QtQuickShapes',
        'PySide6.QtQuickTest',
        'PySide6.QtQuickEffects',
        'PySide6.QtQuickTimeline',
        'PySide6.QtQuickTimelineBlendTrees',
        'PySide6.QtQuickVectorImage',
        'PySide6.QtQuickVectorImageGenerator',
        'PySide6.QtQuickDialogs2',
        'PySide6.QtQuickDialogs2Utils',
        'PySide6.QtQuickDialogs2QuickImpl',
        'PySide6.QtQuickControls2Basic',
        'PySide6.QtQuickControls2BasicStyleImpl',
        'PySide6.QtQuickControls2Fusion',
        'PySide6.QtQuickControls2FusionStyleImpl',
        'PySide6.QtQuickControls2Imagine',
        'PySide6.QtQuickControls2ImagineStyleImpl',
        'PySide6.QtQuickControls2Material',
        'PySide6.QtQuickControls2MaterialStyleImpl',
        'PySide6.QtQuickControls2Universal',
        'PySide6.QtQuickControls2UniversalStyleImpl',
        'PySide6.QtQuickControls2MacOSStyleImpl',
        'PySide6.QtQuickControls2IOSStyleImpl',
        'PySide6.QtQuickControls2FluentWinUI3StyleImpl',
        'PySide6.QtQuickControls2Impl',
        'PySide6.QtQml',
        'PySide6.QtQmlCore',
        'PySide6.QtQmlNetwork',
        'PySide6.QtQmlModels',
        'PySide6.QtQmlWorkerScript',
        'PySide6.QtQmlCompiler',
        'PySide6.QtQmlMeta',
        'PySide6.QtQmlLocalStorage',
        'PySide6.QtQmlXmlListModel',
        'PySide6.QtDesigner',
        'PySide6.QtDesignerComponents',
        'PySide6.QtUiTools',
        'PySide6.QtHelp',
        'PySide6.QtPrintSupport',
        'PySide6.QtSvg',
        'PySide6.QtSvgWidgets',
        'PySide6.QtOpenGL',
        'PySide6.QtOpenGLWidgets',
        'PySide6.QtBluetooth',
        'PySide6.QtNfc',
        'PySide6.QtPositioning',
        'PySide6.QtPositioningQuick',
        'PySide6.QtLocation',
        'PySide6.QtSensors',
        'PySide6.QtSensorsQuick',
        'PySide6.QtSerialPort',
        'PySide6.QtSerialBus',
        'PySide6.QtNetworkAuth',
        'PySide6.QtRemoteObjects',
        'PySide6.QtRemoteObjectsQml',
        'PySide6.QtScxml',
        'PySide6.QtScxmlQml',
        'PySide6.QtStateMachine',
        'PySide6.QtStateMachineQml',
        'PySide6.QtTextToSpeech',
        'PySide6.QtVirtualKeyboard',
        'PySide6.QtVirtualKeyboardQml',
        'PySide6.QtVirtualKeyboardSettings',
        'PySide6.QtSpatialAudio',
        'PySide6.QtPdf',
        'PySide6.QtPdfWidgets',
        'PySide6.QtPdfQuick',
        'PySide6.QtHttpServer',
        'PySide6.QtShaderTools',
        'PySide6.QtConcurrent',
        'PySide6.QtTest',
        'PySide6.QtSql',
        'PySide6.QtXml',
        'PySide6.QtDBus',
        'PySide6.QtWebChannelQuick',
        'PySide6.QtLabsPlatform',
        'PySide6.QtLabsAnimation',
        'PySide6.QtLabsFolderListModel',
        'PySide6.QtLabsQmlModels',
        'PySide6.QtLabsSettings',
        'PySide6.QtLabsSharedImage',
        'PySide6.QtLabsWavefrontMesh',
        # FFmpeg and multimedia codecs
        'libavcodec',
        'libavformat',
        'libavutil',
        'libswscale',
        'libswresample',
    ],
    'resources': DATA_FILES,
    'argv_emulation': False,
    'site_packages': False,  # Don't include entire site-packages
    'optimize': 2,  # Enable bytecode optimization
    'strip': True,  # Strip debug symbols
    'plist': {
        'CFBundleName': 'GlowStatus',
        'CFBundleDisplayName': 'GlowStatus',
        'CFBundleExecutable': 'GlowStatus',
        'CFBundleIdentifier': 'com.severswoed.glowstatus',
        'CFBundleShortVersionString': '2.0.0',
        'CFBundleVersion': '2.0.0',
        'LSUIElement': True,  # Run as background app without dock icon
        'NSHighResolutionCapable': True,  # Support retina displays
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
    
    # Properly close the log file and restore stdout
    if tee_output:
        tee_output.close()
    if original_stdout:
        sys.stdout = original_stdout