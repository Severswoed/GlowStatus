#!/usr/bin/env python3
"""
Test for Non-blocking OAuth Flow

This test verifies that the OAuth flow runs asynchronously and doesn't block the UI.

MANUAL TEST INSTRUCTIONS:
1. Start GlowStatus
2. Open Settings
3. Click "Sign in with Google"
4. The consent dialog should appear and be responsive
5. You should be able to click OK or Cancel
6. The OAuth button should show "Connecting..." and be disabled
7. Other UI elements should remain responsive
8. After OAuth completes, the button should be re-enabled

EXPECTED BEHAVIOR:
- Consent dialog is responsive (no spinning wheel)
- UI doesn't freeze during OAuth flow
- Button shows progress ("Connecting...")
- Success/error messages appear after completion
- All UI elements are re-enabled after OAuth finishes
"""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_oauth_worker_class_exists():
    """Test that the OAuthWorker class is properly defined."""
    try:
        # Import without initializing Qt
        import importlib.util
        spec = importlib.util.spec_from_file_location("config_ui", "../src/config_ui.py")
        
        # Check if OAuthWorker is defined in the source code
        with open("../src/config_ui.py", 'r') as f:
            content = f.read()
            
        assert "class OAuthWorker(QThread):" in content, "OAuthWorker class should be defined"
        assert "oauth_success = pyqtSignal" in content, "OAuth success signal should be defined"
        assert "oauth_error = pyqtSignal" in content, "OAuth error signal should be defined"
        assert "oauth_no_calendars = pyqtSignal" in content, "OAuth no calendars signal should be defined"
        
        # Check that the OAuth flow uses threading
        assert "self.oauth_worker = OAuthWorker()" in content, "OAuth worker should be instantiated"
        assert "self.oauth_worker.start()" in content, "OAuth worker should be started"
        assert "finished.connect" in content, "Finished signal should be connected"
        
        print("✅ OAuthWorker class is properly implemented")
        return True
        
    except Exception as e:
        print(f"❌ Error checking OAuthWorker implementation: {e}")
        return False

def test_oauth_method_structure():
    """Test that OAuth methods have proper structure."""
    try:
        with open("../src/config_ui.py", 'r') as f:
            content = f.read()
        
        # Check that consent dialog exists
        assert "consent_msg = QMessageBox" in content, "Consent dialog should exist"
        assert "if consent_msg.exec() != QMessageBox.Ok:" in content, "Should check consent dialog result"
        
        # Check that UI is disabled during OAuth
        assert "self.oauth_btn.setEnabled(False)" in content, "OAuth button should be disabled during flow"
        assert "self.save_btn.setEnabled(False)" in content, "Save button should be disabled during flow"
        
        # Check callback methods exist
        assert "def on_oauth_success" in content, "OAuth success callback should exist"
        assert "def on_oauth_error" in content, "OAuth error callback should exist"
        assert "def on_oauth_no_calendars" in content, "OAuth no calendars callback should exist"
        assert "def on_oauth_finished" in content, "OAuth finished callback should exist"
        
        # Check UI is re-enabled
        assert "self.oauth_btn.setEnabled(True)" in content, "OAuth button should be re-enabled"
        
        print("✅ OAuth method structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Error checking OAuth method structure: {e}")
        return False

def test_oauth_signals_connected():
    """Test that OAuth signals are properly connected."""
    try:
        with open("../src/config_ui.py", 'r') as f:
            content = f.read()
        
        # Check signal connections
        assert "oauth_success.connect(self.on_oauth_success)" in content, "Success signal should be connected"
        assert "oauth_error.connect(self.on_oauth_error)" in content, "Error signal should be connected"
        assert "oauth_no_calendars.connect(self.on_oauth_no_calendars)" in content, "No calendars signal should be connected"
        assert "finished.connect(self.on_oauth_finished)" in content, "Finished signal should be connected"
        
        print("✅ OAuth signals are properly connected")
        return True
        
    except Exception as e:
        print(f"❌ Error checking OAuth signal connections: {e}")
        return False

if __name__ == "__main__":
    print("Testing Non-blocking OAuth Flow Implementation...")
    print("=" * 60)
    
    all_tests_passed = True
    
    all_tests_passed &= test_oauth_worker_class_exists()
    all_tests_passed &= test_oauth_method_structure()
    all_tests_passed &= test_oauth_signals_connected()
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("✅ All tests passed! OAuth flow should be non-blocking.")
        print("\nNext steps:")
        print("1. Test manually by running GlowStatus")
        print("2. Open Settings and click 'Sign in with Google'")
        print("3. Verify the consent dialog is responsive")
        print("4. Check that UI doesn't freeze during OAuth")
    else:
        print("❌ Some tests failed. Please fix the OAuth implementation.")
    
    print("\nManual test instructions are in the file header.")
