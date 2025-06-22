import os
import datetime
import dateutil.parser
from google.oauth2 import service_account
from googleapiclient.discovery import build
from logger import get_logger
from utils import normalize_status

logger = get_logger()

class CalendarSync:
    def __init__(self, calendar_id):
        self.calendar_id = calendar_id
        self.service = self._get_service()
        self._log_calendar_email()

    def _log_calendar_email(self):
        """Log the email address or ID of the calendar being accessed."""
        if self.service:
            try:
                calendar_info = self.service.calendars().get(calendarId=self.calendar_id).execute()
                calendar_email = calendar_info.get("id", "unknown")
                calendar_summary = calendar_info.get("summary", "unknown")
                logger.info(f"Accessing Google Calendar: {calendar_summary} (ID/email: {calendar_email})")
            except Exception as e:
                logger.warning(f"Could not fetch calendar email/ID: {e}")

    def _get_service(self):
        """Authenticate and return a Google Calendar API service."""
        creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        scopes = ["https://www.googleapis.com/auth/calendar.readonly"]
        if not creds_path or not os.path.exists(creds_path):
            logger.error("Google service account JSON not found. Set GOOGLE_SERVICE_ACCOUNT_JSON in .env.")
            return None
        try:
            creds = service_account.Credentials.from_service_account_file(creds_path, scopes=scopes)
            service = build("calendar", "v3", credentials=creds)
            return service
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Calendar: {e}")
            return None

    def get_current_status(self, return_next_event_time=False):
        """Return the current status based on ongoing or next event.
        If return_next_event_time is True, also return the next event's start time.
        """
        if not self.service:
            logger.error("Google Calendar service not initialized.")
            return ("offline", None) if return_next_event_time else "offline"
        now = datetime.datetime.now(datetime.timezone.utc)
        now_iso = now.isoformat()
        try:
            # Get all events that have not ended yet (could be ongoing or upcoming)
            events_result = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=now_iso,
                    maxResults=5,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])
            # Check for ongoing event
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                end = event["end"].get("dateTime", event["end"].get("date"))
                start_dt = dateutil.parser.isoparse(start)
                end_dt = dateutil.parser.isoparse(end)
                if start_dt <= now <= end_dt:
                    status = normalize_status(event.get("summary", ""))
                    if return_next_event_time:
                        return status, start_dt
                    return status
            # No ongoing event, check for next event within 1 minute
            if events:
                next_event = events[0]
                start = next_event["start"].get("dateTime", next_event["start"].get("date"))
                start_dt = datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
                if 0 <= (start_dt - now).total_seconds() <= 60:
                    status = "in_meeting"
                    if return_next_event_time:
                        return status, start_dt
                    return status
                if return_next_event_time:
                    return "available", start_dt
            return ("available", None) if return_next_event_time else "available"
        except Exception as e:
            logger.error(f"Failed to fetch calendar events: {e}")
            return ("offline", None) if return_next_event_time else "offline"