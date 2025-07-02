"""
Test version utilities functionality.
"""

import unittest
import os
import sys
import json
import tempfile
import shutil

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from version import get_version_info, get_version_string, get_version_display


class TestVersionUtilities(unittest.TestCase):
    """Test version utilities."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_version_file(self, version_data):
        """Create a test version.json file."""
        version_file = os.path.join(self.test_dir, 'version.json')
        with open(version_file, 'w') as f:
            json.dump(version_data, f)
        return version_file
    
    def test_get_version_info_valid_file(self):
        """Test getting version info from a valid version.json file."""
        test_version = {
            "major": 2,
            "minor": 1,
            "patch": 0,
            "pre": ""
        }
        
        # Create test version file
        self.create_test_version_file(test_version)
        
        # Change to test directory so version.py looks for version.json there
        os.chdir(self.test_dir)
        
        # Create a mock src directory structure
        src_dir = os.path.join(self.test_dir, 'src')
        os.makedirs(src_dir)
        os.chdir(src_dir)
        
        result = get_version_info()
        
        self.assertEqual(result['major'], 2)
        self.assertEqual(result['minor'], 1)
        self.assertEqual(result['patch'], 0)
        self.assertEqual(result['pre'], "")
    
    def test_get_version_info_missing_file(self):
        """Test getting version info when version.json is missing."""
        # Change to test directory where no version.json exists
        os.chdir(self.test_dir)
        
        # Create a mock src directory structure
        src_dir = os.path.join(self.test_dir, 'src')
        os.makedirs(src_dir)
        os.chdir(src_dir)
        
        result = get_version_info()
        
        # Should return default values
        self.assertEqual(result['major'], 2)
        self.assertEqual(result['minor'], 1)
        self.assertEqual(result['patch'], 0)
        self.assertEqual(result['pre'], "")
    
    def test_get_version_info_invalid_json(self):
        """Test getting version info from invalid JSON file."""
        version_file = os.path.join(self.test_dir, 'version.json')
        with open(version_file, 'w') as f:
            f.write("invalid json content")
        
        os.chdir(self.test_dir)
        src_dir = os.path.join(self.test_dir, 'src')
        os.makedirs(src_dir)
        os.chdir(src_dir)
        
        result = get_version_info()
        
        # Should return default values
        self.assertEqual(result['major'], 2)
        self.assertEqual(result['minor'], 1)
        self.assertEqual(result['patch'], 0)
        self.assertEqual(result['pre'], "")
    
    def test_get_version_info_missing_fields(self):
        """Test getting version info when required fields are missing."""
        test_version = {
            "major": 1,
            # missing minor and patch
        }
        
        self.create_test_version_file(test_version)
        os.chdir(self.test_dir)
        src_dir = os.path.join(self.test_dir, 'src')
        os.makedirs(src_dir)
        os.chdir(src_dir)
        
        result = get_version_info()
        
        # Should return default values when required fields are missing
        self.assertEqual(result['major'], 2)
        self.assertEqual(result['minor'], 1)
        self.assertEqual(result['patch'], 0)
        self.assertEqual(result['pre'], "")
    
    def test_get_version_string_no_pre(self):
        """Test getting version string without pre-release tag."""
        test_version = {
            "major": 2,
            "minor": 1,
            "patch": 0,
            "pre": ""
        }
        
        self.create_test_version_file(test_version)
        os.chdir(self.test_dir)
        src_dir = os.path.join(self.test_dir, 'src')
        os.makedirs(src_dir)
        os.chdir(src_dir)
        
        result = get_version_string()
        self.assertEqual(result, "2.1.0")
    
    def test_get_version_string_with_pre(self):
        """Test getting version string with pre-release tag by temporarily modifying version.json."""
        # Get the real version.json path
        src_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
        root_dir = os.path.dirname(src_dir)
        version_file = os.path.join(root_dir, 'version.json')
        
        # Backup original version.json
        backup_data = None
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                backup_data = f.read()
        
        try:
            # Create test version with pre-release
            test_version = {
                "major": 2,
                "minor": 1,
                "patch": 0,
                "pre": "beta.1"
            }
            
            with open(version_file, 'w') as f:
                json.dump(test_version, f)
            
            # Import fresh instance to use the modified file
            import importlib
            if 'version' in sys.modules:
                importlib.reload(sys.modules['version'])
            
            result = get_version_string()
            self.assertEqual(result, "2.1.0-beta.1")
            
        finally:
            # Restore original version.json
            if backup_data:
                with open(version_file, 'w') as f:
                    f.write(backup_data)
            
            # Reload to get back to original state
            if 'version' in sys.modules:
                importlib.reload(sys.modules['version'])
    
    def test_get_version_display(self):
        """Test getting display version string."""
        test_version = {
            "major": 2,
            "minor": 1,
            "patch": 0,
            "pre": ""
        }
        
        self.create_test_version_file(test_version)
        os.chdir(self.test_dir)
        src_dir = os.path.join(self.test_dir, 'src')
        os.makedirs(src_dir)
        os.chdir(src_dir)
        
        result = get_version_display()
        self.assertEqual(result, "Version 2.1.0")


if __name__ == '__main__':
    unittest.main()
