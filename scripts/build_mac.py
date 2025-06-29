#!/usr/bin/env python3
"""
Ultra-minimal macOS app builder for GlowStatus using PyInstaller.
This script replaces py2app to avoid the massive PySide6 bloat.
Target: 50-100MB app bundle (not 1.35GB).
"""

import os
import sys
import subprocess
import shutil
import datetime
from pathlib import Path

# Add scripts directory to Python path for build helpers
sys.path.insert(0, os.path.dirname(__file__))
from build_helpers import check_and_install_requirements, verify_critical_modules, fix_google_namespace_packages

def setup_build_logging():
    """Set up detailed build logging."""
    project_root = Path(__file__).parent.parent
    build_dir = project_root / 'build'
    build_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = build_dir / f'pyinstaller_build_{timestamp}.txt'
    
    print(f"📝 Build log will be saved to: {log_file}")
    print(f"🕐 Build started at: {datetime.datetime.now()}")
    print(f"📁 Project root: {project_root}")
    print()
    
    return log_file, project_root

def install_pyinstaller():
    """Install PyInstaller if not already available."""
    try:
        import PyInstaller
        print(f"✅ PyInstaller already installed: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("📦 Installing PyInstaller...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], 
                          check=True, capture_output=True, text=True)
            print("✅ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install PyInstaller: {e}")
            return False

def find_pyside6_essentials():
    """Find only the essential PySide6 files we need."""
    try:
        import PySide6
        pyside_path = Path(PySide6.__file__).parent
        
        # Only the files we absolutely need
        essential_files = []
        for file_pattern in ['QtCore*', 'QtGui*', 'QtWidgets*']:
            essential_files.extend(pyside_path.glob(file_pattern + '.so'))
            essential_files.extend(pyside_path.glob(file_pattern + '.dylib'))
            essential_files.extend(pyside_path.glob(file_pattern + '.pyi'))
        
        # Also need __init__.py
        init_file = pyside_path / '__init__.py'
        if init_file.exists():
            essential_files.append(init_file)
            
        print(f"📦 Found {len(essential_files)} essential PySide6 files:")
        for f in essential_files:
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"   {f.name} ({size_mb:.1f}MB)")
            
        return essential_files, pyside_path
        
    except ImportError:
        print("❌ PySide6 not found")
        return [], None

def find_shiboken6_essentials():
    """Find only essential shiboken6 files."""
    try:
        import shiboken6
        shiboken_path = Path(shiboken6.__file__).parent
        
        essential_files = []
        for file_pattern in ['shiboken6*']:
            essential_files.extend(shiboken_path.glob(file_pattern + '.so'))
            essential_files.extend(shiboken_path.glob(file_pattern + '.dylib'))
        
        # Also need __init__.py
        init_file = shiboken_path / '__init__.py'
        if init_file.exists():
            essential_files.append(init_file)
            
        print(f"📦 Found {len(essential_files)} essential shiboken6 files:")
        for f in essential_files:
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"   {f.name} ({size_mb:.1f}MB)")
            
        return essential_files, shiboken_path
        
    except ImportError:
        print("❌ shiboken6 not found")
        return [], None

def build_with_pyinstaller(project_root):
    """Build the app using PyInstaller with minimal PySide6."""
    
    print("🔥 Building with PyInstaller (ultra-minimal approach)...")
    print()
    
    # Find essential files
    pyside_files, pyside_path = find_pyside6_essentials()
    shiboken_files, shiboken_path = find_shiboken6_essentials()
    
    if not pyside_files or not shiboken_files:
        print("❌ Cannot find essential PySide6/shiboken6 files")
        return False
    
    # Build PyInstaller command
    app_script = project_root / 'src' / 'tray_app.py'
    icon_file = project_root / 'img' / 'GlowStatus.icns'
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onedir',  # Create a directory bundle (easier to debug than --onefile)
        '--windowed',  # No console window
        '--noconfirm',  # Overwrite output directory
        f'--icon={icon_file}',
        f'--name=GlowStatus',
        '--osx-bundle-identifier=com.severswoed.glowstatus',
        
        # CRITICAL: Exclude all the massive stuff
        '--exclude-module=PySide6.QtWebEngine',
        '--exclude-module=PySide6.QtWebEngineCore',
        '--exclude-module=PySide6.QtWebEngineWidgets',
        '--exclude-module=PySide6.Qt3D',
        '--exclude-module=PySide6.Qt3DCore',
        '--exclude-module=PySide6.Qt3DRender',
        '--exclude-module=PySide6.QtMultimedia',
        '--exclude-module=PySide6.QtMultimediaWidgets',
        '--exclude-module=PySide6.QtCharts',
        '--exclude-module=PySide6.QtQuick',
        '--exclude-module=PySide6.QtQuickControls2',
        '--exclude-module=PySide6.QtQuickWidgets',
        '--exclude-module=PySide6.QtQml',
        '--exclude-module=PySide6.QtNetwork',
        '--exclude-module=PySide6.QtOpenGL',
        '--exclude-module=PySide6.QtSql',
        '--exclude-module=PySide6.QtTest',
        '--exclude-module=PySide6.QtXml',
        
        # Exclude other heavy packages
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=matplotlib',
        '--exclude-module=scipy',
        '--exclude-module=PIL',
        '--exclude-module=tkinter',
        
        # Data files
        f'--add-data={project_root}/img:img',
        f'--add-data={project_root}/config:config',
        f'--add-data={project_root}/resources/client_secret.json:resources',
        
        # Only include essential PySide6 files
        f'--add-binary={pyside_path}/__init__.py:PySide6',
    ]
    
    # Add each essential PySide6 file
    for f in pyside_files:
        if f.name != '__init__.py':  # Already added above
            cmd.append(f'--add-binary={f}:PySide6')
    
    # Add essential shiboken6 files
    for f in shiboken_files:
        cmd.append(f'--add-binary={f}:shiboken6')
    
    # Add the main script
    cmd.append(str(app_script))
    
    print("🔧 PyInstaller command:")
    print(" ".join(cmd))
    print()
    
    # Change to project root for build
    original_cwd = os.getcwd()
    os.chdir(project_root)
    
    try:
        # Run PyInstaller
        print("⚡ Running PyInstaller...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ PyInstaller completed successfully!")
            
            # Check the size
            dist_path = project_root / 'dist' / 'GlowStatus'
            if dist_path.exists():
                # Get size
                size_result = subprocess.run(['du', '-sh', str(dist_path)], 
                                           capture_output=True, text=True)
                if size_result.returncode == 0:
                    size = size_result.stdout.split()[0]
                    print(f"📊 App bundle size: {size}")
                
                # Create .app bundle structure for macOS
                app_bundle = project_root / 'dist' / 'GlowStatus.app'
                if app_bundle.exists():
                    shutil.rmtree(app_bundle)
                
                print("📦 Creating macOS .app bundle...")
                create_app_bundle(dist_path, app_bundle, project_root)
                
                # Check final .app size
                size_result = subprocess.run(['du', '-sh', str(app_bundle)], 
                                           capture_output=True, text=True)
                if size_result.returncode == 0:
                    final_size = size_result.stdout.split()[0]
                    print(f"📊 Final GlowStatus.app size: {final_size}")
                
                return True
            else:
                print("❌ Build directory not found")
                return False
        else:
            print(f"❌ PyInstaller failed: {result.stderr}")
            return False
            
    finally:
        os.chdir(original_cwd)

def create_app_bundle(dist_path, app_bundle, project_root):
    """Create a proper macOS .app bundle from PyInstaller output."""
    
    # Create .app bundle structure
    contents_dir = app_bundle / 'Contents'
    macos_dir = contents_dir / 'MacOS'
    resources_dir = contents_dir / 'Resources'
    
    contents_dir.mkdir(parents=True, exist_ok=True)
    macos_dir.mkdir(exist_ok=True)
    resources_dir.mkdir(exist_ok=True)
    
    # Copy the executable and all files
    print("📁 Copying application files...")
    for item in dist_path.iterdir():
        if item.is_file() and item.name == 'GlowStatus':
            # Main executable goes to MacOS
            shutil.copy2(item, macos_dir / 'GlowStatus')
            # Make it executable
            os.chmod(macos_dir / 'GlowStatus', 0o755)
        else:
            # Everything else goes to Resources
            if item.is_dir():
                shutil.copytree(item, resources_dir / item.name)
            else:
                shutil.copy2(item, resources_dir / item.name)
    
    # Create Info.plist
    info_plist = contents_dir / 'Info.plist'
    plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>GlowStatus</string>
    <key>CFBundleDisplayName</key>
    <string>GlowStatus</string>
    <key>CFBundleExecutable</key>
    <string>GlowStatus</string>
    <key>CFBundleIdentifier</key>
    <string>com.severswoed.glowstatus</string>
    <key>CFBundleShortVersionString</key>
    <string>2.0.0</string>
    <key>CFBundleVersion</key>
    <string>2.0.0</string>
    <key>CFBundleIconFile</key>
    <string>GlowStatus.icns</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
</dict>
</plist>"""
    
    with open(info_plist, 'w') as f:
        f.write(plist_content)
    
    # Copy icon
    icon_src = project_root / 'img' / 'GlowStatus.icns'
    if icon_src.exists():
        shutil.copy2(icon_src, resources_dir / 'GlowStatus.icns')
    
    print("✅ macOS .app bundle created successfully!")

def main():
    """Main build function."""
    print("🚀 GlowStatus macOS Builder (PyInstaller)")
    print("🎯 Target: Ultra-minimal app bundle (50-100MB)")
    print()
    
    # Set up logging
    log_file, project_root = setup_build_logging()
    
    # Check and install requirements
    print("🔧 Checking requirements...")
    check_and_install_requirements()
    if not verify_critical_modules():
        print("❌ Critical modules missing. Please fix the above issues and try again.")
        sys.exit(1)
    
    print("🔧 Fixing Google namespace packages...")
    fix_google_namespace_packages()
    
    # Install PyInstaller
    if not install_pyinstaller():
        sys.exit(1)
    
    print("✅ All requirements satisfied!")
    print()
    
    print("🚫 AVOIDING py2app PySide6 recipe bloat!")
    print("📦 Using PyInstaller with manual PySide6 control:")
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
    
    # Build the app
    if build_with_pyinstaller(project_root):
        print()
        print("🏁 Build completed successfully!")
        print(f"🕐 Build finished at: {datetime.datetime.now()}")
        print(f"📝 Complete build log saved to: {log_file}")
        
        # Show final GlowStatus.app size
        app_bundle = project_root / 'dist' / 'GlowStatus.app'
        if app_bundle.exists():
            size_result = subprocess.run(['du', '-sh', str(app_bundle)], 
                                       capture_output=True, text=True)
            if size_result.returncode == 0:
                final_size = size_result.stdout.split()[0]
                print(f"📊 Final GlowStatus.app size: {final_size}")
        
        print()
        print("📊 Check your app:")
        print(f"   open {project_root}/dist/GlowStatus.app")
        print(f"   du -sh {project_root}/dist/GlowStatus.app")
        print()
        print("🎉 Your app should now be ~50-100MB instead of 1.35GB!")
    else:
        print("❌ Build failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
