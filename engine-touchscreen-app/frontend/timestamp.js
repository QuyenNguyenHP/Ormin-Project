(function () {
  const API_BASE = window.API_BASE_URL || "http://localhost:8000";
  const API_PATH = "/api/live/timestamp";
  const POLL_MS = 5000;

  const valueEl = document.getElementById("timestampValue");
  const metaEl = document.getElementById("timestampMeta");
  const errorEl = document.getElementById("timestampError");
  const refreshBtn = document.getElementById("refreshBtn");

  function setOk(text) {
    valueEl.textContent = text || "No timestamp";
    metaEl.innerHTML = `<span class="status-good">Connected</span> | Updated ${new Date().toLocaleTimeString()}`;
    errorEl.style.display = "none";
    errorEl.textContent = "";
  }

  function setError(message) {
    metaEl.innerHTML = `<span class="status-bad">Disconnected</span> | ${new Date().toLocaleTimeString()}`;
    errorEl.style.display = "block";
    errorEl.textContent = message || "Failed to fetch timestamp";
  }

  async function loadTimestamp() {
    try {
      const res = await fetch(`${API_BASE}${API_PATH}`);
      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }
      const data = await res.json();
      setOk(data && data.timestamp ? data.timestamp : "null");
    } catch (err) {
      setError(err.message);
    }
  }

  refreshBtn.addEventListener("click", loadTimestamp);
  loadTimestamp();
  setInterval(loadTimestamp, POLL_MS);
})();
