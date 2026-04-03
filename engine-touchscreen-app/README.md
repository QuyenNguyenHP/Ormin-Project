# Engine Touchscreen App

## 1. Project Structure

```text
engine-touchscreen-app/
??? backend/
?   ??? app/
?   ?   ??? main.py
?   ?   ??? db.py
?   ?   ??? models.py
?   ?   ??? schemas.py
?   ?   ??? config.py
?   ?   ??? services/
?   ?   ?   ??? live_service.py
?   ?   ?   ??? trend_service.py
?   ?   ?   ??? alarm_service.py
?   ?   ?   ??? system_service.py
?   ?   ??? api/
?   ?   ?   ??? live.py
?   ?   ?   ??? trends.py
?   ?   ?   ??? alarms.py
?   ?   ?   ??? system.py
?   ?   ??? utils/
?   ?       ??? time_utils.py
?   ?       ??? formatters.py
?   ??? requirements.txt
?   ??? run.py
??? frontend/
??? data/
?   ??? live_engine_data.db
??? collector/
?   ??? modbus_collector.py
?   ??? data_collector.py
??? scripts/
??? nginx/
??? README.md
```

## 2. What Was Implemented

### Backend (FastAPI + SQLAlchemy)
- Created FastAPI entry point in `backend/app/main.py`.
- Registered routers for live, trends, alarms, and system APIs.
- Enabled CORS.
- Added startup lifecycle (`lifespan`) to initialize DB metadata.

### Database Layer
- Implemented SQLAlchemy engine/session in `backend/app/db.py`.
- Added model `LiveEngineData` in `backend/app/models.py` mapped to table `live_engine_data`.
- Configured DB path in `backend/app/config.py` to use:
  - `engine-touchscreen-app/data/live_engine_data.db`

### Schemas
- Added response schemas in `backend/app/schemas.py`:
  - `LiveValueResponse`
  - `TrendPoint`, `TrendResponse`
  - `AlarmResponse`
  - `SystemHealthResponse`, `SystemStatusResponse`

### Services
- `live_service.py`: latest values (all/by addr/by group)
- `trend_service.py`: trend queries by hours or custom time range
- `alarm_service.py`: active alarm detection with severity (`warning`/`critical`) from config rules
- `system_service.py`: health/status info (last update, DB existence, disk usage, CPU temp when available)

### API Endpoints

#### Live
- `GET /api/live/all`
- `GET /api/live/{addr}`
- `GET /api/live/group/{group_name}`

#### Trends
- `GET /api/trends/{addr}?hours=1`
- `GET /api/trends/{addr}?from=...&to=...`

#### Alarms
- `GET /api/alarms/active`
- `GET /api/alarms/history`

#### System
- `GET /api/system/health`
- `GET /api/system/status`

### Collector DB Path Update
- Updated `collector/data_collector.py` line 26 to relative path:

```python
LIVE_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "live_engine_data.db"
```

This ensures collector writes to the shared DB under `data/`.

## 3. Backend Run Guide

From project root:

```bash
cd backend
pip install -r requirements.txt
python run.py
```

Or with uvicorn directly:

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API base URL:
- `http://localhost:8000`

Swagger docs:
- `http://localhost:8000/docs`

## 4. Notes
- Alarm history endpoint is currently a placeholder and returns active alarms.
- Existing table has composite primary key (`addr`, `timestamp`) in backend model.
- For future scaling, consider adding `id INTEGER PRIMARY KEY AUTOINCREMENT` in DB schema.
- Runtime verification was not executed in this environment because Python is not installed/accessible here.
