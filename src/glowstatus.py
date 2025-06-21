import os
import time
from dotenv import load_dotenv

from govee_controller import GoveeController
from calendar_sync import CalendarSync
from logger import get_logger
from utils import (
    is_valid_govee_api_key,
    is_valid_govee_device_id,
    is_valid_google_calendar_id,
)

# Load environment variables
load_dotenv()
GOVEE_API_KEY = os.getenv("GOVEE_API_KEY")
GOVEE_DEVICE_ID = os.getenv("GOVEE_DEVICE_ID")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", 60))

logger = get_logger()

def get_status_color(status):
    """Map calendar status to Govee color."""
    color_map = {
        "in_meeting": (255, 0, 0),      # Red
        "available": (0, 255, 0),       # Green
        "focus": (0, 0, 255),           # Blue
        "offline": (128, 128, 128),     # Gray
    }
    return color_map.get(status, (255, 255, 255))  # Default: White

def main():
    # Validate environment variables
    if not is_valid_govee_api_key(GOVEE_API_KEY):
        logger.error("Invalid or missing GOVEE_API_KEY.")
        return
    if not is_valid_govee_device_id(GOVEE_DEVICE_ID):
        logger.error("Invalid or missing GOVEE_DEVICE_ID.")
        return
    if not is_valid_google_calendar_id(GOOGLE_CALENDAR_ID):
        logger.error("Invalid or missing GOOGLE_CALENDAR_ID.")
        return

    logger.info("Starting GlowStatus...")
    govee = GoveeController(GOVEE_API_KEY, GOVEE_DEVICE_ID)
    calendar = CalendarSync(GOOGLE_CALENDAR_ID)

    try:
        while True:
            try:
                status = calendar.get_current_status()
                logger.info(f"Current status: {status}")
                color = get_status_color(status)
                govee.set_color(*color)
            except Exception as e:
                logger.error(f"Error updating status: {e}")
            time.sleep(REFRESH_INTERVAL)
    except KeyboardInterrupt:
        logger.info("GlowStatus stopped by user.")

if __name__ == "__main__":
    main()