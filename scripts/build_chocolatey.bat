@echo off
echo GlowStatus Chocolatey Package Builder
echo ====================================

set VERSION=%1
if "%VERSION%"=="" (
    echo Usage: build_chocolatey.bat [version]
    echo Example: build_chocolatey.bat 1.0.0
    exit /b 1
)

echo Building version: %VERSION%

echo.
echo Step 1: Building Windows executable...
call scripts\build_windows.bat

if not exist "dist\GlowStatus\GlowStatus.exe" (
    echo ✗ Windows build failed - executable not found
    exit /b 1
)

echo ✓ Windows build successful!

echo.
echo Step 2: Creating Chocolatey package structure...
if exist chocolatey rmdir /s /q chocolatey
mkdir chocolatey\glowstatus\tools

echo Copying executable and dependencies...
xcopy "dist\GlowStatus\*" "chocolatey\glowstatus\tools\" /E /I /Y

echo.
echo Step 3: Creating nuspec file...
(
echo ^<?xml version="1.0" encoding="utf-8"?^>
echo ^<package xmlns="http://schemas.microsoft.com/packaging/2015/06/nuspec.xsd"^>
echo   ^<metadata^>
echo     ^<id^>glowstatus^</id^>
echo     ^<version^>%VERSION%^</version^>
echo     ^<packageSourceUrl^>https://github.com/Severswoed/GlowStatus^</packageSourceUrl^>
echo     ^<owners^>Severswoed^</owners^>
echo     ^<title^>GlowStatus^</title^>
echo     ^<authors^>Severswoed^</authors^>
echo     ^<projectUrl^>https://github.com/Severswoed/GlowStatus^</projectUrl^>
echo     ^<iconUrl^>https://raw.githubusercontent.com/Severswoed/GlowStatus/main/img/GlowStatus.png^</iconUrl^>
echo     ^<copyright^>2024-2025 Severswoed^</copyright^>
echo     ^<licenseUrl^>https://github.com/Severswoed/GlowStatus/blob/main/LICENSE^</licenseUrl^>
echo     ^<requireLicenseAcceptance^>false^</requireLicenseAcceptance^>
echo     ^<docsUrl^>https://github.com/Severswoed/GlowStatus/blob/main/README.md^</docsUrl^>
echo     ^<bugTrackerUrl^>https://github.com/Severswoed/GlowStatus/issues^</bugTrackerUrl^>
echo     ^<tags^>govee smart-lights calendar status-indicator productivity remote-work^</tags^>
echo     ^<summary^>Smart Presence Indicator with Govee + Google Calendar^</summary^>
echo     ^<description^>GlowStatus is a cross-platform status indicator system that syncs your Govee smart lights with your Google Calendar, showing your availability at a glance. Perfect for home offices, shared spaces, and remote work.^</description^>
echo     ^<releaseNotes^>https://github.com/Severswoed/GlowStatus/releases/tag/v%VERSION%^</releaseNotes^>
echo   ^</metadata^>
echo   ^<files^>
echo     ^<file src="tools/**" target="tools" /^>
echo   ^</files^>
echo ^</package^>
) > chocolatey\glowstatus\glowstatus.nuspec

echo.
echo Step 4: Creating install script...
(
echo $ErrorActionPreference = 'Stop'
echo.
echo $packageName = 'glowstatus'
echo $toolsDir = Split-Path -parent $MyInvocation.MyCommand.Definition
echo $exePath = Join-Path $toolsDir 'GlowStatus.exe'
echo.
echo # Create desktop shortcut
echo $desktopPath = [Environment]::GetFolderPath('Desktop'^)
echo $shortcutPath = Join-Path $desktopPath 'GlowStatus.lnk'
echo.
echo $WshShell = New-Object -comObject WScript.Shell
echo $Shortcut = $WshShell.CreateShortcut($shortcutPath^)
echo $Shortcut.TargetPath = $exePath
echo $Shortcut.WorkingDirectory = $toolsDir
echo $Shortcut.Description = 'GlowStatus - Smart Presence Indicator'
echo $Shortcut.Save(^)
echo.
echo Write-Host "GlowStatus installed successfully! Desktop shortcut created."
) > chocolatey\glowstatus\tools\chocolateyinstall.ps1

echo.
echo Step 5: Creating uninstall script...
(
echo $ErrorActionPreference = 'Stop'
echo.
echo # Remove desktop shortcut
echo $desktopPath = [Environment]::GetFolderPath('Desktop'^)
echo $desktopShortcut = Join-Path $desktopPath 'GlowStatus.lnk'
echo if (Test-Path $desktopShortcut^) {
echo     Remove-Item $desktopShortcut -Force
echo     Write-Host "Removed desktop shortcut"
echo }
echo.
echo # Stop any running processes
echo Get-Process -Name "GlowStatus" -ErrorAction SilentlyContinue ^| Stop-Process -Force
echo.
echo Write-Host "GlowStatus uninstalled successfully!"
) > chocolatey\glowstatus\tools\chocolateyuninstall.ps1

echo.
echo Step 6: Building Chocolatey package...
cd chocolatey\glowstatus
choco pack

if exist "glowstatus.%VERSION%.nupkg" (
    echo.
    echo ✓ Chocolatey package created successfully!
    echo ✓ Package: chocolatey\glowstatus\glowstatus.%VERSION%.nupkg
    echo.
    echo To test the package locally:
    echo   choco install glowstatus -s . -y --force
    echo.
    echo To publish to Chocolatey Community:
    echo   choco push glowstatus.%VERSION%.nupkg --source https://push.chocolatey.org/
) else (
    echo ✗ Chocolatey package creation failed
    exit /b 1
)

cd ..\..
pause
