#!/usr/bin/env python3
"""
Test suite for OAuth token robustness - ensures the app doesn't crash with invalid/expired tokens.
"""

import os
import sys
import tempfile
import shutil
import json
import pickle
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_calendar_sync_with_invalid_token():
    """Test that CalendarSync handles invalid/expired tokens gracefully."""
    print("Testing CalendarSync with invalid token...")
    
    # Create a temporary token file with invalid data
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pickle') as tmp_token:
        # Write invalid pickle data
        tmp_token.write(b'invalid_token_data')
        tmp_token_path = tmp_token.name
    
    try:
        # Mock the constants to use our temp token file
        with patch('calendar_sync.TOKEN_PATH', tmp_token_path):
            with patch('calendar_sync.CLIENT_SECRET_PATH', '/fake/path/client_secret.json'):
                from calendar_sync import CalendarSync
                
                # This should not crash, even with invalid token
                cal_sync = CalendarSync("primary")
                
                # Service should be None due to invalid token
                assert cal_sync.service is None, "Service should be None with invalid token"
                
                # get_current_status should return "offline" gracefully
                status = cal_sync.get_current_status()
                assert status == "offline", f"Expected 'offline', got '{status}'"
                
                print("✓ CalendarSync handles invalid token gracefully")
    finally:
        os.unlink(tmp_token_path)

def test_calendar_sync_with_expired_token():
    """Test that CalendarSync handles expired tokens gracefully."""
    print("Testing CalendarSync with expired token...")
    
    # Create a mock expired credentials object
    mock_creds = MagicMock()
    mock_creds.valid = False
    mock_creds.expired = True
    mock_creds.refresh_token = None
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pickle') as tmp_token:
        # Write expired credentials
        pickle.dump(mock_creds, tmp_token)
        tmp_token_path = tmp_token.name
    
    try:
        with patch('calendar_sync.TOKEN_PATH', tmp_token_path):
            with patch('calendar_sync.CLIENT_SECRET_PATH', '/fake/path/client_secret.json'):
                from calendar_sync import CalendarSync
                
                # This should not crash with expired token
                cal_sync = CalendarSync("primary")
                
                # Service should be None due to expired token with no refresh capability
                assert cal_sync.service is None, "Service should be None with expired token"
                
                status = cal_sync.get_current_status()
                assert status == "offline", f"Expected 'offline', got '{status}'"
                
                print("✓ CalendarSync handles expired token gracefully")
    finally:
        os.unlink(tmp_token_path)

def test_glowstatus_controller_with_bad_token():
    """Test that GlowStatusController handles calendar authentication failures gracefully."""
    print("Testing GlowStatusController with authentication failures...")
    
    # Create temporary config directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = os.path.join(tmp_dir, 'test_config.json')
        
        # Create test config with calendar sync enabled
        test_config = {
            "SELECTED_CALENDAR_ID": "test@example.com",
            "DISABLE_CALENDAR_SYNC": False,
            "DISABLE_LIGHT_CONTROL": True,  # Disable light control for testing
            "STATUS_COLOR_MAP": {
                "available": {"color": "0,255,0", "power_off": True},
                "in_meeting": {"color": "255,0,0", "power_off": False}
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
        
        # Mock the config loading functions
        with patch('config_ui.CONFIG_PATH', config_path):
            with patch('glowstatus.load_config') as mock_load_config:
                with patch('glowstatus.save_config') as mock_save_config:
                    mock_load_config.return_value = test_config.copy()
                    
                    # Mock CalendarSync to raise an authentication error
                    with patch('glowstatus.CalendarSync') as mock_calendar_sync:
                        mock_calendar_sync.side_effect = Exception("invalid_grant: Token has been expired or revoked")
                        
                        from glowstatus import GlowStatusController
                        
                        controller = GlowStatusController()
                        
                        # This should not crash, even with authentication failure
                        try:
                            controller.update_now()
                            print("✓ GlowStatusController.update_now() handles auth failure gracefully")
                        except Exception as e:
                            print(f"✗ GlowStatusController.update_now() crashed: {e}")
                            raise
                        
                        # Verify that calendar sync was auto-disabled
                        save_calls = mock_save_config.call_args_list
                        if save_calls:
                            saved_config = save_calls[-1][0][0]  # Get the config from the last save call
                            assert saved_config.get("DISABLE_CALENDAR_SYNC") == True, "Calendar sync should be auto-disabled after auth failure"
                            print("✓ Calendar sync auto-disabled after authentication failure")

def test_config_ui_with_bad_token():
    """Test that config UI handles authentication failures gracefully."""
    print("Testing config UI with authentication failures...")
    
    # Mock the calendar loading to simulate auth failure
    with patch('config_ui.CalendarSync') as mock_calendar_sync:
        mock_calendar_sync.side_effect = Exception("invalid_grant: Token has been expired or revoked")
        
        from settings_ui import SettingsWindow
        
        # Mock QApplication and other Qt dependencies for headless testing
        with patch('config_ui.QWidget'):
            with patch('config_ui.load_config') as mock_load_config:
                mock_load_config.return_value = {
                    "SELECTED_CALENDAR_ID": "test@example.com",
                    "DISABLE_CALENDAR_SYNC": False
                }
                
                try:
                    # Create config window - this should not crash
                    window = ConfigWindow()
                    
                    # Call load_calendars directly - this should not crash
                    window.load_calendars()
                    
                    print("✓ Config UI handles authentication failure gracefully")
                except Exception as e:
                    print(f"✗ Config UI crashed: {e}")
                    raise

def test_oauth_worker_with_bad_token():
    """Test that OAuth worker handles authentication failures gracefully."""
    print("Testing OAuth worker with authentication failures...")
    
    from settings_ui import OAuthWorker
    
    # Mock CalendarSync to raise an authentication error
    with patch('config_ui.CalendarSync') as mock_calendar_sync:
        mock_calendar_sync.side_effect = Exception("invalid_grant: Token has been expired or revoked")
        
        worker = OAuthWorker()
        
        # Track emitted signals
        error_emitted = []
        worker.oauth_error.connect(lambda msg: error_emitted.append(msg))
        
        try:
            # Run the OAuth worker - this should not crash
            worker.run()
            
            # Verify error signal was emitted
            assert len(error_emitted) == 1, "OAuth error signal should be emitted"
            assert "invalid_grant" in error_emitted[0], "Error message should contain authentication failure details"
            
            print("✓ OAuth worker handles authentication failure gracefully")
        except Exception as e:
            print(f"✗ OAuth worker crashed: {e}")
            raise

def run_all_tests():
    """Run all token robustness tests."""
    print("=" * 60)
    print("OAUTH TOKEN ROBUSTNESS TESTS")
    print("=" * 60)
    
    tests = [
        test_calendar_sync_with_invalid_token,
        test_calendar_sync_with_expired_token,
        test_glowstatus_controller_with_bad_token,
        test_config_ui_with_bad_token,
        test_oauth_worker_with_bad_token
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        sys.exit(1)
    else:
        print("All token robustness tests passed! 🎉")

if __name__ == "__main__":
    run_all_tests()
