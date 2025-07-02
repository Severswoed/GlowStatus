# GitHub Actions Workflows

This directory contains automated workflows for building, testing, and deploying GlowStatus.

## Windows Build and Chocolatey Package

**File:** `windows-build.yml`

### Triggers
- **Tag Push:** Automatically builds when a version tag is pushed (e.g., `v1.0.0`, `v2.1.3`)
- **Manual Trigger:** Can be triggered manually with a custom version number

### What it does
1. **Builds Windows Executable**
   - Sets up Python 3.11 environment
   - Installs dependencies from `requirements.txt`
   - Runs `scripts/build_windows.bat` to create `GlowStatus.exe`
   - Verifies the build output

2. **Creates Chocolatey Package**
   - Generates `.nuspec` file with package metadata
   - Creates PowerShell install/uninstall scripts
   - Builds `.nupkg` package file
   - Tests local installation

3. **Publishes Release**
   - Creates GitHub release with the built packages
   - Uploads Windows executable and Chocolatey package as artifacts
   - Generates release notes with installation instructions

4. **Chocolatey Publishing** (Manual Step)
   - Provides instructions for publishing to Chocolatey Community Repository
   - Requires manual upload to https://push.chocolatey.org/ for community review

### Chocolatey Package Features

The generated Chocolatey package includes:

- **Installation:**
  - Copies `GlowStatus.exe` and dependencies to Chocolatey tools directory
  - Creates desktop shortcut for easy access
  - Creates Start Menu shortcut
  - Displays setup instructions

- **Uninstallation:**
  - Removes desktop and Start Menu shortcuts
  - Stops running GlowStatus processes
  - Preserves user configuration files

### Usage

#### Automatic (Recommended)
1. Create and push a version tag:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. The workflow will automatically:
   - Build the Windows executable
   - Create Chocolatey package
   - Create GitHub release

#### Manual Trigger
1. Go to Actions tab in GitHub
2. Select "Windows Build and Chocolatey Package"
3. Click "Run workflow"
4. Enter desired version number
5. Click "Run workflow"

### Local Testing

To test Chocolatey package creation locally:

```bash
# Build specific version
scripts\build_chocolatey.bat 1.0.0

# Test local installation
cd chocolatey\glowstatus
choco install glowstatus -s . -y --force
```

### Publishing to Chocolatey

After the GitHub Action completes:

1. Download the `.nupkg` file from the GitHub release
2. Visit https://push.chocolatey.org/
3. Upload the package file
4. Wait for community moderation and approval

For automated publishing (requires Chocolatey API key):
```bash
choco push glowstatus.1.0.0.nupkg --source https://push.chocolatey.org/ --api-key YOUR_API_KEY
```

### Environment Setup

The workflow requires:
- **Windows runner** (uses `windows-latest`)
- **Python 3.11** environment
- **Chocolatey** installation
- **PyInstaller** for executable creation

### Artifacts

Each build produces:
- `glowstatus-windows-v{VERSION}` - Contains Windows executable and all dependencies
- `glowstatus-chocolatey-v{VERSION}` - Contains the `.nupkg` Chocolatey package

### Security

- No sensitive credentials are stored in the workflow
- OAuth secrets are properly excluded from builds
- Package integrity is verified during testing

### Troubleshooting

**Build fails with missing dependencies:**
- Check `requirements.txt` is up to date
- Verify all imports are listed in `GlowStatus.spec` hiddenimports

**Chocolatey package fails to install:**
- Verify PowerShell scripts have correct syntax
- Check file paths in the package structure
- Test locally before pushing tags

**GitHub release creation fails:**
- Ensure the tag follows semantic versioning (v1.0.0 format)
- Check that `GITHUB_TOKEN` permissions are sufficient
