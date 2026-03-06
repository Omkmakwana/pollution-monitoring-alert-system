const stationListEl = document.getElementById("station-list");
const alertFeedEl = document.getElementById("alert-feed");
const openAlertCountEl = document.getElementById("open-alert-count");
const refreshBtn = document.getElementById("refresh-btn");

let selectedStationId = null;
let trendChart = null;
let map = null;
let markers = [];

function severityClass(severity) {
  return `alert-sev-${String(severity || "low").toLowerCase()}`;
}

function buildStationCard(station) {
  const el = document.createElement("button");
  el.type = "button";
  el.className = `station-card ${station.station_id === selectedStationId ? "active" : ""}`;
  el.innerHTML = `
    <h3>${station.station_name}</h3>
    <p class="station-meta">${station.city}</p>
    <div class="station-aqi">AQI: ${station.latest_aqi ?? "N/A"} | ${station.latest_category ?? "Unknown"}</div>
    <div class="station-aqi">PM2.5: ${station.latest_pm25 ?? "N/A"}  PM10: ${station.latest_pm10 ?? "N/A"}</div>
  `;
  el.addEventListener("click", async () => {
    selectedStationId = station.station_id;
    await renderDashboard();
  });
  return el;
}

function ensureMap() {
  if (map) return;
  map = L.map("map").setView([20.5937, 78.9629], 4);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);
}

function renderMap(stations) {
  ensureMap();
  markers.forEach((m) => map.removeLayer(m));
  markers = [];

  stations.forEach((s) => {
    const marker = L.marker([s.latitude, s.longitude]).addTo(map);
    marker.bindPopup(`<strong>${s.station_name}</strong><br/>AQI: ${s.latest_aqi ?? "N/A"}<br/>${s.city}`);
    markers.push(marker);
  });

  if (stations.length > 0) {
    const group = L.featureGroup(markers);
    map.fitBounds(group.getBounds().pad(0.25));
  }
}

function renderAlerts(alerts) {
  alertFeedEl.innerHTML = "";
  if (!alerts.length) {
    alertFeedEl.innerHTML = "<div class='alert-item'><p>No open alerts</p></div>";
    return;
  }

  alerts.forEach((alert) => {
    const el = document.createElement("article");
    el.className = `alert-item ${severityClass(alert.severity)}`;
    el.innerHTML = `
      <p><strong>Station ${alert.station_id}</strong> | ${alert.pollutant}</p>
      <p>Severity: ${alert.severity}</p>
      <p>${alert.message}</p>
    `;
    alertFeedEl.appendChild(el);
  });
}

async function renderTrend(stationId) {
  if (!stationId) return;
  const response = await fetch(`/stations/${stationId}/readings/recent?limit=40`);
  const readings = await response.json();
  const ordered = [...readings].reverse();

  const labels = ordered.map((r) => new Date(r.timestamp).toLocaleTimeString());
  const pm25 = ordered.map((r) => (r.pollutant === "PM2.5" ? r.value : null));
  const pm10 = ordered.map((r) => (r.pollutant === "PM10" ? r.value : null));

  const ctx = document.getElementById("trend-chart");
  if (trendChart) trendChart.destroy();

  trendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        { label: "PM2.5", data: pm25, borderColor: "#ffb703", tension: 0.25, spanGaps: true },
        { label: "PM10", data: pm10, borderColor: "#8ecae6", tension: 0.25, spanGaps: true },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: "#eff8ff" } },
      },
      scales: {
        x: { ticks: { color: "#b2cfdf", maxTicksLimit: 8 }, grid: { color: "rgba(255,255,255,0.08)" } },
        y: { ticks: { color: "#b2cfdf" }, grid: { color: "rgba(255,255,255,0.08)" } },
      },
    },
  });
}

async function renderDashboard() {
  const response = await fetch("/dashboard/summary");
  const summary = await response.json();

  openAlertCountEl.textContent = summary.open_alerts;

  stationListEl.innerHTML = "";
  summary.stations.forEach((station) => {
    if (selectedStationId === null) selectedStationId = station.station_id;
    stationListEl.appendChild(buildStationCard(station));
  });

  renderMap(summary.stations);
  renderAlerts(summary.active_alerts);
  await renderTrend(selectedStationId);
}

refreshBtn.addEventListener("click", renderDashboard);

renderDashboard();
setInterval(renderDashboard, 15000);
