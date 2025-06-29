#!/usr/bin/env python3
"""
Test script to verify the Govee API key loading bug fix.
This script tests that load_secret() can retrieve keys from keyring
after they've been saved via the UI.
"""

import os
import sys
import tempfile
import shutil

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from utils import load_secret

def test_keyring_functionality():
    """Test that keyring can store and retrieve secrets."""
    try:
        import keyring
        
        # Test saving and loading a secret
        test_key = "TEST_GOVEE_API_KEY"
        test_value = "abcdef1234567890test_api_key"
        
        print("Testing keyring functionality...")
        
        # Save the test key
        keyring.set_password("GlowStatus", test_key, test_value)
        print(f"✓ Saved test key '{test_key}' to keyring")
        
        # Try to load it using our load_secret function
        loaded_value = load_secret(test_key)
        
        if loaded_value == test_value:
            print(f"✓ Successfully loaded test key from keyring: {loaded_value}")
            
            # Clean up
            keyring.delete_password("GlowStatus", test_key)
            print("✓ Cleaned up test key from keyring")
            return True
        else:
            print(f"✗ Failed to load test key. Expected: {test_value}, Got: {loaded_value}")
            return False
            
    except ImportError:
        print("✗ Keyring module not available")
        return False
    except Exception as e:
        print(f"✗ Error testing keyring: {e}")
        return False

def test_environment_variable_precedence():
    """Test that environment variables take precedence over keyring."""
    try:
        import keyring
        
        test_key = "TEST_ENV_PRECEDENCE"
        keyring_value = "keyring_value"
        env_value = "env_value"
        
        print("\nTesting environment variable precedence...")
        
        # Save to keyring
        keyring.set_password("GlowStatus", test_key, keyring_value)
        
        # Set environment variable
        os.environ[test_key] = env_value
        
        # Test load_secret
        loaded_value = load_secret(test_key)
        
        if loaded_value == env_value:
            print(f"✓ Environment variable correctly takes precedence: {loaded_value}")
            success = True
        else:
            print(f"✗ Environment variable precedence failed. Expected: {env_value}, Got: {loaded_value}")
            success = False
        
        # Clean up
        del os.environ[test_key]
        keyring.delete_password("GlowStatus", test_key)
        print("✓ Cleaned up test data")
        
        return success
        
    except Exception as e:
        print(f"✗ Error testing environment variable precedence: {e}")
        return False

def test_govee_api_key_scenario():
    """Test the specific Govee API key scenario that was failing."""
    try:
        import keyring
        
        print("\nTesting Govee API key scenario...")
        
        # Simulate saving an API key like the UI would do
        api_key = "test_govee_api_key_12345678901234567890"
        keyring.set_password("GlowStatus", "GOVEE_API_KEY", api_key)
        print("✓ Simulated saving Govee API key via UI")
        
        # Now test loading it like the main app would do
        loaded_key = load_secret("GOVEE_API_KEY")
        
        if loaded_key == api_key:
            print(f"✓ Successfully loaded Govee API key: {loaded_key[:20]}...")
            success = True
        else:
            print(f"✗ Failed to load Govee API key. Expected: {api_key}, Got: {loaded_key}")
            success = False
        
        # Clean up
        keyring.delete_password("GlowStatus", "GOVEE_API_KEY")
        print("✓ Cleaned up test Govee API key")
        
        return success
        
    except Exception as e:
        print(f"✗ Error testing Govee API key scenario: {e}")
        return False

def main():
    """Run all tests to verify the bug fix."""
    print("=== Govee API Key Loading Bug Fix Verification ===")
    print("This tests the fix for the issue where load_secret() only checked")
    print("environment variables but not keyring, causing the app to not find")
    print("Govee API keys saved via the UI.\n")
    
    tests = [
        test_keyring_functionality,
        test_environment_variable_precedence,
        test_govee_api_key_scenario
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n=== Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! The bug fix is working correctly.")
        print("✓ load_secret() now properly checks both environment variables and keyring.")
        return True
    else:
        print("✗ Some tests failed. The bug fix may not be working correctly.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
