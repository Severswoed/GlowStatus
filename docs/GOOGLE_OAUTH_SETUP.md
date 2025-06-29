# Google Cloud Console OAuth Setup Guide
# =====================================
# Complete step-by-step guide for setting up Google OAuth for GlowStatus

## Prerequisites
- Google account with access to Google Cloud Console
- Domain ownership of glowstatus.app (already configured)
- Privacy Policy and Terms of Service live at:
  - https://www.glowstatus.app/privacy
  - https://www.glowstatus.app/terms

## Step 1: Create Google Cloud Project
1. Go to https://console.cloud.google.com/
2. Click "New Project" or select existing project
3. Project name: "GlowStatus"
4. Note the Project ID for later use

## Step 2: Enable Google Calendar API
1. In Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google Calendar API"
3. Click on it and press "Enable"

## Step 3: Configure OAuth Consent Screen
1. Go to "APIs & Services" > "OAuth consent screen"
2. Choose "External" user type (unless you have Google Workspace)
3. Fill out the form:

### App Information
- **App name:** GlowStatus
- **User support email:** [your-email@domain.com]
- **App logo:** Upload GlowStatus logo (optional but recommended)

### App Domain
- **Application home page:** https://www.glowstatus.app
- **Application privacy policy link:** https://www.glowstatus.app/privacy
- **Application terms of service link:** https://www.glowstatus.app/terms

### Authorized Domains
- Add: `glowstatus.app`

### Developer Contact Information
- **Email addresses:** [your-email@domain.com]

### Scopes
1. Click "Add or Remove Scopes"
2. Add: `https://www.googleapis.com/auth/calendar.readonly`
3. This scope allows read-only access to calendar events

### Test Users (for development)
- Add your own email for testing before verification

## Step 4: Create OAuth Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Application type: "Desktop application"
4. Name: "GlowStatus Desktop Client"
5. Click "Create"
6. Download the JSON file as `client_secret.json`

## Step 5: Replace Template Credentials
1. Replace `/workspaces/GlowStatus/resources/client_secret.json` with the downloaded file
2. Verify the format matches:
```json
{
  "installed": {
    "client_id": "your-actual-client-id.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "your-actual-client-secret",
    "redirect_uris": ["http://localhost"]
  }
}
```

## Step 6: Test OAuth Flow
1. Build and run GlowStatus
2. Open Settings
3. Click "Check OAuth Verification Readiness"
4. Address any issues found
5. Test "Sign in with Google" button
6. Verify calendar access works correctly

## Step 7: Prepare for Verification
1. Ensure app is fully functional
2. Test all OAuth flows (connect, disconnect, error handling)
3. Verify privacy policy is comprehensive
4. Test on multiple platforms (Windows/macOS)
5. Document any sensitive scopes usage (calendar.readonly is generally approved)

## Step 8: Submit for Verification (if required)
1. In Google Cloud Console, go to "OAuth consent screen"
2. Click "Publish App" if still in testing mode
3. If your app needs verification (depends on usage and scopes), submit for review
4. Provide detailed explanations of how you use calendar data
5. Wait for Google's review (can take several days)

## Verification Requirements Checklist
- [x] ✅ Privacy policy accessible and comprehensive
- [x] ✅ Terms of service accessible
- [x] ✅ OAuth consent screen properly configured
- [x] ✅ Limited scope usage (calendar.readonly only)
- [x] ✅ Google branding guidelines followed
- [x] ✅ User consent and control implemented
- [x] ✅ Secure credential handling
- [x] ✅ Error handling implemented
- [ ] 🔄 Real OAuth credentials configured
- [ ] 🔄 End-to-end testing completed
- [ ] 🔄 Multi-platform testing completed

## Notes
- Calendar.readonly scope typically doesn't require verification for personal use
- Verification may be required if distributing publicly or using sensitive scopes
- Keep credentials secure and never commit real client_secret.json to version control
- Monitor Google's OAuth policies for any changes

## Support Resources
- Google OAuth 2.0 Documentation: https://developers.google.com/identity/protocols/oauth2
- Google API Console: https://console.developers.google.com/
- OAuth Verification Requirements: https://support.google.com/cloud/answer/13464321
