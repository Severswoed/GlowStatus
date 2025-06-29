import re
import os
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller/py2app bundle."""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller
        base_path = sys._MEIPASS
    elif getattr(sys, 'frozen', False):
        # py2app
        base_path = os.environ.get('RESOURCEPATH', os.path.abspath("."))
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def clamp_rgb(r, g, b):
    """Clamp RGB values to the 0-255 range."""
    return (
        max(0, min(255, int(r))),
        max(0, min(255, int(g))),
        max(0, min(255, int(b))),
    )

def normalize_status(summary, color_map=None):
    """
    Return the status keyword if any status keyword is found in the summary (case-insensitive, substring match).
    If color_map is provided, use its keys as keywords. Otherwise, use default keywords.
    """
    if not summary:
        return "in_meeting"
    summary_lower = summary.lower()
    keywords = color_map.keys() if color_map else ["in_meeting", "focus", "available", "offline"]
    for keyword in keywords:
        if keyword.lower() in summary_lower:
            return keyword
    return "in_meeting"

def load_secret(key):
    """Load a secret from environment variables or keyring."""
    # First try environment variables (for development/CLI usage)
    value = os.environ.get(key)
    if value:
        return value
    
    # Then try keyring (for GUI users)
    try:
        import keyring
        keyring_value = keyring.get_password("GlowStatus", key)
        if keyring_value:
            return keyring_value
    except Exception:
        pass  # Keyring not available or other error
    
    return None

def format_time(dt):
    """Format a datetime object for logging/display."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def is_valid_govee_api_key(api_key):
    """Basic check for Govee API key format (should be a long hex string)."""
    return bool(api_key) and len(api_key) >= 32

def is_valid_govee_device_id(device_id):
    """Check for Govee device ID format like 10:00:D7:C1:83:46:65:8C."""
    return bool(device_id) and bool(re.match(r"^([0-9A-Fa-f]{2}:){7}[0-9A-Fa-f]{2}$", device_id))

def is_valid_govee_device_model(device_model):
    """Basic check for Govee device model format (e.g., H6159, H6001)."""
    return bool(device_model) and bool(re.match(r"^[A-Za-z][A-Za-z0-9\-]*$", device_model))

def is_valid_google_calendar_id(calendar_id):
    """Google Calendar IDs are usually email addresses or long strings."""
    # Accepts 'primary', email, or long string with @group.calendar.google.com
    if calendar_id == "primary":
        return True
    if re.match(r"[^@]+@[^@]+\.[^@]+", calendar_id):
        return True
    if calendar_id.endswith("@group.calendar.google.com"):
        return True
    return False