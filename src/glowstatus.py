import threading
import time
import datetime
import os

from govee_controller import GoveeController
from calendar_sync import CalendarSync
from config_ui import load_config, save_config
from logger import get_logger
from utils import normalize_status, load_secret, resource_path

logger = get_logger()

class GlowStatusController:
    def __init__(self):
        self._running = False
        self._thread = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def apply_status_to_light(self, govee, status, color_map, off_for_unknown_status):
        status_key = status.lower()
        entry = color_map.get(status_key)
        if entry:
            # Backward compatibility: if entry is a string, treat as color only
            if isinstance(entry, str):
                rgb_str = entry
                govee.set_power("on")
                try:
                    r, g, b = map(int, rgb_str.split(","))
                except Exception as e:
                    logger.error(f"Invalid RGB string '{rgb_str}' for status '{status_key}': {e}")
                    r, g, b = 255, 255, 255
                govee.set_color(r, g, b)
            elif isinstance(entry, dict):
                if entry.get("power_off"):
                    govee.set_power("off")
                else:
                    rgb_str = entry.get("color", "255,255,255")
                    try:
                        r, g, b = map(int, rgb_str.split(","))
                    except Exception as e:
                        logger.error(f"Invalid RGB string '{rgb_str}' for status '{status_key}': {e}")
                        r, g, b = 255, 255, 255
                    govee.set_power("on")
                    govee.set_color(r, g, b)
        else:
            if off_for_unknown_status:
                govee.set_power("off")
            else:
                govee.set_power("on")
                govee.set_color(255, 255, 255)

    def update_now(self):
        now = datetime.datetime.now()
        logger.info(f"Manual status update at: {now.strftime('%H:%M:%S.%f')[:-3]}")
        
        config = load_config()
        GOVEE_API_KEY = load_secret("GOVEE_API_KEY")
        GOVEE_DEVICE_ID = config.get("GOVEE_DEVICE_ID")
        GOVEE_DEVICE_MODEL = config.get("GOVEE_DEVICE_MODEL")
        SELECTED_CALENDAR_ID = config.get("SELECTED_CALENDAR_ID")
        STATUS_COLOR_MAP = config.get("STATUS_COLOR_MAP", {})
        POWER_OFF_WHEN_AVAILABLE = bool(config.get("POWER_OFF_WHEN_AVAILABLE", True))
        OFF_FOR_UNKNOWN_STATUS = bool(config.get("OFF_FOR_UNKNOWN_STATUS", True))
        DISABLE_CALENDAR_SYNC = bool(config.get("DISABLE_CALENDAR_SYNC", False))
        DISABLE_LIGHT_CONTROL = bool(config.get("DISABLE_LIGHT_CONTROL", False))

        # Guard: If light control is disabled, only update status without controlling lights
        if DISABLE_LIGHT_CONTROL:
            logger.info("Light control disabled - status tracking only")
            if not DISABLE_CALENDAR_SYNC:
                calendar = CalendarSync(SELECTED_CALENDAR_ID)
                status = calendar.get_current_status(color_map=STATUS_COLOR_MAP)
            else:
                status = config.get("CURRENT_STATUS", "available")
            
            config["CURRENT_STATUS"] = status
            save_config(config)
            logger.info(f"Current status: {status} | Color map keys: {list(STATUS_COLOR_MAP.keys())}")
            return

        # Guard: If Govee credentials are missing, skip light control
        if not GOVEE_API_KEY or not GOVEE_DEVICE_ID or not GOVEE_DEVICE_MODEL:
            logger.error("Govee API key or Device ID not set.")
            return
        
        govee = GoveeController(GOVEE_API_KEY, GOVEE_DEVICE_ID, GOVEE_DEVICE_MODEL)

        manual_status = config.get("CURRENT_STATUS")
        manual_timestamp = config.get("MANUAL_STATUS_TIMESTAMP")
        manual_expiry = config.get("MANUAL_STATUS_EXPIRY", 2 * 60 * 60)  # Default 2 hours
        
        # Check if manual override has expired
        if manual_status and manual_timestamp:
            import time
            if time.time() - manual_timestamp > manual_expiry:
                logger.info(f"Manual status '{manual_status}' expired after {manual_expiry/3600:.1f} hours")
                manual_status = None
                config["CURRENT_STATUS"] = None
                config["MANUAL_STATUS_TIMESTAMP"] = None
                save_config(config)
        
        if DISABLE_CALENDAR_SYNC:
            if manual_status:
                status = manual_status
            else:
                # When calendar sync is disabled and no manual override, default to available
                status = "available"
                # Only turn off light if specifically configured to do so
                if config.get("POWER_OFF_WHEN_AVAILABLE", True):
                    govee.set_power("off")
                    return
        else:
            if manual_status == "meeting_ended_early":
                govee.set_power("off")
                return
            else:
                # Guard: If calendar ID or client_secret.json is missing, skip calendar sync
                client_secret_path = resource_path('resources/client_secret.json')
                if not SELECTED_CALENDAR_ID or not os.path.exists(client_secret_path):
                    logger.warning("Google Calendar ID or client_secret.json not set. Please configure in Settings.")
                    govee.set_power("off")
                    return
                
                calendar = CalendarSync(SELECTED_CALENDAR_ID)
                calendar_status, next_event_start = calendar.get_current_status(return_next_event_time=True, color_map=STATUS_COLOR_MAP)
                
                # Check for imminent meeting (within 1 minute) - this overrides manual status
                imminent_meeting = (
                    calendar_status == "available"
                    and next_event_start is not None
                    and (0 <= (next_event_start - datetime.datetime.now(datetime.timezone.utc)).total_seconds() <= 60)
                )
                
                # Check for active meeting - this also overrides manual status
                active_meeting = calendar_status == "in_meeting"
                
                if active_meeting or imminent_meeting:
                    # Calendar events take priority over manual overrides
                    status = "in_meeting"
                    if manual_status and manual_status != "in_meeting":
                        logger.info(f"Meeting starting - clearing manual override '{manual_status}'")
                        config["CURRENT_STATUS"] = None
                        config["MANUAL_STATUS_TIMESTAMP"] = None
                        save_config(config)
                elif manual_status:
                    status = manual_status
                else:
                    status = calendar_status

        color_map = STATUS_COLOR_MAP or {
            "in_meeting": {"color": "255,0,0", "power_off": False},
            "available": {"color": "0,255,0", "power_off": True},
            "focus": {"color": "0,0,255", "power_off": False},
            "offline": {"color": "128,128,128", "power_off": False},
        }

        logger.info(f"Current status: {status} | Color map keys: {list(color_map.keys())}")
        config["CURRENT_STATUS"] = status
        save_config(config)

        self.apply_status_to_light(govee, status, color_map, OFF_FOR_UNKNOWN_STATUS)

    def _sync_to_minute_boundary(self):
        """Calculate seconds until the next minute boundary and sleep until then."""
        now = datetime.datetime.now()
        seconds_into_minute = now.second + now.microsecond / 1_000_000
        seconds_until_next_minute = 60 - seconds_into_minute
        
        # Always sync to the next minute boundary, even if it's very soon
        # This ensures we start polling at exactly :00 seconds
        logger.info(f"Syncing to minute boundary: waiting {seconds_until_next_minute:.2f} seconds")
        time.sleep(seconds_until_next_minute)

    def _run(self):
        # First, sync to the minute boundary for precise timing
        self._sync_to_minute_boundary()
        
        while self._running:
            config = load_config()
            GOVEE_API_KEY = load_secret("GOVEE_API_KEY")
            GOVEE_DEVICE_ID = config.get("GOVEE_DEVICE_ID")
            GOVEE_DEVICE_MODEL = config.get("GOVEE_DEVICE_MODEL")
            SELECTED_CALENDAR_ID = config.get("SELECTED_CALENDAR_ID")
            STATUS_COLOR_MAP = config.get("STATUS_COLOR_MAP", {})
            REFRESH_INTERVAL = int(config.get("REFRESH_INTERVAL", 15))
            POWER_OFF_WHEN_AVAILABLE = bool(config.get("POWER_OFF_WHEN_AVAILABLE", True))
            OFF_FOR_UNKNOWN_STATUS = bool(config.get("OFF_FOR_UNKNOWN_STATUS", True))
            DISABLE_CALENDAR_SYNC = bool(config.get("DISABLE_CALENDAR_SYNC", False))
            DISABLE_LIGHT_CONTROL = bool(config.get("DISABLE_LIGHT_CONTROL", False))

            # Log the exact time we're checking for precision verification
            now = datetime.datetime.now()
            logger.info(f"Status check at: {now.strftime('%H:%M:%S.%f')[:-3]} (:{now.second:02d}.{now.microsecond//1000:03d})")

            # If light control is disabled, only track status without controlling lights
            if DISABLE_LIGHT_CONTROL:
                if not DISABLE_CALENDAR_SYNC:
                    calendar = CalendarSync(SELECTED_CALENDAR_ID)
                    status = calendar.get_current_status(color_map=STATUS_COLOR_MAP)
                else:
                    status = config.get("CURRENT_STATUS", "available")
                
                config["CURRENT_STATUS"] = status
                save_config(config)
                logger.info(f"Current status: {status} | Color map keys: {list(STATUS_COLOR_MAP.keys())}")
                self._sleep_until_next_interval(REFRESH_INTERVAL)
                continue

            # Guard: If Govee credentials are missing, skip light control
            if not GOVEE_API_KEY or not GOVEE_DEVICE_ID or not GOVEE_DEVICE_MODEL:
                logger.error("Govee API key or Device ID not set.")
                self._sleep_until_next_interval(REFRESH_INTERVAL)
                continue

            govee = GoveeController(GOVEE_API_KEY, GOVEE_DEVICE_ID, GOVEE_DEVICE_MODEL)

            if DISABLE_CALENDAR_SYNC:
                # When sync is disabled, still process manual status and control lights
                manual_status = config.get("CURRENT_STATUS")
                if manual_status:
                    # Process manual status with light control
                    try:
                        color_map = STATUS_COLOR_MAP or {
                            "in_meeting": {"color": "255,0,0", "power_off": False},
                            "available": {"color": "0,255,0", "power_off": True},
                            "focus": {"color": "0,0,255", "power_off": False},
                            "offline": {"color": "128,128,128", "power_off": False},
                        }
                        self.apply_status_to_light(govee, manual_status, color_map, OFF_FOR_UNKNOWN_STATUS)
                        logger.info(f"Manual status: {manual_status} (sync disabled)")
                    except Exception as e:
                        logger.error(f"Error setting light for manual status: {e}")
                else:
                    # No manual status, default behavior
                    if config.get("POWER_OFF_WHEN_AVAILABLE", True):
                        try:
                            govee.set_power("off")
                            logger.info("No manual status - lights off (sync disabled)")
                        except Exception as e:
                            logger.error(f"Error turning off lights: {e}")
                
                # Sleep until next interval and continue
                self._sleep_until_next_interval(REFRESH_INTERVAL)
                continue

            calendar = CalendarSync(SELECTED_CALENDAR_ID)
            try:
                manual_status = config.get("CURRENT_STATUS")
                manual_timestamp = config.get("MANUAL_STATUS_TIMESTAMP")
                manual_expiry = config.get("MANUAL_STATUS_EXPIRY", 2 * 60 * 60)  # Default 2 hours
                
                # Check if manual override has expired
                if manual_status and manual_timestamp:
                    import time
                    if time.time() - manual_timestamp > manual_expiry:
                        logger.info(f"Manual status '{manual_status}' expired after {manual_expiry/3600:.1f} hours")
                        manual_status = None
                        config["CURRENT_STATUS"] = None
                        config["MANUAL_STATUS_TIMESTAMP"] = None
                        save_config(config)
                
                if manual_status == "meeting_ended_early":
                    govee.set_power("off")
                    self._sleep_until_next_interval(REFRESH_INTERVAL)
                    continue
                else:
                    calendar_status, next_event_start = calendar.get_current_status(return_next_event_time=True, color_map=STATUS_COLOR_MAP)
                    
                    # Check for imminent meeting (within 1 minute) - this overrides manual status
                    imminent_meeting = (
                        calendar_status == "available"
                        and next_event_start is not None
                        and (0 <= (next_event_start - datetime.datetime.now(datetime.timezone.utc)).total_seconds() <= 60)
                    )
                    
                    # Check for active meeting - this also overrides manual status
                    active_meeting = calendar_status == "in_meeting"
                    
                    if active_meeting or imminent_meeting:
                        # Calendar events take priority over manual overrides
                        status = "in_meeting"
                        if manual_status and manual_status != "in_meeting":
                            logger.info(f"Meeting starting - clearing manual override '{manual_status}'")
                            config["CURRENT_STATUS"] = None
                            config["MANUAL_STATUS_TIMESTAMP"] = None
                            save_config(config)
                    elif manual_status:
                        status = manual_status
                    else:
                        status = calendar_status

                color_map = STATUS_COLOR_MAP or {
                    "in_meeting": {"color": "255,0,0", "power_off": False},
                    "available": {"color": "0,255,0", "power_off": True},
                    "focus": {"color": "0,0,255", "power_off": False},
                    "offline": {"color": "128,128,128", "power_off": False},
                }

                logger.info(f"Current status: {status} | Color map keys: {list(color_map.keys())}")

                self.apply_status_to_light(govee, status, color_map, OFF_FOR_UNKNOWN_STATUS)
            except Exception as e:
                logger.error(f"Error updating status: {e}")
            
            # Sleep until next scheduled check time (maintaining minute synchronization)
            self._sleep_until_next_interval(REFRESH_INTERVAL)

    def _sleep_until_next_interval(self, interval_seconds):
        """Sleep until the next scheduled check time, maintaining minute synchronization."""
        if interval_seconds == 60:
            # For 60-second intervals, sleep exactly until the next minute boundary
            now = datetime.datetime.now()
            seconds_into_minute = now.second + now.microsecond / 1_000_000
            sleep_time = 60 - seconds_into_minute
        else:
            # For other intervals, just sleep the specified time
            sleep_time = interval_seconds
            
        if sleep_time > 0:
            time.sleep(sleep_time)