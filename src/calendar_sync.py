import os
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from logger import get_logger
from utils import normalize_status

logger = get_logger()

class CalendarSync:
    def __init__(self, calendar_id):
        self.calendar_id = calendar_id
        self.service = self._get_service()

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

    def get_current_status(self):
        """Return the current status based on the next event."""
        if not self.service:
            logger.error("Google Calendar service not initialized.")
            return "offline"
        now = datetime.datetime.utcnow().isoformat() + "Z"
        try:
            events_result = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=now,
                    maxResults=1,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])
            if not events:
                return "available"
            event = events[0]
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))
            now_dt = datetime.datetime.now(datetime.timezone.utc)
            start_dt = datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
            end_dt = datetime.datetime.fromisoformat(end.replace("Z", "+00:00"))
            if start_dt <= now_dt <= end_dt:
                return normalize_status(event.get("summary", ""))
            else:
                return "available"
        except Exception as e:
            logger.error(f"Failed to fetch calendar events: {e}")