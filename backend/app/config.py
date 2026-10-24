import os

ADAPTER = os.environ.get("ADAPTER", "mock")
ECURIOUS_BASE_URL = os.environ.get("ECURIOUS_BASE_URL", "https://parking-lock-service-production.up.railway.app")
ECURIOUS_API_KEY = os.environ.get("ECURIOUS_API_KEY", "")
LOCK_IDS = os.environ.get("LOCK_IDS", "lock-0002,lock-0003").split(",")
DB_PATH = os.environ.get("DB_PATH", "data.db")
GRACE_MINUTES = float(os.environ.get("GRACE_MINUTES", "15"))
CAMERA_STALE_SECONDS = int(os.environ.get("CAMERA_STALE_SECONDS", "120"))
POLL_SECONDS = float(os.environ.get("POLL_SECONDS", "5"))
OPERATOR_TOKEN = os.environ.get("OPERATOR_TOKEN", "")  # empty = operator routes open (local only); set it on any deploy
