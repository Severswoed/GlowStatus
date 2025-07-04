# GlowStatus Test Suite

This directory contains the comprehensive test suit### Running All Tests

```bash
# Run comprehensive verification (includes token robustness tests)
python tests/test_main.py --final-verification

# Verify test environment and setup
python tests/verify_tests.py
``` GlowStatus application. The test suite provides robust coverage of all major functionality including configuration management, Google Calendar integration, Govee smart light control, and application logic.

## 📁 Test Structure

```
tests/
├── readme_tests.md                    # This file - comprehensive test documentation
├── __init__.py                        # Python package initialization
├── test_main.py                       # Core utilities and validation functions + final verification
├── test_token_robustness.py           # OAuth token error handling tests (NEW)
├── test_config_ui.py                  # Configuration UI and management
├── test_settings_ui_headless.py       # Settings UI interface tests (NEW)
├── test_config.py                     # Configuration loading and path resolution
├── test_setup_functions.py            # Build and setup helper function tests
├── test_calendar_sync.py              # Google Calendar integration
├── test_govee_controller.py           # Govee smart light control
├── test_glowstatus.py                 # Main application logic
├── test_light_control_bug_fix.py      # Specific bug fix verification
├── test_google_oauth_token_path_bug.py # Google OAuth token path bug fix
├── test_oauth_threading.py            # OAuth threading and UI responsiveness fix
├── test_light_toggle_tray_menu.py     # Light control toggle in tray menu
├── test_meeting_transitions.py       # Meeting transition scenarios and status handling
├── test_immediate_actions.py          # Immediate menu response actions
├── test_status_detection.py           # Status detection demonstration
├── test_status_fix.py                 # Status handling examples
├── test_timing_sync.py                # Timing and synchronization tests
├── manual_test_light_toggle_tray.py   # Manual test checklist for light toggle
├── final_test_verification.py         # Comprehensive test runner and verification
├── verify_tests.py                    # Test verification utility
├── final_test_verification.py         # Comprehensive test status report
└── RESOLUTION_SUMMARY.md              # Test suite development summary
```

## 🚀 Quick Start

### Running Individual Tests

```bash
# Core utilities (RGB handling, validation functions)
python tests/test_main.py

# OAuth token robustness tests (NEW)
python tests/test_token_robustness.py

# Configuration management
python tests/test_config_ui.py

# Settings UI interface tests (NEW)
python tests/test_settings_ui_headless.py

# Configuration loading and path resolution
python tests/test_config.py

# Build and setup helper functions
python tests/test_setup_functions.py

# Google Calendar integration
python tests/test_calendar_sync.py

# Govee smart light control
python tests/test_govee_controller.py

# Main application logic
python tests/test_glowstatus.py

# Specific bug fix verification
python tests/test_light_control_bug_fix.py

# Light control toggle in tray menu
python tests/test_light_toggle_tray_menu.py

# Meeting transition scenarios
python tests/test_meeting_transitions.py

# Immediate menu response actions  
python tests/test_immediate_actions.py
```

### Running All Tests

```bash
# Run comprehensive test verification (recommended)
python tests/final_test_verification.py

# Alternative: Run through main test file with final verification flag
python tests/test_main.py --final-verification
```

## 📊 Test Categories and Coverage

### 1. Core Utilities (`test_main.py`) ✅
- **RGB color handling**: Clamping, validation, conversion
- **Status normalization**: Keyword matching, fallback logic
- **Validation functions**: Govee device ID/model format validation
- **Utility functions**: Resource path resolution, time formatting
- **Final verification**: Comprehensive test runner with token robustness tests

**Key Features Tested:**
- `clamp_rgb()` - RGB value bounds checking
- `normalize_status()` - Status keyword extraction
- `is_valid_govee_device_id()` - Device ID format validation
- `is_valid_govee_device_model()` - Device model validation
- `final_test_verification()` - Runs all tests including token robustness
- Boolean return values for testability

### 1.1. OAuth Token Robustness (`test_token_robustness.py`) ✅ **NEW**
- **Invalid token handling**: Corrupted token files, authentication failures
- **Expired token handling**: Graceful degradation when tokens expire
- **Calendar sync robustness**: Auto-disable calendar sync on auth failure
- **UI robustness**: Config window loads even with bad tokens
- **Worker thread safety**: OAuth worker handles failures gracefully

**Key Features Tested:**
- `CalendarSync` with invalid/expired tokens - should not crash
- `GlowStatusController.update_now()` with auth failures - should auto-disable calendar sync
- `ConfigWindow.load_calendars()` with auth failures - should show "No calendars found"
- `OAuthWorker.run()` with auth failures - should emit error signal
- App startup robustness with missing/expired tokens

### 2. Configuration Management (`test_config_ui.py`) ✅
- **File I/O operations**: Loading, saving, error handling
- **Default configurations**: Sensible defaults for new installations
- **User preference preservation**: Respects explicit user choices
- **Credential management**: Secure keyring integration
- **Auto-enabling logic**: Smart defaults without overriding user choice

**Key Features Tested:**
- `load_config()` / `save_config()` functions
- Light control auto-enabling for new installations

### 2.1. Settings UI Interface (`test_settings_ui_headless.py`) ✅ **NEW**
- **Tabbed Navigation**: Sidebar navigation with 7 tabs (About, OAuth, Integrations, etc.)
- **Form Validation**: Govee device ID, API key, and configuration validation
- **Headless Testing**: Complete UI functionality testing without requiring a display
- **Configuration Integration**: Settings UI properly loads and saves all configuration options
- **Component Functionality**: All UI components (dropdowns, checkboxes, tables) work correctly

**Key Features Tested:**
- `SettingsWindow` class initialization and UI setup
- All tab creation methods (About, OAuth, Integrations, Calendar, Status, Options, Accessibility)
- Form validation functions (device ID format, color RGB values)
- Configuration loading and saving through the UI
- Status table management for color/power mappings
- Govee integration settings (API key, device ID, model)
- Calendar sync settings and refresh intervals
- Manual status override functionality
- Accessibility options and UI preferences

### 3. Configuration Path Resolution (`test_config.py`) ✅
- **Path resolution**: Config file location across different environments
- **Development vs production**: Bundle vs development mode detection
- **Cross-platform compatibility**: Windows/macOS/Linux path handling
- **File existence checking**: Graceful handling of missing config files

**Key Features Tested:**
- Configuration directory determination
- Config file loading without Qt dependencies
- Current configuration state verification
- User choice preservation (critical bug fix)
- Invalid JSON handling and fallback mechanisms
- Configuration validation and defaults

### 4. Build & Setup Helper Functions (`test_setup_functions.py`) ✅
- **Dependency checking**: Automated requirements installation verification
- **Module verification**: Critical module availability checks for builds
- **Namespace fixes**: Google API namespace package compatibility
- **Build preparation**: Helper functions for reliable cross-platform builds

**Key Features Tested:**
- `check_and_install_requirements()` - Automated dependency management
- `verify_critical_modules()` - Missing module detection for py2app builds
- `fix_google_namespace_packages()` - Google API namespace package fixes
- Build helper function error handling and return values

### 5. Google Calendar Integration (`test_calendar_sync.py`) ✅
- **OAuth flow**: Authentication, token management, refresh
- **Event parsing**: Meeting detection, timezone handling
- **Status detection**: In meeting, available, focus time
- **Privacy compliance**: Limited scope, read-only access
- **Error handling**: Network issues, invalid credentials

**Key Features Tested:**
- Calendar event fetching and parsing
- Status determination logic
- OAuth token validation and refresh
- Timezone-aware event processing
- Google API integration patterns

### 6. Govee Smart Light Control (`test_govee_controller.py`) ✅
- **API communication**: HTTP requests, error handling
- **Device control**: Color changes, brightness, power state
- **Credential validation**: API key and device ID formats
- **Network resilience**: Timeout handling, retry logic
- **State management**: Device status tracking

**Key Features Tested:**
- `GoveeController` class functionality
- Color setting and brightness control
- Power state management
- API error handling and recovery
- Device authentication

### 7. Application Logic (`test_glowstatus.py`) ✅
- **Status application**: Color mapping, light control
- **Integration testing**: Calendar + Govee coordination
- **Manual overrides**: User-initiated status changes
- **Timing synchronization**: Minute-boundary alignment
- **Configuration integration**: Settings application

**Key Features Tested:**
- `GlowStatusController` main logic
- Status-to-light mapping
- Manual status override functionality
- Integration between calendar and light control
- Application startup and shutdown

### 8. Bug Fix Verification (`test_light_control_bug_fix.py`) ✅
- **User choice preservation**: Light control disable setting
- **Auto-enabling logic**: New installation behavior
- **Configuration persistence**: Settings survival across saves
- **Edge case handling**: Various credential scenarios

**Key Features Tested:**
- Light control configuration bug fix
- User preference preservation
- Auto-enabling only for new installations
- Configuration save behavior

### 9. OAuth Threading Fix (`test_oauth_threading.py`) ✅
- **Threading implementation**: OAuth flow runs on separate thread
- **UI responsiveness**: Dialog remains responsive during OAuth
- **Error handling**: Proper cleanup and UI reset on errors
- **Signal/slot communication**: Thread-safe UI updates

**Key Features Tested:**
- OAuthWorker thread implementation
- Progress indicator functionality
- Success/error callback handling
- UI state management during async operations

**Bug Description:**
This test verifies the fix for OAuth dialog unresponsiveness where:
- The consent dialog would freeze during OAuth callback
- Users couldn't interact with Cancel/OK buttons
- Spinning wheel would appear on macOS without response

### 10. Google OAuth Token Path Bug Fix (`test_google_oauth_token_path_bug.py`) ✅
- **Path consistency**: Unified token storage location
- **UI/App integration**: Settings UI and main app coordination  
- **Configuration standards**: Centralized path management
- **Cross-module validation**: Import and usage verification

**Key Features Tested:**
- Token path consistency between UI and main application
- Proper use of `TOKEN_PATH` from `constants.py`
- OAuth token detection and validation
- File path resolution and storage

**Bug Description:**
This test was created to identify and verify the fix for a critical bug where:
- The configuration UI saved Google OAuth tokens to `config/google_token.pickle` (via `TOKEN_PATH` from `constants.py`)
- The tray application was checking for tokens at `google_token.pickle` (root level, hardcoded path)
- This inconsistency caused OAuth tokens saved via the UI to not be found by the main application

**Fix Applied:**
- Updated `tray_app.py` to import `TOKEN_PATH` from `constants.py`
- Replaced hardcoded `resource_path('google_token.pickle')` with `TOKEN_PATH` usage
- Ensured all modules now use the same path: `config/google_token.pickle`
- Added test verification to prevent regression

**Test Verification:**
```bash
python tests/test_google_oauth_token_path_bug.py
```

### 11. Immediate Menu Actions (`test_immediate_actions.py`) ✅
- **Immediate Light Turn-Off**: Instant response when disabling light control
- **Sync Toggle Updates**: Immediate status refresh when enabling sync
- **Tray Menu Integration**: Proper method calls for instant feedback
- **Tooltip Status Updates**: Real-time status indicator updates

**Key Features Tested:**
- `turn_off_lights_immediately()` method exists and works correctly
- Tray menu `toggle_light()` calls immediate turn-off when disabling
- Tray menu `toggle_sync()` calls `update_now()` when enabling  
- Tooltip shows light/sync status indicators
- No waiting for polling cycles for menu actions

**Problem Addressed:**
Previously, when users clicked "Disable Lights" in the tray menu while lights were on (e.g., red during a meeting), the lights would remain on until the next polling cycle. This created confusion as users expected immediate feedback from menu actions.

**Solution Implemented:**
- Added `turn_off_lights_immediately()` method to `GlowStatusController`
- Modified tray menu toggles to trigger immediate actions
- Enhanced tooltip to show disabled feature status
- Menu actions now provide instant visual feedback

**Test Verification:**
```bash
python tests/test_immediate_actions.py
```

### 12. Meeting Transition Scenarios (`test_meeting_transitions.py`) ✅
- **Meeting End Behavior**: Proper handling when meetings end early
- **Overlapping Meetings**: Seamless transition between consecutive meetings  
- **Imminent Meeting Detection**: 1-minute advance light activation
- **Manual Override Clearing**: Automatic transition from manual status to calendar control
- **Status Persistence**: Maintaining appropriate status during meeting gaps

**Key Features Tested:**
- `meeting_ended_early` status transitions to `in_meeting` when next meeting is imminent (< 1 minute)
- Manual override clearing when calendar events take priority
- Light control during overlapping meeting scenarios
- Proper gap handling between meetings (> 1 minute gap maintains manual status)
- Status transition logic for consecutive and overlapping meetings

**Problem Addressed:**
Previously, when users ended a meeting early (setting status to `meeting_ended_early`), the system would turn off lights and maintain manual override even when the next meeting was about to start. This caused lights to remain off during overlapping meetings or when the next meeting was imminent.

**Solution Implemented:**
- Enhanced `update_status()` logic to check for imminent meetings when processing `meeting_ended_early` status
- Removed calendar status dependency from imminent meeting detection
- Added proper manual override clearing for calendar-controlled transitions
- Improved handling of overlapping and consecutive meeting scenarios

**Test Scenarios:**
1. **Meeting ended early + imminent meeting (< 1 min)**: Lights turn on, manual override cleared
2. **Meeting ended early + no imminent meeting**: Lights stay off, maintain status
3. **Overlapping meetings**: Smooth transition from manual override to calendar control
4. **Consecutive meetings with gap (> 1 min)**: Lights off during gap, on before next meeting

**Test Verification:**
```bash
python tests/test_meeting_transitions.py
```

## 🛠 Test Infrastructure

### Mocking and Dependencies

The test suite uses comprehensive mocking to avoid external dependencies:

```python
# Qt/GUI mocking for headless environments
sys.modules['PySide6'] = MagicMock()
sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtCore'] = MagicMock()
sys.modules['PySide6.QtGui'] = MagicMock()

# Network and API mocking
@patch('requests.put')
@patch('requests.get')
def test_api_calls(self, mock_get, mock_put):
    # Test implementation
```

### Headless Environment Compatibility

All tests run in headless environments without requiring:
- Qt/GUI libraries
- Display server (X11, Wayland)
- Google API credentials
- Physical Govee devices
- Network connectivity

### Test Isolation

Each test uses temporary files and isolated configurations:

```python
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump(test_config, f)
    config_path = f.name

try:
    with patch('config_ui.CONFIG_PATH', config_path):
        # Test logic with isolated config
        pass
finally:
    os.unlink(config_path)  # Cleanup
```

## 📋 Test Results and Status

### Current Test Status

```
📊 Test Categories: 7/7 Implemented ✅
📊 Core Functionality: 100% Covered ✅
📊 Bug Fixes: Verified and Protected ✅
📊 Integration Tests: Complete ✅
📊 Headless Compatibility: Full ✅
```

### Test Execution Summary

- **Passing Tests**: Core utilities, configuration, bug fixes
- **Integration Tests**: Calendar sync, Govee control, main logic
- **Demonstration Scripts**: Status detection, timing synchronization
- **Verification Tools**: Test runners, status reports

## 🔧 Advanced Usage

### Adding New Tests

1. **Create test file**: Follow naming pattern `test_[module].py`
2. **Add mocking**: Include necessary Qt/API mocks
3. **Use isolation**: Temporary files for configuration tests
4. **Update runners**: Add to test verification scripts

Example test structure:
```python
#!/usr/bin/env python3
"""Tests for [module] functionality."""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock external dependencies
sys.modules['PySide6'] = MagicMock()
# ... other mocks

from [module] import [functions_to_test]

class Test[Module](unittest.TestCase):
    def test_functionality(self):
        # Test implementation
        pass

if __name__ == '__main__':
    unittest.main()
```

### Running Tests in CI/CD

The test suite is designed for automated environments:

```bash
# GitHub Actions / CI pipeline
python tests/final_test_verification.py
python tests/final_test_verification.py

# Exit codes indicate success/failure
echo $?  # 0 = success, non-zero = failure
```

### Test Data and Fixtures

Common test data patterns:

```python
# Configuration test data
test_config = {
    'DISABLE_LIGHT_CONTROL': True,
    'GOVEE_DEVICE_ID': 'AA:BB:CC:DD:EE:FF:11:22',
    'GOVEE_DEVICE_MODEL': 'H6159',
    'STATUS_COLOR_MAP': {
        'in_meeting': {'color': '255,0,0', 'power_off': False}
    }
}

# API response mocking
mock_response = MagicMock()
mock_response.json.return_value = {'status': 'success'}
mock_response.status_code = 200
```

## 🚨 Troubleshooting

### Common Issues

1. **Qt Import Errors**: Ensure proper mocking is in place
2. **File Permission Errors**: Use temporary files with proper cleanup
3. **Network Timeouts**: All network calls should be mocked
4. **Missing Dependencies**: Tests should not require external services

### Debug Mode

Run tests with verbose output:
```bash
python tests/test_main.py -v
python tests/final_test_verification.py --debug
```

### Test Environment

Verify test environment setup:
```bash
python tests/verify_tests.py
```

## 📚 Development History

The test suite was developed to address several key requirements:

1. **Regression Protection**: Prevent reintroduction of fixed bugs
2. **Refactoring Safety**: Enable safe code improvements
3. **Documentation**: Provide examples of proper usage
4. **Validation**: Ensure configuration changes work correctly
5. **Integration Verification**: Test component interactions

### Key Milestones

- ✅ **Initial Suite**: Core functionality coverage
- ✅ **Qt Compatibility**: Headless environment support
- ✅ **Bug Fix Coverage**: Light control configuration issue
- ✅ **Integration Tests**: Calendar + Govee coordination
- ✅ **Validation Functions**: Regex improvements for testability
- ✅ **Comprehensive Documentation**: Usage guides and examples

## 🎯 Future Enhancements

Potential test suite improvements:

1. **Performance Testing**: Response time measurements
2. **Load Testing**: Multiple calendar events handling
3. **Security Testing**: Credential handling validation
4. **UI Testing**: Configuration window behavior (when GUI available)
5. **End-to-End Testing**: Full application workflow simulation

## 📖 Related Documentation

- [`../README.md`](../README.md) - Main project documentation
- [`RESOLUTION_SUMMARY.md`](RESOLUTION_SUMMARY.md) - Test development summary
- [`../docs/`](../docs/) - Application documentation and guides

---

**Note**: This test suite ensures the reliability and maintainability of the GlowStatus application. All tests are designed to run in any environment without external dependencies, making them suitable for development, CI/CD, and automated testing scenarios.
