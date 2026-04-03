# 🚀 Backend API (FastAPI + SQLite)

This backend serves generator monitoring data from SQLite and exposes JSON APIs for the dashboard.

## ✨ Features
- ⚡ FastAPI-based REST API
- 🗄️ SQLite data source (`data/live_engine_data.db`)
- 🧠 Service-layer structure (`live`, `trends`, `alarms`, `system`)
- 🌐 CORS enabled for frontend access
- 📘 Auto API docs via Swagger

## 📁 Structure
- `app/main.py` → FastAPI app entrypoint
- `app/config.py` → app config, DB path, alarm rules
- `app/db.py` → SQLAlchemy engine/session dependency
- `app/models.py` → ORM model (`live_engine_data`)
- `app/schemas.py` → Pydantic response schemas
- `app/services/` → business logic
- `app/api/` → API routers
- `run.py` → local startup script
- `requirements.txt` → Python dependencies

## 🗄️ Database
Configured in `app/config.py`:
- `DB_PATH = project_root/data/live_engine_data.db`

Expected main table:
- `live_engine_data`

Main fields used by API:
- `imo`, `serial`, `addr`, `label`, `timestamp`, `val`, `unit`

## 🔌 API Endpoints

### Live
- `GET /api/live/all`
- `GET /api/live/{addr}`
- `GET /api/live/group/{group_name}`
- `GET /api/live/timestamp`
- `GET /api/live/lable_value`
- `GET /api/live/analog_lable_value`

### Trends
- `GET /api/trends/{addr}?hours=1`
- `GET /api/trends/{addr}?from=...&to=...`

### Alarms
- `GET /api/alarms/active`
- `GET /api/alarms/history`

### System
- `GET /api/system/health`
- `GET /api/system/status`

## ▶️ Run Backend

```bash
cd backend
pip install -r requirements.txt
python run.py
```

Alternative:

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📘 API Docs
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## 🛠️ Quick Test

PowerShell:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/live/analog_lable_value" -Method Get | ConvertTo-Json -Depth 5
```

Browser:
- `http://localhost:8000/api/live/analog_lable_value`

## 🧪 Notes About Current Implementation
- `analog_lable_value` returns only rows with `unit != "On/Off"`.
- `lable_value` keeps current naming to match your existing usage.
- `alarms/history` currently returns the same result as active alarms (placeholder behavior).

## ⚠️ Troubleshooting

1. `Address not found` on `/api/live/timestamp`
- Ensure static routes are defined before dynamic `/{addr}` route (already handled in current code).

2. Empty results (`[]`)
- Collector may not be running or DB has no recent data.
- Verify collector writes to `data/live_engine_data.db`.

3. CORS/frontend fetch issue
- Check backend is running on expected host/port.
- Confirm frontend API base URL matches backend.

4. Import/module errors
- Run commands from inside `backend` folder.
- Ensure dependencies from `requirements.txt` are installed.

## 📌 Recommended Next Improvements
- Add `id INTEGER PRIMARY KEY AUTOINCREMENT` for easier maintenance.
- Add dedicated alarm history storage.
- Add authentication if exposing API beyond local network.
