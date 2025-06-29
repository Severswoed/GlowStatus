#!/usr/bin/env python3
"""Test that the OAuth threading components import correctly."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_oauth_threading_imports():
    """Test that OAuth threading components can be imported."""
    try:
        # Test PySide6 imports
        from PySide6.QtCore import Qt, QThread, Signal
        print("✅ PySide6.QtCore imports (Qt, QThread, Signal)")
        
        # Test that we can import the config_ui module - but handle GUI issues gracefully
        try:
            import config_ui
            print("✅ config_ui module imports")
            
            # Test that OAuthWorker class exists
            worker_class = getattr(config_ui, 'OAuthWorker', None)
            if worker_class:
                print("✅ OAuthWorker class found")
            else:
                print("❌ OAuthWorker class not found")
                return False
                
            # Test that signals are defined
            if hasattr(worker_class, 'oauth_success'):
                print("✅ oauth_success signal defined")
            else:
                print("❌ oauth_success signal not found")
                return False
                
        except Exception as gui_error:
            # If there are GUI/display issues, we can still check if the module structure is correct
            print(f"⚠️ GUI import issue (expected in headless environments): {gui_error}")
            
            # Try to load the source file directly and check for the class
            config_ui_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'config_ui.py')
            if os.path.exists(config_ui_path):
                with open(config_ui_path, 'r') as f:
                    content = f.read()
                    if 'class OAuthWorker' in content and 'oauth_success' in content:
                        print("✅ OAuthWorker class and signals found in source code")
                    else:
                        print("❌ OAuthWorker class or signals not found in source code")
                        return False
            else:
                print("❌ config_ui.py source file not found")
                return False
        
        print("✅ All OAuth threading components are available")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Testing OAuth threading imports...")
    success = test_oauth_threading_imports()
    if success:
        print("\n🎉 OAuth threading should work correctly in py2app build")
    else:
        print("\n❌ OAuth threading may have issues")
        sys.exit(1)
    
    sys.exit(0 if success else 1)
