"""Helper functions for setup and build processes."""

import glob
import subprocess
import sys
import os
import site


def fix_google_namespace_packages():
    """Create __init__.py files for Google namespace packages if they don't exist."""
    try:
        # Try to find google packages through different import paths
        google_path = None
        
        # Try different ways to find google packages
        for module_name in ['google', 'google_auth_oauthlib', 'googleapiclient']:
            try:
                module = __import__(module_name)
                if hasattr(module, '__file__') and module.__file__:
                    potential_google_path = os.path.dirname(module.__file__)
                    # For google_auth_oauthlib, we need to go up to find the google directory
                    if module_name == 'google_auth_oauthlib':
                        site_packages = os.path.dirname(potential_google_path)
                        google_path = os.path.join(site_packages, 'google')
                    elif module_name == 'googleapiclient':
                        site_packages = os.path.dirname(potential_google_path)
                        google_path = os.path.join(site_packages, 'google')
                    else:
                        google_path = potential_google_path
                    
                    if os.path.exists(google_path):
                        break
                        
            except ImportError:
                continue
        
        if not google_path or not os.path.exists(google_path):
            print("Google packages not found - skipping namespace fix")
            return
            
        print(f"Found google packages at: {google_path}")
        
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
                        
    except Exception as e:
        print(f"Warning: Could not fix Google namespace packages: {e}")
        print("This is not critical - build will continue")


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
    
    # Essential modules (build will fail without these)
    essential_modules = [
        'PySide6.QtWidgets',
        'PySide6.QtCore', 
        'PySide6.QtGui',
        'keyring',
        'requests',
        'dateutil'
    ]
    
    # Optional modules (nice to have, but not critical)
    optional_modules = [
        'google_auth_oauthlib',
        'googleapiclient',
        'google.auth'
    ]
    
    failed_essential = []
    
    # Check essential modules
    for module in essential_modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            failed_essential.append(module.split('.')[0])
    
    # Check optional modules (don't fail build if missing)
    print("  Optional modules:")
    for module in optional_modules:
        try:
            __import__(module)
            print(f"    ✓ {module}")
        except ImportError as e:
            print(f"    ⚠️  {module}: Not available ({e})")
    
    if failed_essential:
        unique_failed = list(set(failed_essential))
        pip_cmd = 'pip3' if subprocess.run(['which', 'pip3'], capture_output=True).returncode == 0 else 'pip'
        print(f"\n💡 Try installing missing essential modules: {pip_cmd} install {' '.join(unique_failed)}")
        return False
    
    print("✓ All essential modules verified")
    return True
