# 🚀 Generator Analog Dashboard (Static Frontend)

A lightweight, static frontend (HTML/CSS/JS) for monitoring generator analog values from your backend API.

## ✨ Highlights
- ⚡ No build tool required (no Vite/NPM needed to run)
- 🔄 Auto-refresh every 5 seconds
- 🟢 Connection status: Connected / Disconnected
- 🕒 Last updated timestamp
- 📊 Clean card view for `label` + `value`

## 📁 Project Files
- `index.html`
- `timestamp.html`
- `config.js`
- `index.js`
- `timestamp.js`
- `app.css`

## 🔌 Backend API Used
- `GET /api/live/analog_lable_value`
- `GET /api/live/timestamp`
- Default backend base URL: `http://localhost:8000`

If your backend runs on a different host/port, update `config.js` only:

```js
window.APP_CONFIG = {
  apiBaseUrl: "http://localhost:8000",
  refreshMs: 5000,
  paths: {
    analog: "/api/live/analog_lable_value",
    timestamp: "/api/live/timestamp",
  },
};
```

## ▶️ How To Run

### Option 1: Open directly
Open `index.html` in your browser.

### Option 2: Run with Python static server (recommended)
```bash
cd frontend
python3 -m http.server 5170
```
Then open:
- `http://localhost:5170/`
- or `http://localhost:5170/index.html`

## ❗ Important Note
Use `index.html` (NOT `index.htm`).
Using `index.htm` will return `404 File not found`.

## 🛠️ Quick Troubleshooting

1. Check frontend files are served
- In the static server terminal, you should see:
  - `GET /index.html`
  - `GET /config.js`
  - `GET /index.js`
  - `GET /app.css`

2. Check backend API directly in browser
- Open: `http://localhost:8000/api/live/analog_lable_value`

3. Check browser console
- Press `F12` → `Console`
- Look for fetch/CORS/network errors

## 🌐 WSL Note
If you run `python3 -m http.server` inside WSL, open the frontend from Windows browser using:
- `http://localhost:5170`
- or `http://127.0.0.1:5170`

## 📌 Dashboard Behavior
- Refreshes data every 5 seconds
- Shows backend connection state
- Shows latest refresh time
- Renders all analog metrics as cards
