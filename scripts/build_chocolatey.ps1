Write-Host "GlowStatus Chocolatey Package Builder"
Write-Host "===================================="

# Read version from version.json (in root)
$versionFile = "version.json"
if (!(Test-Path $versionFile)) {
    Write-Error "version.json not found in root directory!"
    exit 1
}

$v = Get-Content $versionFile | ConvertFrom-Json
if (-not $v.major) {
    Write-Error "Could not read version fields from version.json"
    exit 1
}
$VERSION = "$($v.major).$($v.minor).$($v.patch)"
if ($v.pre -and $v.pre -ne "") { $VERSION = "$VERSION-$($v.pre)" }
Write-Host "Building version: $VERSION"

# Step 0: Setting up environment credentials
Write-Host "`nStep 0: Setting up environment credentials..."

# Check GitHub authentication
if ($env:GITHUB_TOKEN) {
    Write-Host "✓ GitHub token found in environment"
} else {
    Write-Warning "No GitHub token found"
    Write-Host "  - Set GITHUB_TOKEN environment variable for GitHub releases"
    Write-Host "  - Generate a Personal Access Token at: https://github.com/settings/tokens"
    Write-Host "  - Required permissions: repo (for releases)"
}

# Check Chocolatey API key
if ($env:CHOCO_APIKEY) {
    Write-Host "✓ Chocolatey API key found in environment"
} else {
    Write-Warning "No Chocolatey API key found"
    Write-Host "  - Set CHOCO_APIKEY environment variable for automatic publishing"
    Write-Host "  - Get your API key at: https://community.chocolatey.org/account"
}

# Check Google OAuth credentials
if ($env:CLIENT_SECRET_JSON) {
    Write-Host "Creating client_secret.json from environment variable..."
    if (!(Test-Path "resources")) {
        New-Item -ItemType Directory -Path "resources" -Force | Out-Null
    }
    $env:CLIENT_SECRET_JSON | Out-File -Encoding ascii -NoNewline "resources/client_secret.json"
    Write-Host "✓ client_secret.json created from CLIENT_SECRET_JSON"
} elseif (Test-Path "resources/client_secret.json") {
    Write-Host "✓ Using existing client_secret.json"
} else {
    Write-Warning "No client_secret.json found"
    Write-Host "  - Set CLIENT_SECRET_JSON environment variable, or"
    Write-Host "  - Copy your Google OAuth credentials to resources/client_secret.json"
    Write-Host "  - See resources/client_secret.json.template for format"
}

Write-Host "`nEnvironment Setup Notes:"
Write-Host "========================"
Write-Host "Required environment variables for full automation:"
Write-Host "  GITHUB_TOKEN     - GitHub Personal Access Token (repo permissions)"
Write-Host "  CHOCO_APIKEY     - Chocolatey Community API Key"
Write-Host "  CLIENT_SECRET_JSON - Google OAuth credentials (JSON format)"
Write-Host ""
if (-not $env:GITHUB_TOKEN -or -not $env:CHOCO_APIKEY) {
    Write-Host "Some environment variables are missing. Continue? (y/n)"
    $response = Read-Host
    if ($response -ne 'y' -and $response -ne 'Y') {
        Write-Host "Setup cancelled by user"
        exit 0
    }
}

# Step 1: Building Windows executable (only if not present)
if (!(Test-Path "dist/GlowStatus/GlowStatus.exe")) {
    Write-Host "`nStep 1: Building Windows executable..."
    if (!(Test-Path "scripts/build_windows.bat")) {
        Write-Error "scripts/build_windows.bat not found!"
        exit 1
    }
    $buildResult = & "scripts/build_windows.bat"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Windows build script failed with exit code $LASTEXITCODE"
        exit 1
    }
    if (!(Test-Path "dist/GlowStatus/GlowStatus.exe")) {
        Write-Error "Windows build failed - executable not found"
        exit 1
    }
    Write-Host "✓ Windows build successful!"
} else {
    Write-Host "`nStep 1: Skipping build, dist/GlowStatus/GlowStatus.exe already exists."
}

# Step 2: Creating Chocolatey package structure
Write-Host "`nStep 2: Creating Chocolatey package structure..."
if (Test-Path "chocolatey") { Remove-Item chocolatey -Recurse -Force }
New-Item -ItemType Directory -Path "chocolatey/glowstatus/tools" -Force | Out-Null

Write-Host "Copying executable and dependencies..."
Copy-Item "dist/GlowStatus/*" "chocolatey/glowstatus/tools/" -Recurse -Force

# Step 3: Creating nuspec file from template (nuspec in root)
Write-Host "`nStep 3: Creating nuspec file from template..."
$nuspecTemplate = Get-Content "GlowStatus.nuspec" -Raw
$nuspec = $nuspecTemplate -replace '\$VERSION', $VERSION
$nuspecPath = "chocolatey/glowstatus/GlowStatus.nuspec"
$nuspec | Set-Content -Path $nuspecPath -Encoding UTF8

# Step 4: Creating install script
Write-Host "`nStep 4: Creating install script..."
$installScript = @'
$ErrorActionPreference = 'Stop'

$packageName = 'glowstatus'
$toolsDir = Split-Path -parent $MyInvocation.MyCommand.Definition

# Create Program Files directory
$programFilesDir = Join-Path $env:ProgramFiles 'GlowStatus'
if (!(Test-Path $programFilesDir)) {
    New-Item -ItemType Directory -Path $programFilesDir -Force | Out-Null
}

# Copy all files from tools directory to Program Files
Write-Host "Installing GlowStatus to $programFilesDir..."
Copy-Item "$toolsDir\*" $programFilesDir -Recurse -Force

$exePath = Join-Path $programFilesDir 'GlowStatus.exe'

# Create desktop shortcut
$desktopPath = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktopPath 'GlowStatus.lnk'

$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $exePath
$Shortcut.WorkingDirectory = $programFilesDir
$Shortcut.Description = 'GlowStatus - Smart Presence Indicator'
$Shortcut.Save()

Write-Host "GlowStatus installed successfully to $programFilesDir!"
Write-Host "Desktop shortcut created."
'@
$installScript | Set-Content "chocolatey/glowstatus/tools/chocolateyinstall.ps1"

# Step 5: Creating uninstall script
Write-Host "`nStep 5: Creating uninstall script..."
$uninstallScript = @'
$ErrorActionPreference = 'Stop'

# Remove desktop shortcut
$desktopPath = [Environment]::GetFolderPath('Desktop')
$desktopShortcut = Join-Path $desktopPath 'GlowStatus.lnk'
if (Test-Path $desktopShortcut) {
    Remove-Item $desktopShortcut -Force
    Write-Host "Removed desktop shortcut"
}

# Stop any running processes
Get-Process -Name "GlowStatus" -ErrorAction SilentlyContinue | Stop-Process -Force

# Remove Program Files directory
$programFilesDir = Join-Path $env:ProgramFiles 'GlowStatus'
if (Test-Path $programFilesDir) {
    Remove-Item $programFilesDir -Recurse -Force
    Write-Host "Removed $programFilesDir"
}

Write-Host "GlowStatus uninstalled successfully!"
'@
$uninstallScript | Set-Content "chocolatey/glowstatus/tools/chocolateyuninstall.ps1"

# Step 6: Building Chocolatey package first (so we can get the package URL)
Write-Host "`nStep 6: Building Chocolatey package..."
Push-Location "chocolatey/glowstatus"
$packageBuiltSuccessfully = $false
$chocolateyPackageUrl = "https://community.chocolatey.org/packages/glowstatus"

try {
    choco pack
    
    if (Test-Path "glowstatus.$VERSION.nupkg") {
        Write-Host "`n✓ Chocolatey package created successfully!"
        Write-Host "✓ Package: chocolatey/glowstatus/glowstatus.$VERSION.nupkg"
        $packageBuiltSuccessfully = $true
        
        # Try to publish if API key is available
        if ($env:CHOCO_APIKEY) {
            Write-Host "Publishing automatically with API key..."
            choco push "glowstatus.$VERSION.nupkg" --source https://push.chocolatey.org/ --api-key $env:CHOCO_APIKEY
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Package published successfully!"
                $chocolateyPackageUrl = "https://community.chocolatey.org/packages/glowstatus/$VERSION"
            }
            else {
                Write-Host "✗ Publishing failed - using generic package URL"
            }
        }
        else {
            Write-Host "No API key found - package created but not published"
            Write-Host "To publish manually:"
            Write-Host "  choco push glowstatus.$VERSION.nupkg --source https://push.chocolatey.org/ --api-key YOUR_API_KEY"
        }
    } 
    else {
        Write-Host "✗ Chocolatey package creation failed"
        exit 1
    }
}
catch {
    Write-Error "Error building Chocolatey package: $($_.Exception.Message)"
    exit 1
}
finally {
    Pop-Location
}

# Step 7: Creating GitHub release with proper release notes using StringBuilder
Write-Host "`nStep 7: Creating GitHub release..."
if ($env:GITHUB_TOKEN && $packageBuiltSuccessfully) {
    Write-Host "Creating GitHub release v$VERSION..."
    
    # Check if release already exists
    $releaseCheckUrl = "https://api.github.com/repos/Severswoed/GlowStatus/releases/tags/v" + "$VERSION"
    $headers = @{
        "Authorization" = "token $env:GITHUB_TOKEN"
        "Accept" = "application/vnd.github.v3+json"
    }
    
    try {
        $existingRelease = Invoke-RestMethod -Uri $releaseCheckUrl -Headers $headers -Method Get -ErrorAction Stop
        Write-Host "✓ Release v$VERSION already exists"
        Write-Host "  Release URL: $($existingRelease.html_url)"
    }
    catch {
        if ($_.Exception.Response.StatusCode -eq 404) {
            # Release doesn't exist, create it using StringBuilder
            Write-Host "Creating new GitHub release..."
            
            # Create comprehensive release notes using StringBuilder
            $releaseNotesBuilder = New-Object System.Text.StringBuilder
            [void]$releaseNotesBuilder.AppendLine("# GlowStatus v$VERSION")
            [void]$releaseNotesBuilder.AppendLine("")
            [void]$releaseNotesBuilder.AppendLine("## Installation Options")
            [void]$releaseNotesBuilder.AppendLine("")
            [void]$releaseNotesBuilder.AppendLine("### Chocolatey Package (Recommended)")
            [void]$releaseNotesBuilder.AppendLine('```')
            [void]$releaseNotesBuilder.AppendLine("choco install glowstatus")
            [void]$releaseNotesBuilder.AppendLine('```')
            [void]$releaseNotesBuilder.AppendLine("")
            [void]$releaseNotesBuilder.AppendLine("**Package Information:**")
            [void]$releaseNotesBuilder.AppendLine("- [Chocolatey Package]($chocolateyPackageUrl)")
            [void]$releaseNotesBuilder.AppendLine("- Installs to: Program Files\GlowStatus")
            [void]$releaseNotesBuilder.AppendLine("- Creates desktop shortcut automatically")
            [void]$releaseNotesBuilder.AppendLine("- Easy updates with choco upgrade glowstatus")
            [void]$releaseNotesBuilder.AppendLine("")
            [void]$releaseNotesBuilder.AppendLine("### Manual Installation")
            [void]$releaseNotesBuilder.AppendLine("Download the executable from the assets below and run directly.")
            [void]$releaseNotesBuilder.AppendLine("")
            [void]$releaseNotesBuilder.AppendLine("## What's New in v$VERSION")
            [void]$releaseNotesBuilder.AppendLine("- Cross-platform status indicator system")
            [void]$releaseNotesBuilder.AppendLine("- Govee smart lights integration")
            [void]$releaseNotesBuilder.AppendLine("- Google Calendar synchronization")
            [void]$releaseNotesBuilder.AppendLine("- Perfect for home offices and remote work")
            [void]$releaseNotesBuilder.AppendLine("")
            [void]$releaseNotesBuilder.AppendLine("## Features")
            [void]$releaseNotesBuilder.AppendLine("- **Smart Presence Detection** - Automatically updates your status")
            [void]$releaseNotesBuilder.AppendLine("- **Govee Light Integration** - Visual status indicators using smart lights")
            [void]$releaseNotesBuilder.AppendLine("- **Google Calendar Sync** - Calendar-based status updates")
            [void]$releaseNotesBuilder.AppendLine("- **Easy Installation** - One-click Chocolatey package installation")
            [void]$releaseNotesBuilder.AppendLine("- **Auto-Updates** - Keep your installation current effortlessly")
            [void]$releaseNotesBuilder.AppendLine("")
            [void]$releaseNotesBuilder.AppendLine("## Support")
            [void]$releaseNotesBuilder.AppendLine("- [Report Issues](https://github.com/Severswoed/GlowStatus/issues)")
            [void]$releaseNotesBuilder.AppendLine("- [Documentation](https://github.com/Severswoed/GlowStatus/blob/main/README.md)")
            [void]$releaseNotesBuilder.AppendLine("- [Discussions](https://github.com/Severswoed/GlowStatus/discussions)")
            [void]$releaseNotesBuilder.AppendLine("")
            [void]$releaseNotesBuilder.AppendLine("## Quick Start")
            [void]$releaseNotesBuilder.AppendLine("1. Install via Chocolatey: choco install glowstatus")
            [void]$releaseNotesBuilder.AppendLine("2. Run GlowStatus from your desktop shortcut")
            [void]$releaseNotesBuilder.AppendLine("3. Configure your Govee lights and Google Calendar")
            [void]$releaseNotesBuilder.AppendLine("4. Enjoy automated status updates!")
            [void]$releaseNotesBuilder.AppendLine("")
            [void]$releaseNotesBuilder.AppendLine("This release includes the official Chocolatey package for easy installation and updates.")
            
            $releaseBody = $releaseNotesBuilder.ToString()
            
            $releaseData = @{
                tag_name = "v$VERSION"
                target_commitish = "main"
                name = "GlowStatus v$VERSION"
                body = $releaseBody
                draft = $false
                prerelease = ($VERSION -match "-")
            } | ConvertTo-Json -Depth 10
            
            try {
                $createUrl = "https://api.github.com/repos/Severswoed/GlowStatus/releases"
                $release = Invoke-RestMethod -Uri $createUrl -Headers $headers -Method Post -Body $releaseData -ContentType "application/json"
                Write-Host "✓ GitHub release v$VERSION created successfully!"
                Write-Host "  Release URL: $($release.html_url)"
            }
            catch {
                Write-Warning "Failed to create GitHub release: $($_.Exception.Message)"
                Write-Host "  You may need to create the release manually at:"
                Write-Host "  https://github.com/Severswoed/GlowStatus/releases/new"
                Write-Host "  Suggested release notes saved for manual use."
            }
        }
        else {
            Write-Warning "Error checking for existing release: $($_.Exception.Message)"
        }
    }
} else {
    Write-Warning "No GitHub token found - skipping release creation"
    Write-Host "  Manual action required:"
    Write-Host "  1. Go to https://github.com/Severswoed/GlowStatus/releases/new"
    Write-Host "  2. Create a new release with tag: v$VERSION"
    Write-Host "  3. Title: GlowStatus v$VERSION"
    Write-Host "  4. Include link to Chocolatey package: $chocolateyPackageUrl"
}

# Final summary
Write-Host "`n" + "="*50
Write-Host "BUILD SUMMARY"
Write-Host "="*50
Write-Host "Version: $VERSION"
Write-Host "Chocolatey Package: $(if($packageBuiltSuccessfully){"✓ Built"}else{"✗ Failed"})"
Write-Host "Chocolatey URL: $chocolateyPackageUrl"
Write-Host "GitHub Release: $(if($env:GITHUB_TOKEN){"Attempted"}else{"Skipped - no token"})"
Write-Host ""
Write-Host "Next Steps:"
if ($packageBuiltSuccessfully -and $env:CHOCO_APIKEY) {
    Write-Host "  ✓ Package should be available on Chocolatey Community shortly"
    Write-Host "  ✓ Users can install with: choco install glowstatus"
}
elseif ($packageBuiltSuccessfully) {
    Write-Host "  - Manually publish to Chocolatey Community"
    Write-Host "  - Set CHOCO_APIKEY environment variable for auto-publishing"
}
if (-not $env:GITHUB_TOKEN) {
    Write-Host "  - Set GITHUB_TOKEN environment variable for auto-releases"
    Write-Host "  - Or create GitHub release manually"
}
Write-Host ""

pause