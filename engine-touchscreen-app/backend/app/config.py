from pathlib import Path

APP_NAME = "Engine Touchscreen API"
APP_VERSION = "0.1.0"

# backend/app -> project root -> data/live_engine_data.db
DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "live_engine_data.db"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

ALARM_RULES = {
    "LUB OIL PRESSURE": {"warning_below": 0.2, "critical_below": 0.1},
    "H.T. WATER TEMPERATURE": {"warning_above": 95.0, "critical_above": 105.0},
    "ENGINE SPEED": {"warning_above": 900.0, "critical_above": 1000.0},
}

CORS_ORIGINS = ["*"]
