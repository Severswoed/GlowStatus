#!/usr/bin/env python3
"""
Test to verify that all modules correctly import and use TOKEN_PATH.
"""

import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

def test_token_path_imports():
    """Test that TOKEN_PATH is consistently imported across modules."""
    print("=== Testing TOKEN_PATH Imports ===")
    
    try:
        # Test constants.py
        from constants import TOKEN_PATH
        print(f"✓ constants.py: TOKEN_PATH = {TOKEN_PATH}")
        
        # Test that tray_app.py can import TOKEN_PATH
        # We can't run the full module due to PySide6 dependencies
        # But we can check that the import would work
        with open('/workspaces/GlowStatus/src/tray_app.py', 'r') as f:
            content = f.read()
            
        if 'from constants import TOKEN_PATH' in content:
            print("✓ tray_app.py: Correctly imports TOKEN_PATH from constants")
        else:
            print("✗ tray_app.py: Does not import TOKEN_PATH from constants")
            return False
            
        if 'os.path.exists(TOKEN_PATH)' in content:
            print("✓ tray_app.py: Uses TOKEN_PATH for token existence check")
        else:
            print("✗ tray_app.py: Does not use TOKEN_PATH for token check")
            return False
            
        # Verify path consistency
        expected_path = TOKEN_PATH
        if expected_path.endswith('config/google_token.pickle'):
            print("✓ TOKEN_PATH correctly points to config/google_token.pickle")
        else:
            print(f"✗ TOKEN_PATH points to unexpected location: {expected_path}")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Error testing TOKEN_PATH imports: {e}")
        return False

if __name__ == "__main__":
    success = test_token_path_imports()
    print(f"\nResult: {'✓ PASS' if success else '✗ FAIL'}")
    sys.exit(0 if success else 1)
