import pathlib
WEB_ROOT = pathlib.Path(__file__).parent.parent / "frontend"
CREDENTIALS_PATH = pathlib.Path(__file__).parent.parent / "backend" / "credentials.json"
SESSIONS_SAVED_PATH = WEB_ROOT / "sessions.json"
SESSIONS_MAX_AGE = 2592000