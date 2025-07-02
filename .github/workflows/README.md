# GitHub Actions Workflows

This directory contains automated workflows for building, testing, and deploying GlowStatus.

## Windows Build and Chocolatey Package

**File:** `windows-build.yml`

### Triggers
- **Tag Push:** Automatically builds when a version tag is pushed (e.g., `v1.0.0`, `v2.1.3`)
- **Manual Trigger:** Can be triggered manually with a custom version number

### What it does
1. **Prepares Build Environment**
   - Sets up Python 3.11 environment
   - Installs dependencies from `requirements.txt`
   - Creates `client_secret.json` from `CLIENT_SECRET_JSON` GitHub secret
   - Validates Google OAuth credentials

2. **Builds Windows Executable**
   - Runs `scripts/build_windows.bat` to create `GlowStatus.exe`
   - Verifies the build output and tests executable
   - Cleans up sensitive credentials after build

3. **Creates Chocolatey Package**
   - Generates `.nuspec` file with package metadata
   - Creates PowerShell install/uninstall scripts
   - Builds `.nupkg` package file
   - Tests local installation

4. **Publishes Release**
   - Creates GitHub release with the built packages
   - Uploads Windows executable and Chocolatey package as artifacts
   - Generates release notes with installation instructions

5. **Automated Chocolatey Publishing**
   - Automatically publishes to Chocolatey Community Repository
   - Uses `CHOCO_APIKEY` GitHub secret for authentication
   - Requires manual approval via GitHub Environment protection

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
   - Build the Windows executable with Google OAuth credentials
   - Create and test Chocolatey package
   - Create GitHub release with download links
   - Publish to Chocolatey Community Repository (after approval)

#### Manual Trigger
1. Go to Actions tab in GitHub
2. Select "Windows Build and Chocolatey Package"
3. Click "Run workflow"
4. Enter desired version number
5. Click "Run workflow"

### Local Testing

To test Chocolatey package creation locally:

```bash
# Set environment variables (optional)
set CLIENT_SECRET_JSON={"installed":{"client_id":"...","client_secret":"..."}}
set CHOCO_APIKEY=your-chocolatey-api-key

# Build specific version
scripts\build_chocolatey.bat 1.0.0

# Test local installation
cd chocolatey\glowstatus
choco install glowstatus -s . -y --force
```

### Publishing to Chocolatey

**Automated Publishing (Current Setup):**
The workflow now automatically publishes to Chocolatey using the `CHOCO_APIKEY` secret:

1. Push a version tag (e.g., `v1.0.0`)
2. GitHub Actions builds the package
3. Go to Actions tab → Select the workflow run
4. Click "Review deployments" → Approve the `chocolatey-publish` environment
5. Package is automatically submitted to Chocolatey Community Repository
6. Wait for community moderation and approval (usually 24-48 hours)

**Manual Publishing (Fallback):**
If you prefer manual publishing:

1. Download the `.nupkg` file from the GitHub release
2. Visit https://push.chocolatey.org/
3. Upload the package file
4. Wait for community moderation and approval

**CLI Publishing (Local):**
```bash
choco push glowstatus.1.0.0.nupkg --source https://push.chocolatey.org/ --api-key YOUR_API_KEY
```

### Environment Setup

The workflow requires:
- **Windows runner** (uses `windows-latest`)
- **Python 3.11** environment
- **Chocolatey** installation
- **PyInstaller** for executable creation

**Required GitHub Secrets:**
- `CLIENT_SECRET_JSON` - Google OAuth credentials (JSON format)
- `CHOCO_APIKEY` - Chocolatey API key for automated publishing

**GitHub Environment:**
- `chocolatey-publish` environment with manual approval required

### GitHub Secrets Setup

To set up the required secrets for automated builds:

1. **Get Google OAuth Credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create/select a project and enable Google Calendar API
   - Create OAuth 2.0 credentials for a desktop application
   - Download the JSON file

2. **Get Chocolatey API Key:**
   - Sign up at [Chocolatey Community](https://community.chocolatey.org/)
   - Go to your profile → API Keys
   - Generate a new API key

3. **Add GitHub Secrets:**
   - Go to your repository → Settings → Secrets and variables → Actions
   - Add the following secrets:

   **CLIENT_SECRET_JSON:**
   ```json
   {"installed":{"client_id":"your-client-id","client_secret":"your-secret","project_id":"your-project","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","redirect_uris":["http://localhost"]}}
   ```

   **CHOCO_APIKEY:**
   ```
   your-chocolatey-api-key-here
   ```

4. **Set up Environment Protection:**
   - Go to Settings → Environments
   - Create environment named `chocolatey-publish`
   - Add yourself as a required reviewer
   - This adds approval gate before publishing

### Artifacts

Each build produces:
- `glowstatus-windows-v{VERSION}` - Contains Windows executable and all dependencies
- `glowstatus-chocolatey-v{VERSION}` - Contains the `.nupkg` Chocolatey package

### Security

- **GitHub Secrets Protection**: OAuth credentials and API keys stored securely
- **Access Control**: Only repository owner/maintainers can trigger builds
- **Environment Approval**: Manual approval required for Chocolatey publishing
- **Credential Cleanup**: OAuth secrets removed from build environment after use
- **Artifact Retention**: Limited storage time to control costs (30-90 days)
- **Audit Trail**: All operations logged and traceable

### Troubleshooting

**Build fails with missing dependencies:**
- Check `requirements.txt` is up to date
- Verify all imports are listed in `GlowStatus.spec` hiddenimports

**OAuth credentials not working:**
- Verify `CLIENT_SECRET_JSON` secret contains valid JSON
- Check that Google Calendar API is enabled in your project
- Ensure OAuth consent screen is configured

**Chocolatey package fails to install:**
- Verify PowerShell scripts have correct syntax
- Check file paths in the package structure
- Test locally before pushing tags

**Publishing fails:**
- Verify `CHOCO_APIKEY` secret is set correctly
- Check that your Chocolatey account has publishing permissions
- Ensure package name doesn't conflict with existing packages

**GitHub release creation fails:**
- Ensure the tag follows semantic versioning (v1.0.0 format)
- Check that `GITHUB_TOKEN` permissions are sufficient
- Verify all required secrets are configured

**Environment approval not working:**
- Ensure `chocolatey-publish` environment exists
- Check that you're added as a required reviewer
- Verify environment protection rules are enabled
