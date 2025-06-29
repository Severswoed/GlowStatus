"""Helper functions for setup and build processes."""

import glob
import subprocess
import sys
import os
import site


def fix_google_namespace_packages():
    """Create __init__.py files for Google namespace packages if they don't exist."""
    try:
        import google
        google_path = os.path.dirname(google.__file__)
        
        # Ensure google/__init__.py exists
        google_init = os.path.join(google_path, '__init__.py')
        if not os.path.exists(google_init):
            print(f"Creating {google_init} for py2app compatibility...")
            with open(google_init, 'w') as f:
                f.write('# Namespace package\n__path__ = __import__("pkgutil").extend_path(__path__, __name__)\n')
        
        # Also check for any google.* subpackages
        for subdir in ['auth', 'oauth2']:
            subdir_path = os.path.join(google_path, subdir)
            if os.path.exists(subdir_path):
                subdir_init = os.path.join(subdir_path, '__init__.py')
                if not os.path.exists(subdir_init):
                    print(f"Creating {subdir_init} for py2app compatibility...")
                    with open(subdir_init, 'w') as f:
                        f.write('# Namespace package\n')
                        
    except ImportError:
        print("Google packages not found - skipping namespace fix")
    except Exception as e:
        print(f"Warning: Could not fix Google namespace packages: {e}")


def check_and_install_requirements():
    """Check if requirements are installed and install them if needed."""
    # Get the parent directory (project root) from the scripts directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    requirements_file = os.path.join(project_root, 'requirements.txt')
    
    if not os.path.exists(requirements_file):
        print(f"Warning: {requirements_file} not found, skipping dependency check")
        return
    
    print("Checking and installing requirements...")
    
    try:
        # Try pip3 first, then pip
        pip_cmd = 'pip3' if subprocess.run(['which', 'pip3'], capture_output=True).returncode == 0 else 'pip'
        
        # Install requirements
        result = subprocess.run([
            pip_cmd, 'install', '-r', requirements_file
        ], check=True, capture_output=True, text=True)
        
        print("✓ Requirements installed successfully")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        print(f"\n💡 Please run manually: {pip_cmd} install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error checking requirements: {e}")
        print(f"💡 Please run manually: {pip_cmd} install -r requirements.txt")


def verify_critical_modules():
    """Verify that critical modules can be imported."""
    print("🔍 Verifying critical modules...")
    critical_modules = [
        'PySide6.QtWidgets',
        'PySide6.QtCore', 
        'PySide6.QtGui',
        'keyring',
        'google.auth',
        'google_auth_oauthlib',
        'googleapiclient',
        'requests',
        'dateutil'
    ]
    
    failed_modules = []
    for module in critical_modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            failed_modules.append(module.split('.')[0])
    
    if failed_modules:
        unique_failed = list(set(failed_modules))
        pip_cmd = 'pip3' if subprocess.run(['which', 'pip3'], capture_output=True).returncode == 0 else 'pip'
        print(f"\n💡 Try installing missing modules: {pip_cmd} install {' '.join(unique_failed)}")
        return False
    
    print("✓ All critical modules verified")
    return True
