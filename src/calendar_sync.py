import os
import datetime
import dateutil.parser
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from logger import get_logger
from utils import normalize_status

# Import paths and scopes from config_ui
from constants import TOKEN_PATH, CLIENT_SECRET_PATH, SCOPES

logger = get_logger()

def ensure_aware(dt):
    """Ensure a datetime is timezone-aware (UTC if naive)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.timezone.utc)
    return dt

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
        """Authenticate and return a Google Calendar API service using OAuth."""
        creds = None
        # Load token if it exists
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, "rb") as token:
                creds = pickle.load(token)
        # If no valid creds, start OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for next run
            with open(TOKEN_PATH, "wb") as token:
                pickle.dump(creds, token)
        try:
            service = build("calendar", "v3", credentials=creds)
            return service
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Calendar: {e}")
            return None

    def get_all_calendars(self):
        """Return a list of all calendars available to the user."""
        if not self.service:
            logger.error("Google Calendar service not initialized.")
            return []
        try:
            calendars = self.service.calendarList().list().execute().get("items", [])
            logger.info(f"Fetched {len(calendars)} calendars from Google Calendar.")
            return calendars
        except Exception as e:
            logger.error(f"Failed to fetch calendar list: {e}")
            return []

    def get_current_status(self, return_next_event_time=False):
        """Return the current status based on ongoing or next event.
        If return_next_event_time is True, also return the next event's start time.
        """
        if not self.service:
            logger.error("Google Calendar service not initialized.")
            return ("offline", None) if return_next_event_time else "offline"
        now = datetime.datetime.now(datetime.timezone.utc)
        lookback_minutes = 15
        time_min = (now - datetime.timedelta(minutes=lookback_minutes)).isoformat()
        # Set timeMax to midnight tonight UTC
        tomorrow = now + datetime.timedelta(days=1)
        midnight = datetime.datetime.combine(tomorrow.date(), datetime.time.min, tzinfo=datetime.timezone.utc)
        time_max = midnight.isoformat()
        try:
            events_result = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=5,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            # After fetching events
            events = events_result.get("items", [])
            logger.info(f"Fetched {len(events)} events from Google Calendar:")

            # 1. Check for ongoing event (this takes priority)
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                end = event["end"].get("dateTime", event["end"].get("date"))
                start_dt = ensure_aware(dateutil.parser.isoparse(start))
                end_dt = ensure_aware(dateutil.parser.isoparse(end))
                logger.info(f"Checking event: {event.get('summary', '')} | Start: {start_dt} | End: {end_dt} | Now: {now}")
                if start_dt <= now <= end_dt:
                    status = normalize_status(event.get("summary", ""))
                    duration_minutes = int((end_dt - start_dt).total_seconds() // 60)
                    logger.info(f"Detected meeting: {event.get('summary', '')} | Duration: {duration_minutes} minutes")
                    if return_next_event_time:
                        return status, start_dt
                    return status
            # 2. No ongoing event, check for next event within 1 minute (start early)
            if events:
                next_event = events[0]
                start = next_event["start"].get("dateTime", next_event["start"].get("date"))
                start_dt = ensure_aware(dateutil.parser.isoparse(start))
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