#!/bin/bash

# This script creates GitHub issues for GlowStatus v2 using GitHub CLI (gh).
# Assumes you're running inside a GitHub Codespace with repo access.

create_issue() {
  TITLE=$1
  BODY=$2
  LABELS=$3

  gh issue create --title "$TITLE" --body "$BODY" --label "$LABELS"
}

# 1. Standalone Testing
create_issue "Test v2 Windows standalone .exe on clean environment" \
  "For GlowStatus v2, use a clean Windows VM (no Python installed) to validate the PyInstaller-built .exe." \
  "windows,testing"

create_issue "Test v2 macOS .app bundle on a new user account" \
  "For GlowStatus v2, test the .app bundle on a separate Mac profile to simulate a fresh install." \
  "mac,testing"

# 2. User Experience
create_issue "Improve v2 first-run experience wizard" \
  "In GlowStatus v2, guide users through API key and Google OAuth setup on first launch." \
  "ux,enhancement"

create_issue "Improve v2 error handling for missing config/auth" \
  "In GlowStatus v2, display user-facing messages for missing Govee key, OAuth failure, or config issues." \
  "ux,bug"

create_issue "Add v2 Windows installer using Inno Setup" \
  "Package GlowStatus v2 with a .exe installer using Inno Setup with proper shortcuts and uninstall support." \
  "windows,installer"

create_issue "Package v2 macOS app as DMG" \
  "Distribute GlowStatus v2 as signed DMG for user-friendly installation." \
  "mac,installer"

# 3. Code Signing
create_issue "Sign v2 Windows .exe to avoid SmartScreen warnings" \
  "Use a code-signing certificate to sign the GlowStatus v2 executable." \
  "windows,security"

create_issue "Notarize GlowStatus v2 macOS .app with Apple" \
  "Use Apple Developer credentials to notarize and staple the macOS app bundle for GlowStatus v2." \
  "mac,security"

# 4. Google OAuth
create_issue "Configure OAuth consent screen for GlowStatus v2" \
  "Set up branding, scopes, and app info in Google Cloud Console for v2." \
  "google-oauth,security"

create_issue "Add privacy policy and TOS for GlowStatus v2" \
  "Publish via GitHub Pages or simple web host to support OAuth verification for v2." \
  "docs,compliance"

create_issue "Record usage video for Google OAuth verification (v2)" \
  "Demonstrate how GlowStatus v2 uses Google Calendar API to fulfill OAuth requirements." \
  "google-oauth,compliance"

create_issue "Submit GlowStatus v2 for Google OAuth verification" \
  "Complete verification process and respond to any Google feedback for v2 release." \
  "google-oauth,compliance"

# 5. Documentation
create_issue "Update GlowStatus v2 README with install and troubleshooting" \
  "Include setup steps for Windows and macOS, API key config, and troubleshooting common errors." \
  "docs"

create_issue "Publish privacy policy and support contact for v2" \
  "Link a GitHub Pages site in the README for GlowStatus v2 privacy and support." \
  "docs,compliance"

create_issue "Create GitHub Pages site for GlowStatus v2" \
  "Simple landing page for GlowStatus v2 with downloads, documentation, and support info." \
  "website,docs"

# 6. Feedback Loop
create_issue "Share GlowStatus v2 builds with early testers" \
  "Distribute v2 builds and gather feedback on UX, setup flow, and bug reports." \
  "feedback,beta"

create_issue "Incorporate early tester feedback into GlowStatus v2" \
  "Prioritize and resolve feedback items from GlowStatus v2 early users." \
  "feedback,enhancement"

# 7. Release
create_issue "Publish GlowStatus v2 installers to GitHub Releases" \
  "Upload the signed Windows .exe and notarized macOS .app with release notes." \
  "release"

create_issue "Announce GlowStatus v2 public release" \
  "Post launch announcement and demo across GitHub, LinkedIn, and social media." \
  "release,marketing"
