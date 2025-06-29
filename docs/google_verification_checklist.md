# Google OAuth Verification Checklist for GlowStatus
# ===================================================

## COMPLETED ✅
- [x] OAuth 2.0 implementation with PKCE (InstalledAppFlow)
- [x] Limited scope: calendar.readonly only
- [x] Google branding on OAuth button
- [x] User consent dialog with clear data usage explanation
- [x] Privacy notice with policy links
- [x] Secure credential handling (gitignore protection)
- [x] Disconnect/revoke functionality
- [x] Error handling and fallback mechanisms
- [x] Cross-platform compatibility
- [x] Google Limited Use compliance statements

## TODO BEFORE VERIFICATION 📋
- [ ] Deploy live Privacy Policy at https://www.glowstatus.app/privacy
- [ ] Deploy live Terms of Service at https://www.glowstatus.app/terms
- [ ] Replace template client_secret.json with real Google Cloud Console credentials
- [ ] Configure OAuth consent screen in Google Cloud Console
- [ ] Add domain verification in Google Cloud Console
- [ ] Test complete OAuth flow with real credentials
- [ ] Verify privacy policy contains all required sections per Google policy

## GOOGLE CLOUD CONSOLE SETUP REQUIRED
1. Create OAuth 2.0 credentials for desktop application
2. Configure OAuth consent screen with:
   - App name: GlowStatus
   - User support email
   - Developer contact information
   - App domain: glowstatus.app
   - Privacy policy link: https://www.glowstatus.app/privacy
   - Terms of service link: https://www.glowstatus.app/terms
3. Add scopes: calendar.readonly
4. Download client_secret.json and replace template

## VERIFICATION SUBMISSION REQUIREMENTS
- App must be functional with OAuth flow
- Privacy policy must be comprehensive and accessible
- Terms of service must be accessible
- App must handle errors gracefully
- Must demonstrate compliance with Google's Limited Use policy
- All branding must follow Google's guidelines

## POST-VERIFICATION
- Monitor for any compliance issues
- Keep privacy policy up to date
- Renew verification as required
- Monitor for any Google policy updates
