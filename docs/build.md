# Build & Distribution Guide for GlowStatus

This guide covers how to build, package, and prepare GlowStatus for distribution on **macOS** and **Windows**. It also includes steps for privacy, Google OAuth approval, and best practices for a professional release.

---

## Table of Contents

1. [Preparation](#preparation)
2. [Windows Build (PyInstaller)](#windows-build-pyinstaller)
3. [macOS Build (py2app)](#macos-build-py2app)
4. [Testing Your Builds](#testing-your-builds)
5. [Privacy & Security](#privacy--security)
6. [Google OAuth Approval](#google-oauth-approval)
7. [Release Checklist](#release-checklist)
8. [Troubleshooting](#troubleshooting)

---

## Preparation

- Ensure your codebase is clean and up to date.
- **Install all dependencies first:**
    ```bash
    pip install -r requirements.txt
    ```
- Remove all personal information from `config/glowstatus_config.json`:
    - Set `"GOVEE_DEVICE_ID": ""`, `"GOVEE_DEVICE_MODEL": ""`, `"SELECTED_CALENDAR_ID": ""`.
- Ensure all required icons are present:
    - `img/GlowStatus.ico` (Windows)
    - `img/GlowStatus.icns` (macOS)
- Ensure your `scripts/build_mac.py` is configured as shown in this repo.

**Important:** The updated `scripts/build_mac.py` now includes automatic dependency checking and will verify that all required packages are installed before building. It also includes explicit PySide6 module inclusion for better macOS compatibility.

---

## Updated Build Script Features

The `scripts/build_mac.py` file has been enhanced with several improvements for better build reliability:

**Automatic Dependency Checking:**
- Verifies all packages from `requirements.txt` are installed before building
- Provides clear error messages if dependencies are missing
- Ensures consistent builds across different environments

**Critical Module Verification:**
- Checks that essential modules (PySide6, keyring, google-auth, etc.) can be imported
- Prevents build failures due to missing or broken installations
- Lists any problematic modules with helpful error messages

**Explicit PySide6 Module Inclusion:**
- Explicitly includes all necessary PySide6 modules for py2app
- Ensures GUI components work correctly in the built macOS app
- Reduces "module not found" errors in distributed builds

**Enhanced User Feedback:**
- Clear progress messages during dependency checking
- Informative error messages with actionable suggestions
- Success confirmation when all checks pass

**Cross-Platform Compatibility:**
- Works consistently on both macOS and Windows
- Handles platform-specific dependency requirements
- Maintains compatibility with both py2app and PyInstaller workflows

---

## Windows Build (PyInstaller)

1. **Install dependencies and PyInstaller:**
    ```bash
    pip install -r requirements.txt
    pip install pyinstaller
    ```

2. **Build the Executable:**
    ```bash
    pyinstaller --noconfirm --windowed --name GlowStatus --icon=img/GlowStatus.ico --add-data "img;img" --add-data "resources;resources" src/tray_app.py
    ```
    - The output should be in the `dist/GlowStatus/` folder as `GlowStatus.exe`.
    - The `--name GlowStatus` parameter sets the executable name and output directory.
    - The icon will be used for the taskbar and window.

    **If the above doesn't work (still creates `dist/tray_app/`), try these alternatives:**

    **Method 1 - Clean build with explicit spec file:**
    ```bash
    # Clean any previous builds
    rm -rf build/ dist/ *.spec
    
    # Generate a spec file first
    pyi-makespec --windowed --name GlowStatus --icon=img/GlowStatus.ico src/tray_app.py
    
    # Edit GlowStatus.spec to add data files, then build
    pyinstaller GlowStatus.spec
    ```

    **Method 2 - Manual rename after build:**
    ```bash
    pyinstaller --noconfirm --windowed --icon=img/GlowStatus.ico --add-data "img;img" --add-data "resources;resources" src/tray_app.py
    
    # Rename the output directory and executable
    mv dist/tray_app dist/GlowStatus
    mv dist/GlowStatus/tray_app.exe dist/GlowStatus/GlowStatus.exe
    ```

    **Method 3 - Use a custom spec file:**
    Create `GlowStatus.spec`:
    ```python
    # -*- mode: python ; coding: utf-8 -*-

    a = Analysis(
        ['src/tray_app.py'],
        pathex=[],
        binaries=[],
        datas=[('img', 'img'), ('resources', 'resources')],
        hiddenimports=[],
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        excludes=[],
        noarchive=False,
    )
    pyz = PYZ(a.pure)

    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='GlowStatus',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowing_subsystem=False,
        icon='img/GlowStatus.ico',
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='GlowStatus',
    )
    ```
    Then run: `pyinstaller GlowStatus.spec`

    **Alternative - Single File Executable:**
    ```bash
    pyinstaller --noconfirm --windowed --onefile --name GlowStatus --icon=img/GlowStatus.ico --add-data "img;img" --add-data "resources;resources" src/tray_app.py
    ```
    - Creates a single `GlowStatus.exe` file in `dist/` (slower startup but easier distribution).

3. **Test the Executable:**
    - Navigate to `dist/GlowStatus/` and run `GlowStatus.exe`.
    - Test on a clean Windows machine (no Python installed).
    - Ensure all features work and resources load correctly.
    - The entire `dist/GlowStatus/` folder contains all necessary files for distribution.

4. **Create a Standalone Distribution:**
    - Zip the entire `dist/GlowStatus/` folder for distribution.
    - Or create an installer using tools like Inno Setup or NSIS.

5. **(Optional) Code Signing:**
    - Sign your `.exe` with a code-signing certificate to avoid SmartScreen warnings.
    
    **Step 1: Obtain a Code Signing Certificate**
    - Purchase from a Certificate Authority (CA) like Sectigo, DigiCert, or GlobalSign
    - Or use a free certificate from Microsoft's Partner Program (if eligible)
    - Cost: ~$100-400/year for commercial certificates
    
    **Step 2: Install the Certificate**
    - Install the certificate (.p12 or .pfx file) on your Windows build machine
    - Import it to the Windows Certificate Store (Personal > Certificates)
    
    **Step 3: Sign the Executable**
    ```bash
    # Using SignTool (comes with Windows SDK)
    signtool sign /a /t http://timestamp.sectigo.com /d "GlowStatus" /du "https://github.com/Severswoed/GlowStatus" dist/GlowStatus/GlowStatus.exe
    ```
    
    **Alternative - Using PowerShell:**
    ```powershell
    # If you have the certificate thumbprint
    Set-AuthenticodeSignature -FilePath "dist/GlowStatus/GlowStatus.exe" -Certificate (Get-ChildItem Cert:\CurrentUser\My\{THUMBPRINT}) -TimestampServer "http://timestamp.sectigo.com"
    ```
    
    **Step 4: Verify the Signature**
    ```bash
    signtool verify /pa /v dist/GlowStatus/GlowStatus.exe
    ```
    
    **Alternative - Using osslsigncode (cross-platform):**
    ```bash
    # Install osslsigncode first: apt-get install osslsigncode
    osslsigncode sign -certs mycert.crt -key mykey.key -t http://timestamp.sectigo.com -in dist/GlowStatus/GlowStatus.exe -out dist/GlowStatus/GlowStatus_signed.exe
    ```
    
    **Automated Build Script (build_and_sign.bat):**
    ```batch
    @echo off
    echo Building GlowStatus...
    pyinstaller --noconfirm --windowed --name GlowStatus --icon=img/GlowStatus.ico --add-data "img;img" --add-data "resources;resources" src/tray_app.py
    
    echo Signing executable...
    signtool sign /a /t http://timestamp.sectigo.com /d "GlowStatus" /du "https://github.com/Severswoed/GlowStatus" dist/GlowStatus/GlowStatus.exe
    
    echo Verifying signature...
    signtool verify /pa /v dist/GlowStatus/GlowStatus.exe
    
    echo Build and signing complete!
    ```

---

## macOS Build (py2app)

**Important:** py2app only works on macOS. You cannot build macOS apps from Windows or Linux.

### Quick Build with Custom Recipe

GlowStatus now includes an advanced `scripts/build_mac.py` with a **custom py2app recipe** that dramatically reduces app bundle size by only including essential Qt components.

```bash
# Clean previous builds
rm -rf build/ dist/

# Build the app with custom minimal recipe
python scripts/build_mac.py py2app
```

### What the Custom Recipe Does

Our custom py2app recipe **replaces the default PySide6 recipe** to eliminate massive bloat:

**Only Includes Essential Qt Components:**
- `QtCore` - Core functionality (required)
- `QtGui` - Icons, pixmaps, painting (required for QIcon, QPainter)
- `QtWidgets` - Window system (required for QWidget, layouts, dialogs)
- `QtDBus` - macOS system integration (small, needed for system tray)
- Only 6 essential Qt plugins (platform, image formats, native style)

**Excludes Massive Qt Bloat:**
- `QtWebEngine` + `QtWebEngineCore` (~200MB web browser engine)
- `QtMultimedia` + FFmpeg codecs (~100MB video/audio)
- `Qt3D` graphics modules (~50MB 3D rendering)
- `QtQuick` + `QtQml` (~50MB modern UI framework)
- `QtCharts` + `QtDataVisualization` (~30MB charting)
- Hundreds of unused Qt plugins (GPS, CAN bus, SQL drivers, etc.)

**Expected Results:**
- **Target Size:** 50-100MB (down from 1.2GB = 92% reduction)
- **Faster builds:** Less to process and bundle
- **Faster startup:** Less to load at runtime

### What the build_mac.py Does Automatically

1. **Dependency Check**: Verifies all requirements.txt packages are installed
2. **Module Verification**: Tests that critical modules (PySide6, Google APIs, etc.) can be imported
3. **Custom Recipe Creation**: Replaces default PySide6 recipe with minimal version
4. **Namespace Package Fix**: Resolves Google namespace package issues
5. **Recipe Restoration**: Restores original py2app recipes after build

### Manual Build Steps (if needed)

If the automatic build fails, you can manually troubleshoot:

1. **Install dependencies and py2app:**
    ```bash
    pip install -r requirements.txt
    pip install py2app
    ```

2. **Build the App:**
    ```bash
    python scripts/build_mac.py py2app
    ```
    - The `.app` bundle will be in the `dist/` folder.
    - Look for "🎯 GlowStatus: Using minimal PySide6 recipe" in the output.
    - Final size should be displayed as ~50-100MB instead of 1.2GB.

3. **If build fails with custom recipe errors:**
    ```bash
    # Clean previous build and try again
    rm -rf build/ dist/
    pip install -r requirements.txt
    python scripts/build_mac.py py2app
    ```

4. **Verify the custom recipe worked:**
    ```bash
    # Check the app size
    du -sh dist/GlowStatus.app
    
    # Should show ~50-100MB, not 1.2GB
    # Check that bloated Qt plugins are NOT included
    find dist/GlowStatus.app -name "*webengine*" | wc -l  # Should be 0
    find dist/GlowStatus.app -name "*3d*" | wc -l        # Should be 0
    find dist/GlowStatus.app -name "*multimedia*" | wc -l # Should be 0
    ```

5. **Test the App:**
    - Open `dist/GlowStatus.app` by double-clicking.
    - Ensure all features work despite the minimal Qt components.
    - Test on a clean macOS machine without development tools installed.
    - Verify that PySide6 GUI components function properly with reduced bundle size.

5. **Code Signing & Notarization:**
    
    **Prerequisites:**
    - Apple Developer Account ($99/year)
    - Xcode Command Line Tools: `xcode-select --install`
    - Valid Developer ID Application certificate in Keychain
    
    **Step 1: Sign the Application**
    ```bash
    # Find your signing identity
    security find-identity -v -p codesigning
    
    # Sign the app bundle (replace with your actual Developer ID)
    codesign --force --verify --verbose --sign "Developer ID Application: Your Name (TEAMID)" dist/GlowStatus.app
    
    # Verify the signature
    codesign --verify --verbose dist/GlowStatus.app
    spctl --assess --verbose dist/GlowStatus.app
    ```
    
    **Step 2: Create a DMG for Distribution**
    ```bash
    # Install create-dmg tool
    brew install create-dmg
    
    # Create a DMG
    create-dmg \
      --volname "GlowStatus" \
      --volicon "img/GlowStatus.icns" \
      --window-pos 200 120 \
      --window-size 600 300 \
      --icon-size 100 \
      --icon "GlowStatus.app" 175 120 \
      --hide-extension "GlowStatus.app" \
      --app-drop-link 425 120 \
      "GlowStatus.dmg" \
      "dist/"
    ```
    
    **Step 3: Sign the DMG**
    ```bash
    codesign --force --verify --verbose --sign "Developer ID Application: Your Name (TEAMID)" GlowStatus.dmg
    ```
    
    **Step 4: Notarize with Apple**
    ```bash
    # Create an app-specific password in Apple ID settings first
    # Store credentials in keychain
    xcrun notarytool store-credentials "notarytool-profile" \
      --apple-id "your-apple-id@example.com" \
      --team-id "TEAMID" \
      --password "app-specific-password"
    
    # Submit for notarization
    xcrun notarytool submit GlowStatus.dmg \
      --keychain-profile "notarytool-profile" \
      --wait
    
    # Staple the notarization ticket
    xcrun stapler staple GlowStatus.dmg
    
    # Verify notarization
    xcrun stapler validate GlowStatus.dmg
    spctl --assess --type open --context context:primary-signature --verbose GlowStatus.dmg
    ```
    
    **Alternative - Legacy Notarization (if needed):**
    ```bash
    # Upload for notarization (legacy method)
    xcrun altool --notarize-app \
      --primary-bundle-id "com.severswoed.glowstatus" \
      --username "your-apple-id@example.com" \
      --password "app-specific-password" \
      --file GlowStatus.dmg
    
    # Check status (replace REQUEST-UUID with actual UUID from upload)
    xcrun altool --notarization-info REQUEST-UUID \
      --username "your-apple-id@example.com" \
      --password "app-specific-password"
    ```
    
    **Automated Build Script (build_and_sign_mac.sh):**
    ```bash
    #!/bin/bash
    set -e
    
    echo "Building GlowStatus for macOS..."
    python scripts/build_mac.py py2app
    
    echo "Signing the application..."
    codesign --force --verify --verbose --sign "Developer ID Application: Your Name (TEAMID)" dist/GlowStatus.app
    
    echo "Creating DMG..."
    create-dmg \
      --volname "GlowStatus" \
      --volicon "img/GlowStatus.icns" \
      --window-pos 200 120 \
      --window-size 600 300 \
      --icon-size 100 \
      --icon "GlowStatus.app" 175 120 \
      --hide-extension "GlowStatus.app" \
      --app-drop-link 425 120 \
      "GlowStatus.dmg" \
      "dist/"
    
    echo "Signing DMG..."
    codesign --force --verify --verbose --sign "Developer ID Application: Your Name (TEAMID)" GlowStatus.dmg
    
    echo "Submitting for notarization..."
    xcrun notarytool submit GlowStatus.dmg \
      --keychain-profile "notarytool-profile" \
      --wait
    
    echo "Stapling notarization..."
    xcrun stapler staple GlowStatus.dmg
    
    echo "Verifying final DMG..."
    spctl --assess --type open --context context:primary-signature --verbose GlowStatus.dmg
    
    echo "Build, signing, and notarization complete!"
    echo "Distribution-ready DMG: GlowStatus.dmg"
    ```

---

## Build Process Validation

After completing either the Windows or macOS build process, you should verify:

**Dependency Verification:**
- All required packages are bundled correctly
- No import errors when running the built application
- PySide6 GUI components function properly

**Functionality Testing:**
- Test on a clean machine without Python or development tools
- Verify OAuth flow works correctly
- Check that light control and calendar sync features function
- Ensure tray menu and settings window work properly

**Resource Loading:**
- Icons display correctly in system tray and application windows
- Config files are accessible and writable
- Error logging works and creates log files in appropriate locations

**Cross-Platform Consistency:**
- UI appearance matches expected design
- All features work consistently across platforms
- Configuration and data files use correct paths

---

## Testing Your Builds

- Test on a clean user account or virtual machine.
- Verify:
    - The app launches and the icon appears correctly.
    - The settings window works and prompts for user setup.
    - No personal data is present in the default config.
    - All resources (icons, OAuth, etc.) are included and functional.
    - The tray icon and taskbar/dock icon are correct.

---

## Privacy & Security

- **Remove all personal/device info from distributed configs.**
- **Prepare a privacy policy and terms of service** (can be a simple GitHub Pages or markdown file).
- **Document what data is accessed and how it is used** (especially for Google OAuth).

---

## Google OAuth Approval

1. **Set up your OAuth consent screen** in the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
2. **Add your app logo, support email, privacy policy, and terms of service.**
3. **Add required scopes** (e.g., `https://www.googleapis.com/auth/calendar.readonly`).
4. **Add yourself and testers as test users** (for development).
5. **Prepare for verification:**
    - Record a video showing the OAuth flow and how calendar data is used.
    - Provide screenshots.
6. **Submit for verification** and respond to any Google feedback.

---

## Release Checklist

- [ ] All personal info removed from configs.
- [ ] App icons set for both platforms.
- [ ] Standalone builds tested on clean machines.
- [ ] Privacy policy and terms of service published.
- [ ] Google OAuth consent screen set up and verified.
- [ ] Code signed and notarized (recommended).
- [ ] README and documentation updated.
- [ ] Installers/bundles uploaded to GitHub Releases or your website.
- [ ] Announcement prepared for launch.

---

## Troubleshooting

- **Missing resources:**  
  Add them to `DATA_FILES` in `scripts/build_mac.py` (macOS) or use `--add-data` with PyInstaller (Windows).

- **Missing dependencies during build:**  
  Run `pip install -r requirements.txt` first. The updated build_mac.py will check dependencies automatically.

- **PySide6 import errors on macOS:**  
  The custom recipe handles PySide6 inclusion. If errors persist, clean build and retry: `rm -rf build/ dist/` then rebuild.

- **App bundle still over 200MB:**  
  Check that the custom recipe is working - look for "🎯 GlowStatus: Using minimal PySide6 recipe" in build output. If not present, the recipe failed to apply.

- **Custom recipe errors:**
  The build script backs up and restores original py2app recipes. If recipe modification fails, the build will continue with default behavior but larger size.

- **App name is wrong:**  
  Set `CFBundleName` in the `plist` section of `scripts/build_mac.py` (macOS).

- **Security warnings:**  
  Sign your executables and apps.

- **Code signing errors:**
  - Ensure certificate is properly installed in Windows Certificate Store
  - Use `certlm.msc` to view machine certificates or `certmgr.msc` for user certificates
  - Check certificate validity: `signtool verify /pa /v yourfile.exe`
  - Use timestamping to prevent signature expiration issues
  
- **SmartScreen still shows warnings after signing:**
  - Newly signed executables may still trigger warnings initially
  - Microsoft builds reputation over time based on download/execution patterns
  - Consider Extended Validation (EV) certificates for immediate reputation

- **Google OAuth errors:**  
  Double-check your consent screen, scopes, and credentials.

- **PyInstaller --name parameter not working:**
  - Try cleaning build cache: `rm -rf build/ dist/ __pycache__/ *.spec`
  - Use `pyi-makespec` to generate spec file first, then edit and build
  - Check PyInstaller version: `pyinstaller --version` (should be 5.0+)
  - Try using forward slashes in paths even on Windows
  - As workaround: build normally then rename `dist/tray_app` to `dist/GlowStatus`

- **Missing SignTool:**
  - Install Windows SDK or Visual Studio with Windows development tools
  - SignTool is typically located in: `C:\Program Files (x86)\Windows Kits\10\bin\{version}\x64\signtool.exe`

- **macOS Code Signing Issues:**
  - Ensure you have a valid Developer ID Application certificate in Keychain Access
  - Check certificate expiration: `security find-identity -v -p codesigning`
  - If "no identity found", download certificates from Apple Developer portal
  - Use `codesign --verify --verbose --deep YourApp.app` to debug signing issues

- **macOS Notarization Failures:**
  - Check notarization log: `xcrun notarytool log <submission-id> --keychain-profile "notarytool-profile"`
  - Common issues: unsigned frameworks, invalid bundle IDs, missing entitlements
  - Ensure all nested frameworks are signed: `codesign --verify --deep --verbose YourApp.app`
  - Use `--options runtime` for hardened runtime if required

- **macOS Gatekeeper Issues:**
  - Users can temporarily bypass: Right-click app → "Open" → "Open anyway"
  - For permanent fix: proper code signing + notarization required
  - Test with: `spctl --assess --verbose YourApp.app`

- **DMG Creation Issues:**
  - Install create-dmg: `brew install create-dmg`
  - Ensure proper icon formats (.icns for macOS)
  - Check DMG signature: `codesign --verify --verbose YourFile.dmg`

- **"No module named 'google'" error with py2app:**  
  The build_mac.py automatically fixes this by creating necessary `__init__.py` files and including Google submodules.
  
  If the issue persists:
  ```bash
  # Verify Google packages are installed correctly
  python -c "import google.auth; print('Google auth works')"
  python -c "import googleapiclient; print('Google API client works')"
  
  # Clean build and retry
  rm -rf build/ dist/
  python scripts/build_mac.py py2app
  ```

- **py2app recipe backup/restore issues:**
  If py2app recipes get corrupted, reinstall py2app:
  ```bash
  pip uninstall py2app
  pip install py2app
  ```
  ```

- **py2app build hanging or taking very long:**
  - The build_mac.py now shows progress messages - if it stops at "Verifying critical modules", there may be import issues
  - Check the terminal output for specific module import errors
  - Try building with verbose output: `python scripts/build_mac.py py2app --verbose`