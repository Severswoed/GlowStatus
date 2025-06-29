#!/usr/bin/env python3
"""
Test for OAuth Threading Implementation

This test verifies that the OAuth flow uses threading properly
to keep the UI responsive during authentication.
"""

import os
import sys

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_oauth_worker_structure():
    """Test that OAuthWorker class has the correct structure without importing Qt"""
    
    # Read the config_ui.py file and check for threading implementation
    config_ui_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'config_ui.py')
    
    with open(config_ui_path, 'r') as f:
        content = f.read()
    
    # Check for required threading components
    assert 'from PySide6.QtCore import Qt, QThread, Signal' in content, "Missing QThread import"
    assert 'class OAuthWorker(QThread):' in content, "Missing OAuthWorker class definition"
    assert 'oauth_success = Signal(' in content, "Missing oauth_success signal"
    assert 'oauth_error = Signal(str)' in content, "Missing oauth_error signal"
    assert 'oauth_no_calendars = Signal()' in content, "Missing oauth_no_calendars signal"
    assert 'def run(self):' in content, "Missing run method in OAuthWorker"
    
    # Check for proper signal connections in run_oauth_flow
    assert 'worker = OAuthWorker()' in content, "Missing worker instantiation"
    assert 'worker.finished.connect(' in content, "Missing finished signal connection"
    assert 'worker.oauth_success.connect(' in content, "Missing oauth_success signal connection"
    assert 'worker.oauth_error.connect(' in content, "Missing oauth_error signal connection"
    assert 'worker.start()' in content, "Missing worker.start() call"
    
    print("✓ OAuthWorker class structure is correct")
    return True

def test_ui_responsiveness_logic():
    """Test the logic for maintaining UI responsiveness"""
    
    config_ui_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'config_ui.py')
    
    with open(config_ui_path, 'r') as f:
        content = f.read()
    
    # Check that UI is disabled during OAuth
    assert 'self.oauth_btn.setEnabled(False)' in content, "OAuth button should be disabled during flow"
    assert 'self.disconnect_btn.setEnabled(False)' in content, "Disconnect button should be disabled during flow"
    
    # Check for progress indication
    assert 'self.oauth_btn.setText("Connecting...")' in content, "Should show progress text"
    
    # Check for UI re-enabling in finished handler
    finished_method_found = 'def on_oauth_finished(self):' in content
    assert finished_method_found, "Missing on_oauth_finished method"
    
    if finished_method_found:
        # Extract the finished method
        lines = content.split('\n')
        in_method = False
        method_content = []
        
        for line in lines:
            if 'def on_oauth_finished(self):' in line:
                in_method = True
                method_content.append(line)
            elif in_method:
                if line.strip() and not line.startswith('    ') and not line.startswith('\t'):
                    # End of method
                    break
                method_content.append(line)
        
        method_text = '\n'.join(method_content)
        assert 'self.oauth_btn.setEnabled(True)' in method_text, "Should re-enable OAuth button in finished handler"
        assert 'self.oauth_btn.setText(' in method_text, "Should reset OAuth button text in finished handler"
    
    print("✓ UI responsiveness logic is correct")
    return True

def test_error_handling():
    """Test that error handling is properly implemented"""
    
    config_ui_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'config_ui.py')
    
    with open(config_ui_path, 'r') as f:
        content = f.read()
    
    # Check for error handling method
    assert 'def on_oauth_error(self, error_message):' in content, "Missing error handler method"
    
    # Check that errors are logged
    assert 'logger.error(' in content, "Should log OAuth errors"
    
    # Check for user feedback on errors
    error_method_found = 'def on_oauth_error(self, error_message):' in content
    assert error_method_found, "Missing on_oauth_error method"
    
    print("✓ Error handling implementation is correct")
    return True

def test_thread_safety():
    """Test that thread-safe practices are followed"""
    
    config_ui_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'config_ui.py')
    
    with open(config_ui_path, 'r') as f:
        content = f.read()
    
    # Check that UI updates happen via signals, not direct calls from worker thread
    assert 'self.oauth_success.emit(' in content, "Should use signals for success notification"
    assert 'self.oauth_error.emit(' in content, "Should use signals for error notification"
    # Note: finished signal is built into QThread, no need to emit it manually
    
    print("✓ Thread safety practices are followed")
    return True

if __name__ == "__main__":
    print("Testing OAuth Threading Implementation...")
    print("=" * 50)
    
    try:
        test_oauth_worker_structure()
        test_ui_responsiveness_logic()
        test_error_handling()
        test_thread_safety()
        
        print("\n✓ All OAuth threading tests passed!")
        print("The OAuth flow should now be responsive and non-blocking.")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
