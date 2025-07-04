# Chocolatey Package Documentation

## Overview

GlowStatus is distributed on Windows via Chocolatey, a package manager for Windows that simplifies software installation and management.

## Installation for Users

```powershell
# Install GlowStatus via Chocolatey
choco install glowstatus

# Upgrade to latest version
choco upgrade glowstatus

# Uninstall
choco uninstall glowstatus
```

## Package Structure

```
chocolatey/glowstatus/
├── glowstatus.nuspec                 # Package metadata
├── tools/
│   ├── chocolateyinstall.ps1        # Installation script
│   ├── chocolateyuninstall.ps1      # Uninstallation script
│   ├── GlowStatus.exe               # Main executable
│   └── [dependencies]               # PyInstaller bundle contents
└── glowstatus.{version}.nupkg       # Built package
```

## Build Process

### Automated (GitHub Actions)
1. Push a version tag: `git tag v1.0.0 && git push origin v1.0.0`
2. GitHub Actions automatically builds and publishes

### Manual Local Build
```bash
# Build specific version
scripts\build_chocolatey.bat 1.0.0

# Test installation
cd chocolatey\glowstatus
choco install glowstatus -s . -y --force
```

## Package Metadata

- **ID:** `glowstatus`
- **Authors:** Severswoed
- **Project URL:** https://github.com/Severswoed/GlowStatus
- **License:** MIT
- **Tags:** govee, smart-lights, calendar, status-indicator, productivity, remote-work

## Installation Features

The Chocolatey package automatically:
- Installs GlowStatus.exe to the Chocolatey tools directory
- Creates a desktop shortcut for easy access
- Creates a Start Menu entry
- Displays post-installation setup instructions

## Uninstallation Features

When uninstalled, the package:
- Removes desktop and Start Menu shortcuts
- Stops any running GlowStatus processes
- Preserves user configuration files in `%APPDATA%\GlowStatus`

## Publishing Process

1. **Community Submission**: New packages require manual submission to https://push.chocolatey.org/
2. **Moderation**: Community volunteers review the package for security and quality
3. **Approval**: Once approved, the package becomes available via `choco install`
4. **Updates**: Subsequent versions can be auto-published if trusted maintainer status is achieved

## Verification

Users can verify package authenticity:
```powershell
# View package information
choco info glowstatus

# View package dependencies and files
choco list -lo glowstatus
```

## Troubleshooting

### Common Installation Issues

**"Package not found"**
- Ensure Chocolatey is installed: `choco --version`
- Update package list: `choco upgrade chocolatey`

**"Access denied during installation"**
- Run PowerShell as Administrator
- Check antivirus software isn't blocking installation

**"Shortcut not created"**
- Check Windows user permissions
- Manually create shortcut to: `%ChocolateyInstall%\lib\glowstatus\tools\GlowStatus.exe`

### Package Development Issues

**Build fails with "pyinstaller not found"**
```bash
pip install pyinstaller
```

**Missing dependencies in package**
- Update `requirements.txt`
- Add missing imports to `GlowStatus.spec` hiddenimports
- Test executable before packaging

**Chocolatey pack fails**
- Verify `choco` is in PATH
- Check `.nuspec` file XML syntax
- Ensure all referenced files exist

## Security Considerations

- Package contents are verified during Chocolatey community review
- No sensitive credentials are included in the package
- OAuth secrets are excluded from the build process
- Users should only install from the official Chocolatey Community Repository

## References

- [Chocolatey Package Creation Guide](https://docs.chocolatey.org/en-us/create/create-packages)
- [Chocolatey Community Repository](https://community.chocolatey.org/)
- [GlowStatus GitHub Repository](https://github.com/Severswoed/GlowStatus)
