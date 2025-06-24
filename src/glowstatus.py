import threading
import time
import datetime

from govee_controller import GoveeController
from calendar_sync import CalendarSync
from config_ui import load_config, load_secret
from logger import get_logger
from utils import normalize_status

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

    def update_now(self):
        config = load_config()
        GOVEE_API_KEY = load_secret("GOVEE_API_KEY")
        GOVEE_DEVICE_ID = config.get("GOVEE_DEVICE_ID")
        GOVEE_DEVICE_MODEL = config.get("GOVEE_DEVICE_MODEL")
        SELECTED_CALENDAR_ID = config.get("SELECTED_CALENDAR_ID", config.get("GOOGLE_CALENDAR_ID"))
        STATUS_COLOR_MAP = config.get("STATUS_COLOR_MAP", {})
        POWER_OFF_WHEN_AVAILABLE = bool(config.get("POWER_OFF_WHEN_AVAILABLE", True))
        OFF_FOR_UNKNOWN_STATUS = bool(config.get("OFF_FOR_UNKNOWN_STATUS", True))
        DISABLE_CALENDAR_SYNC = bool(config.get("DISABLE_CALENDAR_SYNC", False))

        govee = GoveeController(GOVEE_API_KEY, GOVEE_DEVICE_ID, GOVEE_DEVICE_MODEL)

        manual_status = config.get("CURRENT_STATUS")
        if DISABLE_CALENDAR_SYNC:
            if manual_status:
                status = manual_status
            else:
                govee.set_power("off")
                return
        else:
            if manual_status == "meeting_ended_early":
                govee.set_power("off")
                return
            elif manual_status:
                status = manual_status
            else:
                calendar = CalendarSync(SELECTED_CALENDAR_ID)
                status, next_event_start = calendar.get_current_status(return_next_event_time=True)
                if (
                    status == "available"
                    and next_event_start is not None
                    and (0 <= (next_event_start - datetime.datetime.now(datetime.timezone.utc)).total_seconds() <= 60)
                ):
                    status = "in_meeting"

        color_map = STATUS_COLOR_MAP or {
            "in_meeting": {"color": "255,0,0", "power_off": False},
            "available": {"color": "0,255,0", "power_off": True},
            "focus": {"color": "0,0,255", "power_off": False},
            "offline": {"color": "128,128,128", "power_off": False},
        }

        status_key = status.lower()
        entry = color_map.get(status_key)
        if entry:
            if entry.get("power_off"):
                govee.set_power("off")
            else:
                rgb_str = entry.get("color", "255,255,255")
                r, g, b = map(int, rgb_str.split(","))
                govee.set_power("on")
                govee.set_color(r, g, b)
        else:
            if OFF_FOR_UNKNOWN_STATUS:
                govee.set_power("off")
            else:
                govee.set_power("on")
                govee.set_color(255, 255, 255)

    def _run(self):
        while self._running:
            config = load_config()
            GOVEE_API_KEY = load_secret("GOVEE_API_KEY")
            GOVEE_DEVICE_ID = config.get("GOVEE_DEVICE_ID")
            GOVEE_DEVICE_MODEL = config.get("GOVEE_DEVICE_MODEL")
            SELECTED_CALENDAR_ID = config.get("SELECTED_CALENDAR_ID", config.get("GOOGLE_CALENDAR_ID"))
            STATUS_COLOR_MAP = config.get("STATUS_COLOR_MAP", {})
            REFRESH_INTERVAL = int(config.get("REFRESH_INTERVAL", 60))
            POWER_OFF_WHEN_AVAILABLE = bool(config.get("POWER_OFF_WHEN_AVAILABLE", True))
            OFF_FOR_UNKNOWN_STATUS = bool(config.get("OFF_FOR_UNKNOWN_STATUS", True))
            DISABLE_CALENDAR_SYNC = bool(config.get("DISABLE_CALENDAR_SYNC", False))

            govee = GoveeController(GOVEE_API_KEY, GOVEE_DEVICE_ID, GOVEE_DEVICE_MODEL)

            if DISABLE_CALENDAR_SYNC:
                time.sleep(REFRESH_INTERVAL)
                continue

            calendar = CalendarSync(SELECTED_CALENDAR_ID)
            try:
                manual_status = config.get("CURRENT_STATUS")
                if manual_status == "meeting_ended_early":
                    govee.set_power("off")
                    time.sleep(REFRESH_INTERVAL)
                    continue
                elif manual_status:
                    status = manual_status
                else:
                    status, next_event_start = calendar.get_current_status(return_next_event_time=True)
                    if (
                        status == "available"
                        and next_event_start is not None
                        and (0 <= (next_event_start - datetime.datetime.now(datetime.timezone.utc)).total_seconds() <= 60)
                    ):
                        status = "in_meeting"

                color_map = STATUS_COLOR_MAP or {
                    "in_meeting": {"color": "255,0,0", "power_off": False},
                    "available": {"color": "0,255,0", "power_off": True},
                    "focus": {"color": "0,0,255", "power_off": False},
                    "offline": {"color": "128,128,128", "power_off": False},
                }

                status_key = status.lower()
                entry = color_map.get(status_key)
                if entry:
                    if entry.get("power_off"):
                        govee.set_power("off")
                    else:
                        rgb_str = entry.get("color", "255,255,255")
                        r, g, b = map(int, rgb_str.split(","))
                        govee.set_power("on")
                        govee.set_color(r, g, b)
                else:
                    if OFF_FOR_UNKNOWN_STATUS:
                        govee.set_power("off")
                    else:
                        govee.set_power("on")
                        govee.set_color(255, 255, 255)
            except Exception as e:
                logger.error(f"Error updating status: {e}")
            time.sleep(REFRESH_INTERVAL)