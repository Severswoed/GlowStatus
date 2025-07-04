import threading
import time
import datetime
import os

from govee_controller import GoveeController
from calendar_sync import CalendarSync
from settings_ui import load_config, save_config
from logger import get_logger
from utils import normalize_status, load_secret, resource_path

logger = get_logger()

def ensure_timezone_aware(dt):
    """Ensure datetime is timezone-aware, defaulting to UTC if naive."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Assume naive datetimes from calendar are in UTC
        return dt.replace(tzinfo=datetime.timezone.utc)
    return dt

def safe_datetime_diff(future_dt, current_dt):
    """Safely calculate time difference between datetimes, handling timezone issues."""
    try:
        if future_dt is None or current_dt is None:
            return None
        
        # Ensure both datetimes are timezone-aware
        future_aware = ensure_timezone_aware(future_dt)
        current_aware = ensure_timezone_aware(current_dt)
        
        return (future_aware - current_aware).total_seconds()
    except Exception as e:
        logger.error(f"Error calculating datetime difference: {e}")
        return None

class GlowStatusController:

    def end_meeting_early(self):
        """Set manual status to 'meeting_ended_early' and snooze until the end of the current meeting (robust).
        Also records the event ID (or summary+start) to avoid snooze being interrupted by the same event."""
        config = load_config()
        SELECTED_CALENDAR_ID = config.get("SELECTED_CALENDAR_ID")
        if not SELECTED_CALENDAR_ID:
            logger.warning("No calendar selected, cannot snooze to meeting end.")
            return
        try:
            calendar = CalendarSync(SELECTED_CALENDAR_ID)
            now = datetime.datetime.now(datetime.timezone.utc)
            events = []
            try:
                events_result = calendar.service.events().list(
                    calendarId=SELECTED_CALENDAR_ID,
                    timeMin=(now - datetime.timedelta(minutes=15)).isoformat(),
                    timeMax=(now + datetime.timedelta(days=1)).isoformat(),
                    maxResults=10,
                    singleEvents=True,
                    orderBy="startTime",
                ).execute()
                events = events_result.get("items", [])
            except Exception as e:
                logger.error(f"Failed to fetch events for robust end_meeting_early: {e}")
            ongoing_events = []
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                end = event["end"].get("dateTime", event["end"].get("date"))
                try:
                    start_dt = ensure_timezone_aware(datetime.datetime.fromisoformat(start.replace('Z', '+00:00')))
                    end_dt = ensure_timezone_aware(datetime.datetime.fromisoformat(end.replace('Z', '+00:00')))
                except Exception as e:
                    logger.warning(f"Could not parse event times: {e}")
                    continue
                logger.info(f"[end_meeting_early] Candidate event: {event.get('summary', '')} | Start: {start_dt} | End: {end_dt} | Now: {now}")
                if start_dt <= now <= end_dt:
                    ongoing_events.append((event, end_dt))
            if ongoing_events:
                # Pick the event with the latest end time
                latest_event, latest_end = max(ongoing_events, key=lambda tup: tup[1])
                config["SNOOZE_UNTIL"] = latest_end.isoformat()
                # Store event id or fallback to summary+start
                event_id = latest_event.get("id")
                if event_id:
                    config["SNOOZE_EVENT_ID"] = event_id
                else:
                    config["SNOOZE_EVENT_SUMMARY"] = latest_event.get("summary", "")
                    config["SNOOZE_EVENT_START"] = latest_event["start"].get("dateTime", latest_event["start"].get("date"))
                logger.info(f"[end_meeting_early] Found {len(ongoing_events)} ongoing event(s), snoozing until latest end: {latest_end}")
            else:
                logger.warning("[end_meeting_early] No ongoing event found, falling back to legacy 5 min snooze.")
                config["SNOOZE_UNTIL"] = None
                config.pop("SNOOZE_EVENT_ID", None)
                config.pop("SNOOZE_EVENT_SUMMARY", None)
                config.pop("SNOOZE_EVENT_START", None)
            config["CURRENT_STATUS"] = "meeting_ended_early"
            config["MANUAL_STATUS_TIMESTAMP"] = time.time()
            save_config(config)
            logger.info(f"Meeting ended early: snoozing until {config['SNOOZE_UNTIL']}")
        except Exception as e:
            logger.error(f"Failed to set snooze until meeting end: {e}")
    def __init__(self):
        self._running = False
        self._thread = None
        self._restart_count = 0
        self._max_restarts = 5
        # Track last light state to avoid redundant API calls
        self._last_power_state = None
        self._last_rgb_color = None
        # Track the two most relevant meetings in memory
        self._current_meeting = None  # Dict with keys: id, summary, start, end
        self._next_meeting = None     # Dict with keys: id, summary, start, end

    def start(self):
        if self._running:
            return
        self._running = True
        # Immediately update status on startup (handles in-progress/imminent meetings)
        try:
            self.update_now()
        except Exception as e:
            logger.error(f"Immediate status update on startup failed: {e}")
        self._thread = threading.Thread(target=self._run_with_monitoring, daemon=True)
        self._thread.start()
        logger.info("GlowStatus controller started")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def apply_status_to_light(self, govee, status, color_map, off_for_unknown_status):
        status_key = status.lower()
        entry = color_map.get(status_key)
        
        desired_power_state = None
        desired_rgb_color = None
        
        if entry:
            # Backward compatibility: if entry is a string, treat as color only
            if isinstance(entry, str):
                desired_power_state = "on"
                rgb_str = entry
                try:
                    desired_rgb_color = tuple(map(int, rgb_str.split(",")))
                except Exception as e:
                    logger.error(f"Invalid RGB string '{rgb_str}' for status '{status_key}': {e}")
                    desired_rgb_color = (255, 255, 255)
            elif isinstance(entry, dict):
                if entry.get("power_off"):
                    desired_power_state = "off"
                    desired_rgb_color = None  # Don't set color when off
                else:
                    desired_power_state = "on"
                    rgb_str = entry.get("color", "255,255,255")
                    try:
                        desired_rgb_color = tuple(map(int, rgb_str.split(",")))
                    except Exception as e:
                        logger.error(f"Invalid RGB string '{rgb_str}' for status '{status_key}': {e}")
                        desired_rgb_color = (255, 255, 255)
        else:
            if off_for_unknown_status:
                desired_power_state = "off"
                desired_rgb_color = None
            else:
                desired_power_state = "on"
                desired_rgb_color = (255, 255, 255)
        
        # Only send API calls if state has actually changed
        api_calls_made = 0
        
        # Check if power state needs to change
        if self._last_power_state != desired_power_state:
            try:
                govee.set_power(desired_power_state)
                self._last_power_state = desired_power_state
                api_calls_made += 1
                logger.info(f"✅ Power state changed to: {desired_power_state}")
            except Exception as e:
                logger.error(f"Failed to set power state: {e}")
                # Don't update state if API call failed
        else:
            logger.debug(f"Power state unchanged: {desired_power_state}")
        
        # Only set color if we're turning on and color is different
        if (desired_power_state == "on" and desired_rgb_color and 
            self._last_rgb_color != desired_rgb_color):
            try:
                r, g, b = desired_rgb_color
                govee.set_color(r, g, b)
                self._last_rgb_color = desired_rgb_color
                api_calls_made += 1
                logger.info(f"🎨 Color changed to RGB{desired_rgb_color}")
            except Exception as e:
                logger.error(f"Failed to set color: {e}")
                # Don't update state if API call failed
        elif desired_power_state == "on" and desired_rgb_color:
            logger.debug(f"Color unchanged: RGB{desired_rgb_color}")
        
        if api_calls_made == 0:
            logger.info(f"⏸️  No API calls needed - light already in desired state (power: {desired_power_state}, color: {desired_rgb_color})")
        else:
            logger.info(f"📡 Made {api_calls_made} Govee API call(s) for status '{status}'")
        
        # Clear color tracking when turning off
        if desired_power_state == "off":
            self._last_rgb_color = None

    def update_now(self):
        try:
            self._update_now_impl()
            # Log in-memory meeting state for tracing and debugging
            logger.info("[DEBUG] In-memory meeting state:")
            logger.info(f"  _current_meeting: {self._current_meeting}")
            logger.info(f"  _next_meeting: {self._next_meeting}")
        except Exception as e:
            logger.error(f"Critical error during status update: {e}")
            # Auto-disable calendar sync if we encounter any critical errors
            config = load_config()
            if not config.get("DISABLE_CALENDAR_SYNC", False):
                config["DISABLE_CALENDAR_SYNC"] = True
                save_config(config)
                logger.info("Auto-disabled calendar sync due to critical error")

    def _update_now_impl(self):
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

        # Always fetch the next two meetings and store in memory
        self._current_meeting = None
        self._next_meeting = None
        calendar_events = []
        if not DISABLE_CALENDAR_SYNC and SELECTED_CALENDAR_ID:
            try:
                calendar = CalendarSync(SELECTED_CALENDAR_ID)
                now_utc = datetime.datetime.now(datetime.timezone.utc)
                # Query only the next 2 hours (plus 15 min in the past for ongoing)
                events_result = calendar.service.events().list(
                    calendarId=SELECTED_CALENDAR_ID,
                    timeMin=(now_utc - datetime.timedelta(minutes=15)).isoformat(),
                    timeMax=(now_utc + datetime.timedelta(hours=2)).isoformat(),
                    maxResults=10,
                    singleEvents=True,
                    orderBy="startTime",
                ).execute()
                events = events_result.get("items", [])
                # Sort and filter for ongoing and next events
                ongoing = []
                upcoming = []
                for event in events:
                    start = event["start"].get("dateTime", event["start"].get("date"))
                    end = event["end"].get("dateTime", event["end"].get("date"))
                    try:
                        start_dt = ensure_timezone_aware(datetime.datetime.fromisoformat(start.replace('Z', '+00:00')))
                        end_dt = ensure_timezone_aware(datetime.datetime.fromisoformat(end.replace('Z', '+00:00')))
                    except Exception:
                        continue
                    if start_dt <= now_utc <= end_dt:
                        ongoing.append({"id": event.get("id"), "summary": event.get("summary", ""), "start": start_dt, "end": end_dt})
                    elif now_utc < start_dt:
                        upcoming.append({"id": event.get("id"), "summary": event.get("summary", ""), "start": start_dt, "end": end_dt})
                # Track the two most relevant meetings
                if ongoing:
                    self._current_meeting = max(ongoing, key=lambda e: e["end"])
                if upcoming:
                    self._next_meeting = min(upcoming, key=lambda e: e["start"])
                calendar_events = ongoing + upcoming
            except Exception as e:
                logger.error(f"Failed to fetch calendar events for meeting tracking: {e}")

        # --- Log in-memory meeting state for tracing/debugging ---
        def _meeting_repr(meeting):
            if not meeting:
                return None
            return {
                "id": meeting.get("id"),
                "summary": meeting.get("summary"),
                "start": str(meeting.get("start")),
                "end": str(meeting.get("end")),
            }
        logger.info(f"[STATE] In-memory meeting state: _current_meeting={_meeting_repr(self._current_meeting)}, _next_meeting={_meeting_repr(self._next_meeting)}")

        # Guard: If light control is disabled, only update status without controlling lights
        if DISABLE_LIGHT_CONTROL:
            logger.info("Light control disabled - status tracking only")
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
        snooze_until = config.get("SNOOZE_UNTIL")
        snooze_event_id = config.get("SNOOZE_EVENT_ID")
        snooze_event_summary = config.get("SNOOZE_EVENT_SUMMARY")
        snooze_event_start = config.get("SNOOZE_EVENT_START")

        # --- Core logic: always check for next meeting and 1-minute warning ---
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        next_meeting_start = self._next_meeting["start"] if self._next_meeting else None
        next_meeting_id = self._next_meeting["id"] if self._next_meeting else None
        current_meeting_id = self._current_meeting["id"] if self._current_meeting else None
        # If snoozing (meeting ended early), only snooze until the original meeting's scheduled end, unless a new meeting is within 1 minute
        if manual_status == "meeting_ended_early" and snooze_until:
            try:
                snooze_until_dt = ensure_timezone_aware(datetime.datetime.fromisoformat(snooze_until))
            except Exception:
                snooze_until_dt = None
            # If a new meeting is within 1 minute, clear snooze and turn on light
            if next_meeting_start:
                seconds_until_next = (next_meeting_start - now_utc).total_seconds()
                if 0 <= seconds_until_next <= 60:
                    logger.info(f"[snooze override] New meeting '{self._next_meeting['summary']}' starts in {seconds_until_next:.1f}s, clearing snooze and turning on light.")
                    config["CURRENT_STATUS"] = None
                    config["MANUAL_STATUS_TIMESTAMP"] = None
                    config["SNOOZE_UNTIL"] = None
                    config.pop("SNOOZE_EVENT_ID", None)
                    config.pop("SNOOZE_EVENT_SUMMARY", None)
                    config.pop("SNOOZE_EVENT_START", None)
                    save_config(config)
                    manual_status = None
            # If still within snooze period, keep light off/green
            if snooze_until_dt and now_utc < snooze_until_dt and manual_status == "meeting_ended_early":
                logger.info(f"[snooze] Still within snooze period until {snooze_until_dt}, keeping light off/green.")
                status = "available"
                color_map = STATUS_COLOR_MAP or {}
                if "available" in color_map:
                    self.apply_status_to_light(govee, status, color_map, OFF_FOR_UNKNOWN_STATUS)
                else:
                    if POWER_OFF_WHEN_AVAILABLE:
                        govee.set_power("off")
                        self._last_power_state = "off"
                        self._last_rgb_color = None
                    else:
                        govee.set_power("on")
                        govee.set_color(0, 255, 0)
                        self._last_power_state = "on"
                        self._last_rgb_color = (0, 255, 0)
                return
            # If snooze expired, clear manual status
            if snooze_until_dt and now_utc >= snooze_until_dt:
                logger.info(f"[snooze expired] Snooze period ended at {snooze_until_dt}, resuming normal logic.")
                config["CURRENT_STATUS"] = None
                config["MANUAL_STATUS_TIMESTAMP"] = None
                config["SNOOZE_UNTIL"] = None
                config.pop("SNOOZE_EVENT_ID", None)
                config.pop("SNOOZE_EVENT_SUMMARY", None)
                config.pop("SNOOZE_EVENT_START", None)
                save_config(config)
                manual_status = None

        # --- Main logic: always give 1-minute warning for next meeting ---
        imminent = False
        if next_meeting_start:
            seconds_until_next = (next_meeting_start - now_utc).total_seconds()
            if 0 <= seconds_until_next <= 60:
                imminent = True
        # If a meeting is ongoing (not ended early), or imminent, turn on light
        if (self._current_meeting and manual_status != "meeting_ended_early") or imminent:
            status = "in_meeting"
            if manual_status and manual_status != "in_meeting":
                logger.info(f"Meeting starting or imminent - clearing manual override '{manual_status}'")
                config["CURRENT_STATUS"] = None
                config["MANUAL_STATUS_TIMESTAMP"] = None
                config["SNOOZE_UNTIL"] = None
                config.pop("SNOOZE_EVENT_ID", None)
                config.pop("SNOOZE_EVENT_SUMMARY", None)
                config.pop("SNOOZE_EVENT_START", None)
                save_config(config)
        elif manual_status:
            status = manual_status
        else:
            status = "available"

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

        # Check if manual override has expired or is invalid
        if manual_status:
            if manual_timestamp:
                import time
                if time.time() - manual_timestamp > manual_expiry:
                    logger.info(f"Manual status '{manual_status}' expired after {manual_expiry/3600:.1f} hours")
                    # --- PATCH: If snooze/manual 'available' was for end_meeting_early, check if the same meeting is still ongoing or only a new meeting is imminent ---
                    if manual_status == "available" and snooze_event_id:
                        client_secret_path = resource_path('resources/client_secret.json')
                        if SELECTED_CALENDAR_ID and os.path.exists(client_secret_path):
                            calendar = CalendarSync(SELECTED_CALENDAR_ID)
                            try:
                                now_utc = datetime.datetime.now(datetime.timezone.utc)
                                events_result = calendar.service.events().list(
                                    calendarId=SELECTED_CALENDAR_ID,
                                    timeMin=(now_utc - datetime.timedelta(minutes=15)).isoformat(),
                                    timeMax=(now_utc + datetime.timedelta(days=1)).isoformat(),
                                    maxResults=10,
                                    singleEvents=True,
                                    orderBy="startTime",
                                ).execute()
                                events = events_result.get("items", [])
                            except Exception as e:
                                logger.error(f"Failed to fetch events for snooze expiry check: {e}")
                                events = []
                            same_meeting_ongoing = False
                            new_meeting_imminent = False
                            imminent_window = datetime.timedelta(minutes=5)
                            turn_on_window = datetime.timedelta(seconds=60)
                            soonest_new_meeting_start = None
                            soonest_new_meeting_summary = None
                            for event in events:
                                start = event["start"].get("dateTime", event["start"].get("date"))
                                end = event["end"].get("dateTime", event["end"].get("date"))
                                try:
                                    start_dt = ensure_timezone_aware(datetime.datetime.fromisoformat(start.replace('Z', '+00:00')))
                                    end_dt = ensure_timezone_aware(datetime.datetime.fromisoformat(end.replace('Z', '+00:00')))
                                except Exception as e:
                                    logger.warning(f"[snooze expiry check] Could not parse event times: {e}")
                                    continue
                                is_same_event = False
                                if snooze_event_id and event.get("id") == snooze_event_id:
                                    is_same_event = True
                                elif not snooze_event_id and snooze_event_summary and snooze_event_start:
                                    if (event.get("summary", "") == snooze_event_summary and start == snooze_event_start):
                                        is_same_event = True
                                if is_same_event and start_dt <= now_utc <= end_dt:
                                    same_meeting_ongoing = True
                                # Check for new imminent/ongoing meeting
                                is_ongoing_or_imminent = (start_dt <= now_utc <= end_dt) or (now_utc < start_dt <= now_utc + imminent_window)
                                if is_ongoing_or_imminent and not is_same_event:
                                    # Only consider as imminent if within 60s
                                    if soonest_new_meeting_start is None or start_dt < soonest_new_meeting_start:
                                        soonest_new_meeting_start = start_dt
                                        soonest_new_meeting_summary = event.get('summary', '')
                                    seconds_until_meeting = (start_dt - now_utc).total_seconds()
                                    if start_dt <= now_utc or seconds_until_meeting <= 60:
                                        new_meeting_imminent = True
                            if same_meeting_ongoing and not new_meeting_imminent:
                                # Extend manual status for another minute, or until meeting end
                                config["CURRENT_STATUS"] = "available"
                                config["MANUAL_STATUS_TIMESTAMP"] = time.time()
                                # Set expiry to the remaining time until meeting end, or 60s
                                expiry_seconds = 60
                                for event in events:
                                    start = event["start"].get("dateTime", event["start"].get("date"))
                                    end = event["end"].get("dateTime", event["end"].get("date"))
                                    try:
                                        start_dt = ensure_timezone_aware(datetime.datetime.fromisoformat(start.replace('Z', '+00:00')))
                                        end_dt = ensure_timezone_aware(datetime.datetime.fromisoformat(end.replace('Z', '+00:00')))
                                    except Exception:
                                        continue
                                    is_same_event = False
                                    if snooze_event_id and event.get("id") == snooze_event_id:
                                        is_same_event = True
                                    elif not snooze_event_id and snooze_event_summary and snooze_event_start:
                                        if (event.get("summary", "") == snooze_event_summary and start == snooze_event_start):
                                            is_same_event = True
                                    if is_same_event and start_dt <= now_utc <= end_dt:
                                        expiry_seconds = max(60, int((end_dt - now_utc).total_seconds()))
                                        break
                                config["MANUAL_STATUS_EXPIRY"] = expiry_seconds
                                save_config(config)
                                manual_status = "available"
                                # Set light to available/off
                                status = "available"
                                color_map = STATUS_COLOR_MAP or {}
                                if "available" in color_map:
                                    self.apply_status_to_light(govee, status, color_map, OFF_FOR_UNKNOWN_STATUS)
                                else:
                                    if POWER_OFF_WHEN_AVAILABLE:
                                        govee.set_power("off")
                                        self._last_power_state = "off"
                                        self._last_rgb_color = None
                                        logger.info("POWER_OFF_WHEN_AVAILABLE is True: turned light off for 'available' status (snooze expiry)")
                                    else:
                                        govee.set_power("on")
                                        govee.set_color(0, 255, 0)
                                        self._last_power_state = "on"
                                        self._last_rgb_color = (0, 255, 0)
                                        logger.info("POWER_OFF_WHEN_AVAILABLE is False: set light to green for 'available' status (snooze expiry)")
                                logger.info("[snooze expiry check] Still in the same meeting that was ended early and no new imminent meeting; remaining 'available'.")
                                return
                    # --- END PATCH ---
                    manual_status = None
                    config["CURRENT_STATUS"] = None
                    config["MANUAL_STATUS_TIMESTAMP"] = None
                    config["SNOOZE_UNTIL"] = None
                    config.pop("SNOOZE_EVENT_ID", None)
                    config.pop("SNOOZE_EVENT_SUMMARY", None)
                    config.pop("SNOOZE_EVENT_START", None)
                    save_config(config)
            elif manual_status != "meeting_ended_early":
                logger.warning(f"Manual status '{manual_status}' has no timestamp - clearing invalid manual override")
                manual_status = None
                config["CURRENT_STATUS"] = None
                config["MANUAL_STATUS_TIMESTAMP"] = None
                config["SNOOZE_UNTIL"] = None
                config.pop("SNOOZE_EVENT_ID", None)
                config.pop("SNOOZE_EVENT_SUMMARY", None)
                config.pop("SNOOZE_EVENT_START", None)
                save_config(config)

        if DISABLE_CALENDAR_SYNC:
            if manual_status:
                status = manual_status
            else:
                status = "available"
                if config.get("POWER_OFF_WHEN_AVAILABLE", True):
                    govee.set_power("off")
                    return
        else:
            if manual_status == "meeting_ended_early":
                import time
                now_utc = datetime.datetime.now(datetime.timezone.utc)
                # If snooze_until is set, use it for robust snooze logic
                if snooze_until:
                    try:
                        snooze_until_dt = ensure_timezone_aware(datetime.datetime.fromisoformat(snooze_until))
                    except Exception as e:
                        logger.warning(f"Invalid SNOOZE_UNTIL value: {snooze_until} ({e}) - clearing snooze")
                        snooze_until_dt = None
                        config["SNOOZE_UNTIL"] = None
                        save_config(config)
                    if snooze_until_dt and now_utc < snooze_until_dt:
                        # Check for any ongoing meeting (not just next event), but ignore the event we snoozed for
                        client_secret_path = resource_path('resources/client_secret.json')
                        if SELECTED_CALENDAR_ID and os.path.exists(client_secret_path):
                            calendar = CalendarSync(SELECTED_CALENDAR_ID)
                            try:
                                events_result = calendar.service.events().list(
                                    calendarId=SELECTED_CALENDAR_ID,
                                    timeMin=(now_utc - datetime.timedelta(minutes=15)).isoformat(),
                                    timeMax=(now_utc + datetime.timedelta(days=1)).isoformat(),
                                    maxResults=10,
                                    singleEvents=True,
                                    orderBy="startTime",
                                ).execute()
                                events = events_result.get("items", [])
                            except Exception as e:
                                logger.error(f"Failed to fetch events for overlap check: {e}")
                                events = []
                            found_overlap = False
                            snooze_event_id = config.get("SNOOZE_EVENT_ID")
                            snooze_event_summary = config.get("SNOOZE_EVENT_SUMMARY")
                            snooze_event_start = config.get("SNOOZE_EVENT_START")
                            imminent_window = datetime.timedelta(minutes=5)
                            turn_on_window = datetime.timedelta(seconds=60)
                            soonest_new_meeting_start = None
                            soonest_new_meeting_summary = None
                            for event in events:
                                start = event["start"].get("dateTime", event["start"].get("date"))
                                end = event["end"].get("dateTime", event["end"].get("date"))
                                try:
                                    start_dt = ensure_timezone_aware(datetime.datetime.fromisoformat(start.replace('Z', '+00:00')))
                                    end_dt = ensure_timezone_aware(datetime.datetime.fromisoformat(end.replace('Z', '+00:00')))
                                except Exception as e:
                                    logger.warning(f"[snooze overlap check] Could not parse event times: {e}")
                                    continue
                                logger.info(f"[snooze overlap check] Candidate event: {event.get('summary', '')} | Start: {start_dt} | End: {end_dt} | Now: {now_utc}")
                                is_same_event = False
                                if snooze_event_id and event.get("id") == snooze_event_id:
                                    is_same_event = True
                                elif not snooze_event_id and snooze_event_summary and snooze_event_start:
                                    if (event.get("summary", "") == snooze_event_summary and start == snooze_event_start):
                                        is_same_event = True
                                is_ongoing_or_imminent = (start_dt <= now_utc <= end_dt) or (now_utc < start_dt <= now_utc + imminent_window)
                                if is_ongoing_or_imminent and not is_same_event:
                                    found_overlap = True
                                    # Track the soonest new meeting start for later logic
                                    if soonest_new_meeting_start is None or start_dt < soonest_new_meeting_start:
                                        soonest_new_meeting_start = start_dt
                                        soonest_new_meeting_summary = event.get('summary', '')
                                    logger.info(f"🔄 Overlapping NEW meeting detected during snooze! Event: {event.get('summary', '')} | Start: {start_dt} | End: {end_dt}")
                            if found_overlap:
                                # Only turn on light if the new meeting is ongoing or within 60 seconds
                                if soonest_new_meeting_start:
                                    seconds_until_meeting = (soonest_new_meeting_start - now_utc).total_seconds()
                                    if soonest_new_meeting_start <= now_utc or seconds_until_meeting <= 60:
                                        logger.info(f"Switching to 'in_meeting' for new event '{soonest_new_meeting_summary}' (starts at {soonest_new_meeting_start}) - within 60s or already started.")
                                        config["CURRENT_STATUS"] = None
                                        config["MANUAL_STATUS_TIMESTAMP"] = None
                                        config["SNOOZE_UNTIL"] = None
                                        config.pop("SNOOZE_EVENT_ID", None)
                                        config.pop("SNOOZE_EVENT_SUMMARY", None)
                                        config.pop("SNOOZE_EVENT_START", None)
                                        save_config(config)
                                        manual_status = None
                                        # Light will be set to 'in_meeting' on next loop
                                    else:
                                        logger.info(f"New meeting detected but not within 60s (starts in {seconds_until_meeting:.1f}s), will remain 'available' until 60s before start.")
                                        # Explicitly set light to available/off now, following config and color map
                                        status = "available"
                                        color_map = STATUS_COLOR_MAP or {}
                                        if "available" in color_map:
                                            self.apply_status_to_light(govee, status, color_map, OFF_FOR_UNKNOWN_STATUS)
                                        else:
                                            # Fallback: use POWER_OFF_WHEN_AVAILABLE config
                                            if POWER_OFF_WHEN_AVAILABLE:
                                                govee.set_power("off")
                                                self._last_power_state = "off"
                                                self._last_rgb_color = None
                                                logger.info("POWER_OFF_WHEN_AVAILABLE is True: turned light off for 'available' status")
                                            else:
                                                # Default to green if not specified
                                                govee.set_power("on")
                                                govee.set_color(0, 255, 0)
                                                self._last_power_state = "on"
                                                self._last_rgb_color = (0, 255, 0)
                                                logger.info("POWER_OFF_WHEN_AVAILABLE is False: set light to green for 'available' status")
                                        config["CURRENT_STATUS"] = "available"
                                        # Set manual status timestamp and expiry to expire 60s before the new meeting
                                        config["MANUAL_STATUS_TIMESTAMP"] = time.time()
                                        # Expiry: time until (soonest_new_meeting_start - 60s), or at least 30s
                                        expiry_seconds = max(30, int(seconds_until_meeting - 60)) if seconds_until_meeting > 60 else 30
                                        config["MANUAL_STATUS_EXPIRY"] = expiry_seconds
                                        config["SNOOZE_UNTIL"] = snooze_until
                                        config.pop("SNOOZE_EVENT_ID", None)
                                        config.pop("SNOOZE_EVENT_SUMMARY", None)
                                        config.pop("SNOOZE_EVENT_START", None)
                                        save_config(config)
                                        manual_status = "available"
                                        logger.info(f"Manual status 'available' will expire in {expiry_seconds} seconds (60s before new meeting)")
                                return
                            else:
                                logger.info(f"Meeting ended early - snoozing until {snooze_until_dt} (meeting end)")
                                # Always set light to available/off during snooze if no overlap
                                status = "available"
                                color_map = STATUS_COLOR_MAP or {
                                    "in_meeting": {"color": "255,0,0", "power_off": False},
                                    "available": {"color": "0,255,0", "power_off": True},
                                    "focus": {"color": "0,0,255", "power_off": False},
                                    "offline": {"color": "128,128,128", "power_off": False},
                                }
                                self.apply_status_to_light(govee, status, color_map, OFF_FOR_UNKNOWN_STATUS)
                                return
                        else:
                            logger.info(f"Meeting ended early - snoozing until {snooze_until_dt} (meeting end, no calendar available)")
                            status = "available"
                            color_map = STATUS_COLOR_MAP or {
                                "in_meeting": {"color": "255,0,0", "power_off": False},
                                "available": {"color": "0,255,0", "power_off": True},
                                "focus": {"color": "0,0,255", "power_off": False},
                                "offline": {"color": "128,128,128", "power_off": False},
                            }
                            self.apply_status_to_light(govee, status, color_map, OFF_FOR_UNKNOWN_STATUS)
                            return
                    else:
                        logger.info(f"Meeting ended early snooze period expired (meeting ended at {snooze_until}) - resuming calendar control")
                        config["CURRENT_STATUS"] = None
                        config["MANUAL_STATUS_TIMESTAMP"] = None
                        config["SNOOZE_UNTIL"] = None
                        save_config(config)
                        manual_status = None
                else:
                    # Fallback: no snooze_until, use legacy 5 min snooze
                    if manual_timestamp:
                        snooze_duration = 5 * 60
                        time_since_ended = time.time() - manual_timestamp
                        if time_since_ended > snooze_duration:
                            logger.info(f"Meeting ended early legacy snooze expired ({time_since_ended/60:.1f} min) - resuming calendar control")
                            config["CURRENT_STATUS"] = None
                            config["MANUAL_STATUS_TIMESTAMP"] = None
                            config["SNOOZE_UNTIL"] = None
                            save_config(config)
                            manual_status = None
                        else:
                            logger.info(f"Meeting ended early - legacy snoozing for {(snooze_duration - time_since_ended)/60:.1f} more min")
                            status = "available"
                            color_map = STATUS_COLOR_MAP or {
                                "in_meeting": {"color": "255,0,0", "power_off": False},
                                "available": {"color": "0,255,0", "power_off": True},
                                "focus": {"color": "0,0,255", "power_off": False},
                                "offline": {"color": "128,128,128", "power_off": False},
                            }
                            self.apply_status_to_light(govee, status, color_map, OFF_FOR_UNKNOWN_STATUS)
                            return
                    else:
                        logger.info(f"Meeting ended early - indefinite legacy snooze (no end time)")
                        status = "available"
                        color_map = STATUS_COLOR_MAP or {
                            "in_meeting": {"color": "255,0,0", "power_off": False},
                            "available": {"color": "0,255,0", "power_off": True},
                            "focus": {"color": "0,0,255", "power_off": False},
                            "offline": {"color": "128,128,128", "power_off": False},
                        }
                        self.apply_status_to_light(govee, status, color_map, OFF_FOR_UNKNOWN_STATUS)
                        return

            # Guard: If calendar ID or client_secret.json is missing, skip calendar sync
            client_secret_path = resource_path('resources/client_secret.json')
            if not SELECTED_CALENDAR_ID or not os.path.exists(client_secret_path):
                logger.warning("Google Calendar ID or client_secret.json not set. Please configure in Settings.")
                govee.set_power("off")
                return

            try:
                calendar = CalendarSync(SELECTED_CALENDAR_ID)
                calendar_status, next_event_start = calendar.get_current_status(return_next_event_time=True, color_map=STATUS_COLOR_MAP)
            except Exception as e:
                logger.warning(f"Calendar sync failed (token may be expired): {e}")
                config["DISABLE_CALENDAR_SYNC"] = True
                save_config(config)
                logger.info("Auto-disabled calendar sync due to authentication failure")
                govee.set_power("off")
                return

            time_to_next = safe_datetime_diff(next_event_start, datetime.datetime.now(datetime.timezone.utc))
            imminent_meeting = (
                time_to_next is not None
                and (0 <= time_to_next <= 60)
            )

            if next_event_start:
                if time_to_next is not None:
                    logger.info(f"Next meeting in {time_to_next:.1f} seconds | Calendar status: {calendar_status} | Manual status: {manual_status}")
                    if imminent_meeting:
                        logger.info("🚨 IMMINENT MEETING DETECTED - should turn on lights!")
                else:
                    logger.warning("Unable to calculate time to next meeting due to timezone issues")

            active_meeting = calendar_status == "in_meeting"

            if active_meeting or imminent_meeting:
                status = "in_meeting"
                if manual_status and manual_status != "in_meeting":
                    logger.info(f"Meeting starting - clearing manual override '{manual_status}'")
                    config["CURRENT_STATUS"] = None
                    config["MANUAL_STATUS_TIMESTAMP"] = None
                    config["SNOOZE_UNTIL"] = None
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

    def _run_with_monitoring(self):
        """Wrapper that monitors the main loop and restarts it if it crashes."""
        while self._running:
            try:
                logger.info("Starting main status update loop")
                self._run()
                # If _run exits normally, break the monitoring loop
                break
            except Exception as e:
                logger.error(f"Main loop crashed: {e}")
                self._restart_count += 1
                
                if self._restart_count >= self._max_restarts:
                    logger.error(f"Main loop crashed {self._restart_count} times, giving up")
                    break
                
                logger.info(f"Restarting main loop (attempt {self._restart_count}/{self._max_restarts})")
                time.sleep(5)  # Wait 5 seconds before restart
        
        logger.info("Status update loop has stopped")

    def _run(self):
        first_run = True
        while self._running:
            try:
                # Always load config and environment at the top of each loop
                config = load_config()
                GOVEE_API_KEY = load_secret("GOVEE_API_KEY")
                GOVEE_DEVICE_ID = config.get("GOVEE_DEVICE_ID")
                GOVEE_DEVICE_MODEL = config.get("GOVEE_DEVICE_MODEL")
                SELECTED_CALENDAR_ID = config.get("SELECTED_CALENDAR_ID")
                STATUS_COLOR_MAP = config.get("STATUS_COLOR_MAP", {})
                REFRESH_INTERVAL = max(15, int(config.get("REFRESH_INTERVAL", 15)))  # Enforce minimum 15 seconds
                POWER_OFF_WHEN_AVAILABLE = bool(config.get("POWER_OFF_WHEN_AVAILABLE", True))
                OFF_FOR_UNKNOWN_STATUS = bool(config.get("OFF_FOR_UNKNOWN_STATUS", True))
                DISABLE_CALENDAR_SYNC = bool(config.get("DISABLE_CALENDAR_SYNC", False))
                DISABLE_LIGHT_CONTROL = bool(config.get("DISABLE_LIGHT_CONTROL", False))

                if first_run:
                    # On first run, skip minute sync and update immediately
                    self.update_now()
                    first_run = False
                else:
                    self._sync_to_minute_boundary()
                    self.update_now()
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                import traceback
            time.sleep(1)

    def _sleep_until_next_interval(self, interval_seconds):
        """Sleep until the next scheduled check time, maintaining synchronization to interval boundaries."""
        now = datetime.datetime.now()
        
        if interval_seconds == 60:
            # For 60-second intervals, sleep exactly until the next minute boundary
            seconds_into_minute = now.second + now.microsecond / 1_000_000
            sleep_time = 60 - seconds_into_minute
            logger.debug(f"60-second interval: sleeping {sleep_time:.2f}s until next minute boundary")
        elif interval_seconds == 15:
            # For 15-second intervals, sync to 15-second boundaries (0, 15, 30, 45)
            seconds_into_minute = now.second + now.microsecond / 1_000_000
            # Find the next 15-second boundary
            next_boundary = ((int(seconds_into_minute) // 15) + 1) * 15
            if next_boundary >= 60:
                next_boundary = 0
                # If we need to go to the next minute, add the remaining seconds to get there
                sleep_time = 60 - seconds_into_minute
            else:
                sleep_time = next_boundary - seconds_into_minute
            logger.debug(f"15-second interval: sleeping {sleep_time:.2f}s until next 15s boundary")
        elif interval_seconds == 30:
            # For 30-second intervals, sync to 30-second boundaries (0, 30)
            seconds_into_minute = now.second + now.microsecond / 1_000_000
            if seconds_into_minute < 30:
                sleep_time = 30 - seconds_into_minute
            else:
                sleep_time = 60 - seconds_into_minute
            logger.debug(f"30-second interval: sleeping {sleep_time:.2f}s until next 30s boundary")
        else:
            # For other intervals, just sleep the specified time (no synchronization)
            sleep_time = interval_seconds
            logger.debug(f"{interval_seconds}-second interval: sleeping {sleep_time:.2f}s (no sync)")
            
        if sleep_time > 0:
            time.sleep(sleep_time)

    def turn_off_lights_immediately(self):
        """Turn off lights immediately, bypassing the DISABLE_LIGHT_CONTROL check.
        Used when disabling light control to ensure lights turn off right away."""
        config = load_config()
        GOVEE_API_KEY = load_secret("GOVEE_API_KEY")
        GOVEE_DEVICE_ID = config.get("GOVEE_DEVICE_ID")
        GOVEE_DEVICE_MODEL = config.get("GOVEE_DEVICE_MODEL")
        
        # Guard: If Govee credentials are missing, skip light control
        if not GOVEE_API_KEY or not GOVEE_DEVICE_ID or not GOVEE_DEVICE_MODEL:
            logger.warning("Cannot turn off lights: Govee credentials not configured")
            return
        
        try:
            govee = GoveeController(GOVEE_API_KEY, GOVEE_DEVICE_ID, GOVEE_DEVICE_MODEL)
            govee.set_power("off")
            logger.info("Lights turned off immediately due to light control being disabled")
        except Exception as e:
            logger.error(f"Failed to turn off lights immediately: {e}")