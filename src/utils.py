import re

def clamp_rgb(r, g, b):
    """Clamp RGB values to the 0-255 range."""
    return (
        max(0, min(255, int(r))),
        max(0, min(255, int(g))),
        max(0, min(255, int(b))),
    )

def normalize_status(event_summary):
    """Map event summary or keywords to a status key."""
    summary = event_summary.lower()
    if "focus" in summary:
        return "focus"
    if "meeting" in summary or "call" in summary:
        return "in_meeting"
    return "available"

def format_time(dt):
    """Format a datetime object for logging/display."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def is_valid_govee_api_key(api_key):
    """Basic check for Govee API key format (should be a long hex string)."""
    return bool(api_key) and len(api_key) >= 32

def is_valid_govee_device_id(device_id):
    """Check for Govee device ID format like 10:00:D7:C1:83:46:65:8C."""
    return bool(device_id) and re.match(r"^([0-9A-Fa-f]{2}:){7}[0-9A-Fa-f]{2}$", device_id)

def is_valid_govee_device_model(device_model):
    """Basic check for Govee device model format (e.g., H6159, H6001)."""
    return bool(device_model) and re.match(r"^[A-Za-z0-9\-]+$", device_model)

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