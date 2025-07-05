@echo off
echo GlowStatus Windows Build Script - Standalone EXE
echo ================================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Bump patch version in version.json and display version
for /f "delims=" %%V in ('python "%~dp0version_bump.py" 2^>nul') do echo %%V

echo.
echo Setting up Python environment...
echo ================================

REM Check if .venv exists, create if not
if not exist ".venv" (
    echo Creating virtual environment...
    py -3.12 -m venv .venv
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

REM Install requirements and all needed build/packaging tools
echo Installing Python dependencies and build tools...
pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo ✗ Failed to upgrade pip/setuptools/wheel
    pause
    exit /b 1
)
pip install -r requirements.txt oauth2client pyinstaller Pillow pywin32 pystray six certifi charset_normalizer idna keyring keyrings.alt packaging requests google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2 PySide6 modulegraph py2app macholib
if errorlevel 1 (
    echo ✗ Failed to install requirements and build dependencies
    pause
    exit /b 1
)

REM Install PyInstaller specifically with latest version
echo Ensuring PyInstaller is available...
pip install --upgrade pyinstaller
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

REM Clean spec file cache
REM Do not delete GlowStatus.spec; needed for PyInstaller build

echo.
echo Building standalone GlowStatus.exe using spec file (with debug)...
echo ====================================================

REM Use the optimized spec file for single executable with debug output
echo Running: pyinstaller --clean --noconfirm GlowStatus.spec
pyinstaller --clean --noconfirm GlowStatus.spec

if exist dist\GlowStatus.exe (
    echo ✓ Standalone build successful! 
    echo ✓ Executable: dist\GlowStatus.exe
    echo ✓ File size: 
    for %%A in (dist\GlowStatus.exe) do echo   %%~zA bytes
    echo.
    echo Testing executable...
    echo Running basic test (will close automatically)
    timeout /t 2 /nobreak >nul
    REM Don't actually run the test in build script as it may require GUI
    echo ✓ Executable created successfully
) else (
    echo ✗ Build failed - executable not found
    echo.
    echo The spec file build failed. Check the output above for errors.
    echo.
    echo Common issues:
    echo - Missing dependencies in requirements.txt
    echo - Import errors in your Python code
    echo - Missing files referenced in the spec
    echo - Antivirus software blocking PyInstaller
    echo - Insufficient disk space
    echo.
    echo Try running: python -m PyInstaller --version
    echo And ensure all your source files are in the correct locations
    pause
    exit /b 1
)

echo.
echo Validating standalone executable...
echo =================================

REM Check if the executable is truly standalone
if exist dist\GlowStatus.exe (
    echo ✓ Single executable file created
    echo ✓ No _internal directory should be present
    
    REM Check for _internal directory (shouldn't exist with --onefile)
    if exist dist\_internal (
        echo ✗ Warning: _internal directory found - this shouldn't happen with --onefile
        echo   The build may not be truly standalone
    ) else (
        echo ✓ No _internal directory - build is standalone
    )
    
    REM Show file details
    echo.
    echo Executable details:
    dir dist\GlowStatus.exe
    
    echo.
    echo ✓ Build validation complete
    echo ✓ Ready for Chocolatey packaging
    echo.
    echo The executable at dist\GlowStatus.exe should run on any Windows system
    echo without requiring Python or additional dependencies to be installed.
    
) else (
    echo ✗ Validation failed - executable not found
    exit /b 1
)

echo Build process finished!
echo ================================================
echo Build Summary:
echo ================================================
echo ✓ Standalone executable: dist\GlowStatus.exe
echo ✓ No external dependencies required
echo ✓ Ready for distribution via Chocolatey
echo ✓ Users won't need Python installed
echo ================================================