## OAuth Flow Fixed: Non-blocking UI Implementation

### Problem
The OAuth consent dialog was becoming unresponsive with a spinning wheel because the OAuth flow was running synchronously on the main UI thread, blocking all user interaction.

### Solution
**Implemented asynchronous OAuth flow using QThread:**

1. **Created `OAuthWorker` class** that inherits from `QThread`
2. **Moved OAuth API calls to worker thread** to prevent UI blocking
3. **Added signal-slot communication** between worker and main thread
4. **Proper UI state management** during OAuth flow

### Key Changes Made

1. **Added QThread import**: `from PySide6.QtCore import Qt, QThread, pyqtSignal`

2. **Created OAuthWorker class** with signals:
   - `oauth_success` - emitted when OAuth succeeds with user email and calendars
   - `oauth_error` - emitted when OAuth fails with error message
   - `oauth_no_calendars` - emitted when OAuth succeeds but no calendars found

3. **Updated `run_oauth_flow()` method**:
   - Shows consent dialog (remains synchronous for user interaction)
   - Disables UI elements during OAuth flow
   - Starts worker thread instead of blocking main thread

4. **Added callback methods**:
   - `on_oauth_success()` - handles successful authentication
   - `on_oauth_error()` - handles authentication errors  
   - `on_oauth_no_calendars()` - handles success with no calendars
   - `on_oauth_finished()` - re-enables UI elements and cleans up worker

### Expected Behavior Now

✅ **Consent dialog is responsive** - no spinning wheel, can click OK/Cancel/Close
✅ **UI doesn't freeze** - other elements remain interactive during OAuth
✅ **Progress indication** - OAuth button shows "Connecting..." and is disabled
✅ **Proper cleanup** - UI elements re-enabled after OAuth completes
✅ **Clear feedback** - success/error messages after authentication

### Testing Instructions

1. **Start GlowStatus** with your real `client_secret.json` in place
2. **Open Settings window**
3. **Click "Sign in with Google"**
4. **Verify consent dialog is responsive** - you should be able to:
   - Click OK or Cancel without delay
   - Close the dialog if needed
   - No spinning wheel should appear
5. **Check OAuth button** shows "Connecting..." and is disabled
6. **Verify other UI elements** remain interactive
7. **Complete or cancel OAuth flow** and verify appropriate messages appear
8. **Check all UI elements** are re-enabled after completion

### Files Modified
- `src/config_ui.py` - Added OAuthWorker class and updated OAuth flow

### Tests Added
- `tests/test_oauth_nonblocking.py` - Verifies threading implementation

The OAuth flow should now be completely non-blocking and user-friendly!
