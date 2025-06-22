import datetime
import os
import time
from dotenv import load_dotenv

from govee_controller import GoveeController
from calendar_sync import CalendarSync
from logger import get_logger
from utils import (
    clamp_rgb,
    is_valid_govee_api_key,
    is_valid_govee_device_id,
    is_valid_govee_device_model,
    is_valid_google_calendar_id,
)

# Load environment variables
load_dotenv()
GOVEE_API_KEY = os.getenv("GOVEE_API_KEY")
GOVEE_DEVICE_ID = os.getenv("GOVEE_DEVICE_ID")
GOVEE_DEVICE_MODEL = os.getenv("GOVEE_DEVICE_MODEL")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", 60))
DISABLE_CALENDAR_SYNC = os.getenv("DISABLE_CALENDAR_SYNC", "0") == "1"
POWER_OFF_WHEN_AVAILABLE = os.getenv("POWER_OFF_WHEN_AVAILABLE", "0") == "1"

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
    if not is_valid_govee_device_model(GOVEE_DEVICE_MODEL):
        logger.error("Invalid or missing GOVEE_DEVICE_MODEL.")
        return
    if not DISABLE_CALENDAR_SYNC and not is_valid_google_calendar_id(GOOGLE_CALENDAR_ID):
        logger.error("Invalid or missing GOOGLE_CALENDAR_ID.")
        return

    logger.info("Starting GlowStatus...")
    govee = GoveeController(GOVEE_API_KEY, GOVEE_DEVICE_ID, GOVEE_DEVICE_MODEL)

    if DISABLE_CALENDAR_SYNC:
        logger.info("Calendar sync is disabled. Testing Govee functions only.")
        # Example: cycle through colors for testing
        test_colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 255, 255) # White
        ]
        try:
            logger.info("Starting GlowStatus test mode...")
            logger.info("Turning on Govee device...")
            govee.set_power("on")
            for color in test_colors:
                logger.info(f"Setting Govee color to: {color}")
                color = clamp_rgb(*color)
                if not color:
                    logger.error("Invalid RGB color values.")
                    continue
                logger.info(f"Setting Govee color to RGB{color}")
                govee.set_color(*color)
                time.sleep(10)  # Increase delay to avoid rate limit
            logger.info("GlowStatus test completed.")
            logger.info("GlowStatus is exiting.")
            govee.set_power("off")
        except KeyboardInterrupt:
            logger.info("GlowStatus stopped by user.")
            logger.info("GlowStatus test completed.")
            logger.info("GlowStatus is exiting.")
            govee.set_power("off")
        return

    calendar = CalendarSync(GOOGLE_CALENDAR_ID)

    try:
        while True:
            try:
                # Get current status, but allow "in_meeting" up to 1 minute before the meeting starts
                status, next_event_start = calendar.get_current_status(return_next_event_time=True)
                logger.info(f"Current status: {status}")

                # If next event is within 1 minute and is a meeting, treat as "in_meeting"
                if (
                    status == "available"
                    and next_event_start is not None
                    and (0 <= (next_event_start - datetime.datetime.now(datetime.timezone.utc)).total_seconds() <= 60)
                ):
                    logger.info("Upcoming meeting within 1 minute. Setting status to 'in_meeting'.")
                    status = "in_meeting"

                if status == "available" and POWER_OFF_WHEN_AVAILABLE:
                    logger.info("Status is 'available' and POWER_OFF_WHEN_AVAILABLE is set. Turning off Govee device.")
                    govee.set_power("off")
                else:
                    color = get_status_color(status)
                    govee.set_power("on")
                    govee.set_color(*color)
            except Exception as e:
                logger.error(f"Error updating status: {e}")
            time.sleep(REFRESH_INTERVAL)
    except KeyboardInterrupt:
        logger.info("GlowStatus stopped by user.")
if __name__ == "__main__":
    main()