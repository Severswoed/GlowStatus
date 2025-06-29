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
- Remove all personal information from `config/glowstatus_config.json`:
    - Set `"GOVEE_DEVICE_ID": ""`, `"GOVEE_DEVICE_MODEL": ""`, `"SELECTED_CALENDAR_ID": ""`.
- Ensure all required icons are present:
    - `img/GlowStatus.ico` (Windows)
    - `img/GlowStatus.icns` (macOS)
- Ensure your `setup.py` is in the project root and configured as shown in this repo.

---

## Windows Build (PyInstaller)

1. **Install PyInstaller:**
    ```bash
    pip install pyinstaller
    ```

2. **Build the Executable:**
    ```bash
    pyinstaller --noconfirm --windowed --name=GlowStatus --icon=img/GlowStatus.ico --add-data "img;img" --add-
    ```
    - The output will be in the `dist/` folder as a standalone `.exe`.
    - The icon will be used for the taskbar and window.

3. **Test the Executable:**
    - Run the `.exe` on a clean Windows machine (no Python installed).
    - Ensure all features work and resources load correctly.

4. **(Optional) Code Signing:**
    - Sign your `.exe` with a code-signing certificate to avoid SmartScreen warnings.

---

## macOS Build (py2app)

1. **Install py2app:**
    ```bash
    pip install py2app
    ```

2. **Ensure `setup.py` is configured:**
    - The `APP` entry should point to your entry script (e.g., `src/tray_app.py`).
    - The `plist` section should set `CFBundleName` and other metadata to `GlowStatus`.

3. **Build the App:**
    ```bash
    python setup.py py2app
    ```
    - The `.app` bundle will be in the `dist/` folder.
    - The Dock icon and app name will match your branding.

4. **Test the App:**
    - Open `dist/GlowStatus.app` by double-clicking.
    - Ensure all features work and resources load correctly.

5. **(Optional) Notarization & Code Signing:**
    - Sign and notarize your `.app` with Apple to avoid Gatekeeper warnings.
    - [Apple Notarization Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)

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
  Add them to `DATA_FILES` in `setup.py` (macOS) or use `--add-data` with PyInstaller (Windows).

- **App name is wrong:**  
  Set `CFBundleName` in the `plist` section of `setup.py` (macOS).

- **Security warnings:**  
  Sign your executables and apps.

- **Google OAuth errors:**  
  Double-check your consent screen, scopes, and credentials.

---

🎵 You'll never shine if you don't glow! 💙 