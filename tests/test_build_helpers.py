"""
Test build helpers functionality.
"""

import unittest
import os
import sys
import json
import tempfile
import shutil

# Add scripts directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts'))

from build_helpers import get_version_info, get_version_string


class TestBuildHelpers(unittest.TestCase):
    """Test build helper utilities."""
    
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
    
    def test_get_version_info_from_build_helpers(self):
        """Test getting version info from build helpers."""
        test_version = {
            "major": 2,
            "minor": 1,
            "patch": 0,
            "pre": ""
        }
        
        # Create test version file
        self.create_test_version_file(test_version)
        
        # Change to test directory and create scripts subdirectory
        scripts_dir = os.path.join(self.test_dir, 'scripts')
        os.makedirs(scripts_dir)
        os.chdir(scripts_dir)
        
        result = get_version_info()
        
        self.assertEqual(result['major'], 2)
        self.assertEqual(result['minor'], 1)
        self.assertEqual(result['patch'], 0)
        self.assertEqual(result['pre'], "")
    
    def test_get_version_string_from_build_helpers(self):
        """Test getting version string from build helpers."""
        # Test with real version.json
        result = get_version_string()
        # Should match the actual version in version.json
        self.assertEqual(result, "2.1.0")
    
    def test_build_helpers_default_fallback(self):
        """Test that build helpers return defaults when version.json is missing."""
        # Change to test directory where no version.json exists
        scripts_dir = os.path.join(self.test_dir, 'scripts')
        os.makedirs(scripts_dir)
        os.chdir(scripts_dir)
        
        result = get_version_info()
        
        # Should return default values
        self.assertEqual(result['major'], 2)
        self.assertEqual(result['minor'], 1)
        self.assertEqual(result['patch'], 0)
        self.assertEqual(result['pre'], "")
        
        version_string = get_version_string()
        self.assertEqual(version_string, "2.1.0")


if __name__ == '__main__':
    unittest.main()
