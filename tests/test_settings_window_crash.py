#!/usr/bin/env python3
"""
Diagnostic test to investigate settings window crash.
This will help identify what's causing the app to crash when opening settings.
"""

import sys
import os
import traceback
from unittest.mock import patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_settings_window_crash():
    """Test what causes the settings window to crash."""
    
    print("🔍 Testing Settings Window Crash")
    print("=" * 50)
    
    # Test 1: Can we import the settings module?
    try:
        print("📦 Testing imports...")
        from settings_ui import SettingsWindow, load_config, save_config
        print("   ✅ settings_ui import successful")
    except Exception as e:
        print(f"   ❌ settings_ui import failed: {e}")
        traceback.print_exc()
        return False
    
    # Test 2: Can we import Qt modules?
    try:
        print("🖼️ Testing Qt imports...")
        from PyQt5.QtWidgets import QApplication, QMainWindow
        from PyQt5.QtCore import Qt
        print("   ✅ PyQt5 import successful")
    except Exception as e:
        print(f"   ❌ PyQt5 import failed: {e}")
        traceback.print_exc()
        return False
    
    # Test 3: Can we create a QApplication?
    try:
        print("🚀 Testing QApplication creation...")
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        print("   ✅ QApplication created successfully")
    except Exception as e:
        print(f"   ❌ QApplication creation failed: {e}")
        traceback.print_exc()
        return False
    
    # Test 4: Can we load config?
    try:
        print("📄 Testing config loading...")
        config = load_config()
        print(f"   ✅ Config loaded: {len(config)} keys")
        print(f"   📝 Config keys: {list(config.keys())}")
    except Exception as e:
        print(f"   ❌ Config loading failed: {e}")
        traceback.print_exc()
        return False
    
    # Test 5: Can we create SettingsWindow?
    try:
        print("🏗️ Testing SettingsWindow creation...")
        
        # Mock the controller to avoid dependencies
        mock_controller = MagicMock()
        
        settings_window = SettingsWindow(mock_controller)
        print("   ✅ SettingsWindow created successfully")
        
        # Test showing the window
        print("👁️ Testing window show...")
        settings_window.show()
        print("   ✅ SettingsWindow show() successful")
        
        # Clean up
        settings_window.close()
        
    except Exception as e:
        print(f"   ❌ SettingsWindow creation/show failed: {e}")
        traceback.print_exc()
        
        # Get detailed error info
        print("\n🔍 Detailed error analysis:")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        print(f"   • Exception type: {exc_type.__name__}")
        print(f"   • Exception message: {str(exc_value)}")
        
        # Print the last few frames of the traceback
        print("   • Traceback (last 3 frames):")
        tb_lines = traceback.format_tb(exc_traceback)
        for line in tb_lines[-3:]:
            print(f"     {line.strip()}")
        
        return False
    
    return True


def test_specific_crash_scenarios():
    """Test specific scenarios that might cause crashes."""
    
    print("\n💥 Testing Specific Crash Scenarios")
    print("=" * 50)
    
    # Test corrupted config scenarios
    crash_configs = [
        # Scenario 1: Null values
        {"GOVEE_DEVICE_ID": None, "SELECTED_CALENDAR_ID": None},
        
        # Scenario 2: Invalid color map
        {"STATUS_COLOR_MAP": {"invalid": "not_a_dict"}},
        
        # Scenario 3: Missing required keys
        {},
        
        # Scenario 4: Invalid JSON structure
        {"STATUS_COLOR_MAP": "should_be_dict_not_string"},
    ]
    
    results = []
    
    for i, test_config in enumerate(crash_configs, 1):
        print(f"\n🧪 Crash Scenario #{i}: {list(test_config.keys())}")
        
        try:
            # Mock load_config to return the test config
            with patch('settings_ui.load_config') as mock_load_config:
                mock_load_config.return_value = test_config
                
                # Try to create QApplication if needed
                app = QApplication.instance()
                if app is None:
                    app = QApplication(sys.argv)
                
                # Mock controller
                mock_controller = MagicMock()
                
                # Try to create settings window
                from settings_ui import SettingsWindow
                settings_window = SettingsWindow(mock_controller)
                settings_window.show()
                settings_window.close()
                
                print(f"   ✅ Scenario #{i} passed")
                results.append(True)
                
        except Exception as e:
            print(f"   ❌ Scenario #{i} crashed: {e}")
            print(f"      Error type: {type(e).__name__}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    print(f"\n📊 Crash Scenario Results: {passed}/{total} passed")
    
    return passed == total


def test_tray_app_crash():
    """Test if the crash happens in tray app when opening settings."""
    
    print("\n🔧 Testing Tray App Settings Integration")
    print("=" * 50)
    
    try:
        # Import tray app
        from tray_app import show_settings
        print("   ✅ tray_app import successful")
        
        # Mock the controller and QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        mock_controller = MagicMock()
        
        # Test the show_settings function directly
        print("🏗️ Testing show_settings function...")
        
        # This function should create and show the settings window
        # We'll mock it to see where it might crash
        with patch('tray_app.SettingsWindow') as mock_settings_window:
            mock_window = MagicMock()
            mock_settings_window.return_value = mock_window
            
            # This should be the function called from tray menu
            show_settings()
            
            print("   ✅ show_settings function completed")
            
    except Exception as e:
        print(f"   ❌ Tray app settings test failed: {e}")
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    print("🩺 SETTINGS WINDOW CRASH DIAGNOSTIC")
    print("=" * 60)
    
    results = []
    
    # Test 1: Basic settings window creation
    try:
        result1 = test_settings_window_crash()
        results.append(("Settings Window Creation", result1))
    except Exception as e:
        print(f"❌ Settings window test failed: {e}")
        results.append(("Settings Window Creation", False))
    
    # Test 2: Crash scenarios
    try:
        result2 = test_specific_crash_scenarios()
        results.append(("Crash Scenarios", result2))
    except Exception as e:
        print(f"❌ Crash scenarios test failed: {e}")
        results.append(("Crash Scenarios", False))
    
    # Test 3: Tray app integration
    try:
        result3 = test_tray_app_crash()
        results.append(("Tray App Integration", result3))
    except Exception as e:
        print(f"❌ Tray app test failed: {e}")
        results.append(("Tray App Integration", False))
    
    print("\n📋 Final Crash Diagnostic Results:")
    print("=" * 40)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 No crashes detected in testing environment!")
        print("   The crash might be environment-specific or timing-related.")
    else:
        print("\n⚠️  Crashes detected! Review the detailed error output above.")
    
    print("\n🔧 Next steps if crashes persist:")
    print("   1. Check the app logs when the crash occurs")
    print("   2. Try running the app with --debug flag")
    print("   3. Check if it's a Qt version or display driver issue")
    print("   4. Verify all dependencies are properly installed")
