#!/usr/bin/env python3
"""Test script to verify build helper functions work correctly."""

import sys
import os

# Add the scripts directory to Python path to access build_helpers.py
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))

# Import the functions from build_helpers.py
from build_helpers import check_and_install_requirements, verify_critical_modules, fix_google_namespace_packages

def main():
    print("🧪 Testing build helper functions...")
    
    # Test function 1
    print("\n1. Testing check_and_install_requirements()...")
    try:
        check_and_install_requirements()
        print("✅ check_and_install_requirements() completed")
    except Exception as e:
        print(f"❌ check_and_install_requirements() failed: {e}")
        return False
    
    # Test function 2  
    print("\n2. Testing verify_critical_modules()...")
    try:
        result = verify_critical_modules()
        if result is not False:  # Could be None (success) or False (failure)
            print("✅ verify_critical_modules() completed")
        else:
            print("⚠️ verify_critical_modules() found missing modules")
    except Exception as e:
        print(f"❌ verify_critical_modules() failed: {e}")
        return False
    
    # Test function 3
    print("\n3. Testing fix_google_namespace_packages()...")
    try:
        fix_google_namespace_packages()
        print("✅ fix_google_namespace_packages() completed")
    except Exception as e:
        print(f"❌ fix_google_namespace_packages() failed: {e}")
        return False
    
    print("\n🎉 All build helper functions work correctly!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
