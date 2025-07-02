@echo off
echo GlowStatus Windows Build Script
echo ================================

REM Get version from version.json for display
python -c "import json; import os; version_file = os.path.join(os.getcwd(), 'version.json'); data = json.load(open(version_file)); version = f'{data[\"major\"]}.{data[\"minor\"]}.{data[\"patch\"]}' + (f'-{data[\"pre\"]}' if data.get('pre') else ''); print('Building GlowStatus version:', version)" 2>nul || echo Building GlowStatus...

echo Setting up Google OAuth credentials...
if defined CLIENT_SECRET_JSON (
    echo Creating client_secret.json from environment variable...
    echo %CLIENT_SECRET_JSON% > resources\client_secret.json
    echo ✓ client_secret.json created from CLIENT_SECRET_JSON
) else (
    if exist "resources\client_secret.json" (
        echo ✓ Using existing client_secret.json
    ) else (
        echo ⚠️  Warning: No client_secret.json found
        echo   Application may not work without Google OAuth credentials
        echo   See resources\client_secret.json.template for format
    )
)

echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

echo Excluding Discord directory from build...
if exist discord_backup rmdir /s /q discord_backup
if exist discord (
    echo Moving discord directory temporarily...
    move discord discord_backup
)

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

echo Restoring discord directory...
if exist discord_backup (
    if exist discord rmdir /s /q discord
    move discord_backup discord
    echo ✓ Discord directory restored
)

pause
