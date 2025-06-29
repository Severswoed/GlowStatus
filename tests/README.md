# GlowStatus Tests

This directory contains comprehensive tests for the GlowStatus application, covering all major functionality areas.

## Test Files

### Unit Tests
- **`test_main.py`** - Core utility functions (clamp_rgb, normalize_status, validation)
- **`test_calendar_sync.py`** - Google Calendar OAuth and event parsing functionality
- **`test_govee_controller.py`** - Govee smart light API integration and device control
- **`test_config_ui.py`** - Configuration file handling and UI logic
- **`test_glowstatus.py`** - Main application logic integration tests

### Integration & Demo Tests
- **`test_status_detection.py`** - Custom status keyword detection verification
- **`test_status_fix.py`** - Status detection with custom color maps demonstration
- **`test_timing_sync.py`** - Minute-boundary synchronization for autostart demonstration

### Test Utilities
- **`run_all_tests.py`** - Comprehensive test runner for all test categories
- **`verify_tests.py`** - Test verification and status reporting script
- **`__init__.py`** - Python package initialization

## Test Coverage

The test suite covers:

✅ **Core Utilities**
- RGB color clamping and validation
- Status string normalization 
- Govee API key/device validation
- Google Calendar ID validation

✅ **Calendar Integration**
- Google OAuth flow with PKCE
- Calendar event parsing and status detection
- Timezone handling and datetime awareness
- Custom color mapping for event status

✅ **Govee Smart Light Control**
- API authentication and headers
- Color setting (RGB values)
- Brightness control
- Power state management
- Device status checking
- Error handling for API failures

✅ **Configuration Management**
- Config file loading and saving
- Default value handling
- Auto-enable logic for light control
- Keyring integration for secure credentials

✅ **Status Detection**
- Custom keyword matching in calendar events
- Priority-based status resolution
- Color mapping customization
- Fallback behavior for unknown events

✅ **Timing & Synchronization**
- Minute-boundary synchronization calculations
- Autostart timing for meeting preparation
- Refresh interval management

## Running Tests

### Individual Test Files
```bash
cd /workspaces/GlowStatus

# Core utility tests
python tests/test_main.py

# Calendar integration tests  
python tests/test_calendar_sync.py

# Govee controller tests
python tests/test_govee_controller.py

# Status detection demos
python tests/test_status_fix.py
python tests/test_timing_sync.py
```

### Test Verification
```bash
# Run verification script
python tests/verify_tests.py
```

### Using pytest (if preferred)
```bash
# Run with pytest
python -m pytest tests/ -v
```

## Dependencies

The tests require the following packages (already installed):
- `pytest` - Modern testing framework
- `pytest-mock` - Enhanced mocking capabilities  
- `unittest.mock` - Built-in mocking for unit tests
- `google-api-python-client` - Google Calendar API
- `google-auth-*` - Google OAuth libraries
- `PySide6` - Qt GUI framework (mocked in tests)
- `requests` - HTTP client library

## Test Philosophy

These tests follow best practices:
- **Isolation** - Each test is independent and mocks external dependencies
- **Coverage** - All major code paths and error conditions are tested
- **Realistic** - Tests use realistic data and scenarios
- **Fast** - Tests run quickly without external API calls
- **Maintainable** - Clear naming and documentation for easy maintenance

## Notes

- GUI tests mock PySide6 to avoid requiring a display server
- API tests mock HTTP requests to avoid external dependencies
- OAuth tests simulate the authentication flow without real credentials
- All tests can run in CI/CD environments without external services

The test suite ensures GlowStatus is robust, reliable, and ready for production use.
