import os
from utils import resource_path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = resource_path('config/google_token.pickle')
CLIENT_SECRET_PATH = resource_path('resources/client_secret.json')
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]