# Engine Touchscreen Frontend 🖥️

Static frontend for the DG monitoring dashboards ⚙️

## 1. Folder Structure 📁

```text
frontend/
  Asset/
    DAIKAI_LOGO.jpg
    DRUMS_LOGO.png
    DRUMS_logo_small.png
    Engine.png
    Engine_image.png
    engine_image_mainpage.png
    Engine_Runing.gif
    Engine_Runing_1.gif
  index.html
  DGs_dashboard_V2.html
  DGs_dashboard.html.bak
  config.js
  index.js
  app.css
  README.md
```

## 2. Active Pages 🌐

- `index.html`: home page with 4 DG cards, READY/RUNNING/ALARM lights, and `FAIL CONNECTION !` warning when data is missing 🚨
- `DGs_dashboard_V2.html`: DG detail page (`?dg=1..4`) showing analog + digital + alarm data 📊

## 3. Favicon (Browser Tab Logo) 🏷️

Both pages currently use:

- `./Asset/DRUMS_logo_small.png`

## 4. API Endpoints Used by Frontend 🔌

### `index.html`
- `GET /api/live/live_digital_value`

### `DGs_dashboard_V2.html`
- `GET /api/live/analog_lable_value`
- `GET /api/live/live_digital_value`
- `GET /api/alarms/dg_status`

Default API base URL: `http://localhost:8000` 🧭

## 5. Run Frontend ▶️

Open HTML files directly, or run a static server:

```bash
cd frontend
python -m http.server 5170
```

Then open:

- `http://localhost:5170/index.html`
- `http://localhost:5170/DGs_dashboard_V2.html?dg=1`

## 6. Important Notes 📝

- `DGs_dashboard.html.bak` is a backup file, not the active page 💾
- `config.js`, `index.js`, `app.css` are legacy files and are currently not imported by `index.html` or `DGs_dashboard_V2.html` 🧩
- If favicon/logo updates do not appear immediately, use `Ctrl + F5` to hard refresh 🔄
