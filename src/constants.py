import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.abspath(os.path.join(BASE_DIR, "../config/google_token.pickle"))
CLIENT_SECRET_PATH = os.path.abspath(os.path.join(BASE_DIR, "../resources/client_secret.json"))
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]