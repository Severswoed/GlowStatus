## Custom py2app Recipe Approach for GlowStatus

### Problem
The default PySide6 py2app recipe includes **everything**, resulting in a 1.2GB app bundle with massive bloat:
- QtWebEngine (~200MB web browser engine)
- FFmpeg multimedia codecs (~100MB)
- Qt3D graphics (~50MB)
- Hundreds of unused Qt plugins (position, canbus, SQL drivers, etc.)

### Solution
Replace the default PySide6 recipe with a minimal custom one that only includes what GlowStatus actually uses.

### What Our Custom Recipe Includes

**Qt Frameworks (4 total):**
- `QtCore` - Core functionality (required)
- `QtGui` - Icons, pixmaps, painting (required for QIcon, QPainter)
- `QtWidgets` - Window system (required for QWidget, layouts, dialogs)
- `QtDBus` - macOS system integration (small, needed for system tray)

**Qt Plugins (6 total):**
- `platforms/libqcocoa.dylib` - macOS platform integration (required)
- `imageformats/libqpng.dylib` - PNG image support (for icons)
- `imageformats/libqjpeg.dylib` - JPEG image support (for icons)
- `imageformats/libqsvg.dylib` - SVG image support (for icons)
- `iconengines/libqsvgicon.dylib` - SVG icon rendering
- `styles/libqmacstyle.dylib` - Native macOS appearance

### What Our Custom Recipe Excludes

**Massive Qt Modules (excluded at source):**
- `QtWebEngine` + `QtWebEngineCore` + `QtWebEngineWidgets` (~200MB)
- `QtMultimedia` + `QtMultimediaWidgets` (~100MB with FFmpeg)
- `Qt3DCore` + `Qt3DRender` + `Qt3DLogic` + `Qt3DAnimation` (~50MB)
- `QtQuick` + `QtQml` + `QtQuickWidgets` (~50MB)
- `QtCharts` + `QtDataVisualization` + `QtGraphs` (~30MB)
- `QtNetwork`, `QtOpenGL`, `QtSql`, `QtXml`
- `QtPositioning`, `QtLocation`, `QtSensors`
- `QtSerialPort`, `QtBluetooth`, `QtNfc`
- `QtPrintSupport`, `QtTest`, `QtConcurrent`
- `QtRemoteObjects`, `QtScxml`, `QtStateMachine`
- `QtTextToSpeech`, `QtHelp`, `QtDesigner`

**Unused Qt Plugins (excluded):**
- `position/` - GPS/location plugins
- `webview/` - Web browser plugins
- `geometryloaders/` - 3D geometry loaders
- `scxmldatamodel/` - State machine plugins
- `canbus/` - Automotive CAN bus plugins
- `sqldrivers/` - Database drivers (SQLite, PostgreSQL, ODBC)
- `multimedia/libffmpegmediaplugin.dylib` - FFmpeg video codecs
- `tls/` - Additional TLS backends

### Expected Results

**Target Size:** 50-100MB (down from 1.2GB = **92% size reduction**)

**Benefits:**
- No post-build cleanup needed - py2app only includes what we specify
- Much faster build times - less to process and bundle
- Smaller download size for users
- Faster app startup - less to load

### Implementation

The custom recipe:
1. Replaces `/path/to/py2app/recipes/pyside6.py` with our minimal version
2. Uses proper py2app recipe format with `check()` and `recipe()` functions
3. Integrates with py2app's modulefinder using `mf.import_hook()`
4. Restores the original recipe after build for system cleanliness

### Verification

To verify the recipe is working:
1. Check build output for "🎯 GlowStatus: Using minimal PySide6 recipe"
2. Verify final app size is ~50-100MB instead of 1.2GB
3. Check that unwanted plugins are absent from the bundle
4. Test that the app still runs correctly on macOS

This approach is based on the official py2app documentation and should be much more reliable than post-build cleanup methods.
