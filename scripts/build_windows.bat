@echo off
echo GlowStatus Windows Build Script
echo ================================

echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

echo Building GlowStatus.exe using spec file...
pyinstaller --noconfirm GlowStatus.spec

if exist dist\GlowStatus\GlowStatus.exe (
    echo ✓ Build successful! 
    echo ✓ Executable: dist\GlowStatus\GlowStatus.exe
    echo ✓ Distribution folder: dist\GlowStatus\
) else (
    echo ✗ Build failed or executable not found
    echo Trying fallback method...
    
    echo Building with direct command...
    pyinstaller --noconfirm --noconsole --icon=img/GlowStatus.ico --add-data "img;img" --add-data "resources;resources" src/tray_app.py
    
    if exist dist\tray_app\tray_app.exe (
        echo Renaming output to GlowStatus...
        ren dist\tray_app dist\GlowStatus
        ren dist\GlowStatus\tray_app.exe GlowStatus.exe
        echo ✓ Build complete with manual rename
    )
)

echo.
echo Build process finished!
pause
