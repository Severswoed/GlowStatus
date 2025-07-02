@echo off
echo GlowStatus Windows Build Script
echo ================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Get version from version.json for display
python -c "import json; import os; version_file = os.path.join(os.getcwd(), 'version.json'); data = json.load(open(version_file)); version = f'{data[\"major\"]}.{data[\"minor\"]}.{data[\"patch\"]}' + (f'-{data[\"pre\"]}' if data.get('pre') else ''); print('Building GlowStatus version:', version)" 2>nul || echo Building GlowStatus...

echo.
echo Setting up Python environment...
echo ================================

REM Check if .venv exists, create if not
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ✗ Failed to create virtual environment
        echo Make sure you have python-venv installed
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
) else (
    echo ✓ Using existing virtual environment
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ✗ Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ✗ Failed to install requirements
    pause
    exit /b 1
)

REM Install PyInstaller specifically (in case it's not in requirements.txt)
echo Ensuring PyInstaller is available...
pip install pyinstaller
if errorlevel 1 (
    echo ✗ Failed to install PyInstaller
    pause
    exit /b 1
)

echo ✓ All dependencies installed successfully
echo.

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
echo ================================

REM Clean build directories with error handling
if exist build (
    echo Removing build directory...
    rmdir /s /q build 2>nul
    if exist build (
        echo Warning: Could not fully remove build directory, continuing...
    )
)

if exist dist (
    echo Removing dist directory...
    rmdir /s /q dist 2>nul
    if exist dist (
        echo Warning: Could not fully remove dist directory, continuing...
    )
)

if exist __pycache__ (
    echo Removing Python cache...
    rmdir /s /q __pycache__ 2>nul
)

REM Clean any .pyc files
echo Cleaning Python bytecode files...
for /r . %%i in (*.pyc) do del "%%i" 2>nul

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
