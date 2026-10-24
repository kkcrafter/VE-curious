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
GOINGELECTRIC_API_KEY = os.environ.get("GOINGELECTRIC_API_KEY", "")  # handed to the browser; GoingElectric terms want the device to fetch [GAP C8]
# Time slots and reservation fee: placeholder numbers, labelled as assumptions [TEAM B4, B7]
SLOT_MINUTES = int(os.environ.get("SLOT_MINUTES", "30"))
SLOT_COUNT = int(os.environ.get("SLOT_COUNT", "8"))  # future slots offered after "now"
FEE_CENTS = int(os.environ.get("FEE_CENTS", "200"))  # reservation fee, separate from the kWh price (AFIR)
PEAK_HOURS = (16, 19)  # local time, start inclusive, end exclusive
PEAK_FACTOR = 1.5
TIMEZONE = os.environ.get("TIMEZONE", "Europe/Berlin")
# Mock charger: Ecurious has no charging API [GAP C3]. Placeholder numbers; the app labels the data as simulated
CHARGE_KW = float(os.environ.get("CHARGE_KW", "22"))
KWH_CENTS = int(os.environ.get("KWH_CENTS", "59"))  # charge point operator's price, shown apart from the reservation fee (AFIR)
BATTERY_KWH = 60
START_SOC = 20  # battery percent at plug-in
CHARGE_SPEEDUP = float(os.environ.get("CHARGE_SPEEDUP", "60"))  # demo: 1 real second = 1 charging minute; full in ~2 min
