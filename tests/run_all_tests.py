#!/usr/bin/env python3
"""
Test runner for GlowStatus tests.
Runs all tests and provides a summary.
"""

import unittest
import sys
import os
import subprocess

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def run_unit_tests():
    """Run the unittest-based tests."""
    print("="*60)
    print("RUNNING UNIT TESTS")
    print("="*60)
    
    test_files = [
        'test_main.py',
        'test_calendar_sync.py',
        'test_govee_controller.py'
    ]
    
    total_tests = 0
    total_failures = 0
    
    for test_file in test_files:
        print(f"\n--- Running {test_file} ---")
        
        # Get the tests directory
        test_dir = os.path.dirname(__file__)
        test_path = os.path.join(test_dir, test_file)
        
        if os.path.exists(test_path):
            # Load and run the test
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromName(f'tests.{test_file[:-3]}')
            runner = unittest.TextTestRunner(verbosity=1)
            result = runner.run(suite)
            
            total_tests += result.testsRun
            total_failures += len(result.failures) + len(result.errors)
            
            if result.failures:
                for test, traceback in result.failures:
                    print(f"FAILURE: {test}")
            
            if result.errors:
                for test, traceback in result.errors:
                    print(f"ERROR: {test}")
        else:
            print(f"Test file not found: {test_path}")
    
    return total_tests, total_failures


def run_script_tests():
    """Run the script-based tests."""
    print("\n" + "="*60)
    print("RUNNING SCRIPT-BASED TESTS")
    print("="*60)
    
    script_tests = [
        'test_status_detection.py',
        'test_status_fix.py',
        'test_timing_sync.py'
    ]
    
    test_dir = os.path.dirname(__file__)
    
    for script in script_tests:
        script_path = os.path.join(test_dir, script)
        if os.path.exists(script_path):
            print(f"\n--- Running {script} ---")
            try:
                # Use subprocess to run the script and capture output
                result = subprocess.run([sys.executable, script_path], 
                                      capture_output=True, text=True, 
                                      cwd=os.path.dirname(os.path.dirname(__file__)))
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print("STDERR:", result.stderr)
                if result.returncode == 0:
                    print("✅ PASSED")
                else:
                    print("❌ FAILED")
            except Exception as e:
                print(f"Error running {script}: {e}")


def main():
    """Main test runner function."""
    print("GlowStatus Test Suite")
    print("=" * 60)
    
    # Run unit tests
    total_tests, total_failures = run_unit_tests()
    
    # Run script tests
    run_script_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Unit tests run: {total_tests}")
    print(f"Unit test failures: {total_failures}")
    
    if total_failures == 0:
        print("🎉 All unit tests passed!")
    else:
        print(f"⚠️  {total_failures} unit test failures")
    
    print("\nTest Categories Covered:")
    print("✅ Utility functions (clamp_rgb, normalize_status, validation)")
    print("✅ Calendar sync functionality (OAuth, event parsing)")
    print("✅ Govee controller (API calls, device control)")
    print("✅ Status detection with custom keywords")
    print("✅ Timing synchronization for autostart")
    
    print("\nAll tests are organized under /tests directory")
    print("="*60)
    
    return total_failures == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
