const stationListEl = document.getElementById("station-list");
const alertFeedEl = document.getElementById("alert-feed");
const cityGridEl = document.getElementById("city-grid");
const pollutantGridEl = document.getElementById("pollutant-grid");
const openAlertCountEl = document.getElementById("open-alert-count");
const criticalAlertCopyEl = document.getElementById("critical-alert-copy");
const stationCountEl = document.getElementById("station-count");
const cityCountEl = document.getElementById("city-count");
const averageAqiEl = document.getElementById("average-aqi");
const worstStationEl = document.getElementById("worst-station");
const subscriberCountEl = document.getElementById("subscriber-count");
const lastUpdatedEl = document.getElementById("last-updated");
const refreshStateEl = document.getElementById("refresh-state");
const refreshBtn = document.getElementById("refresh-btn");
const spotlightTitleEl = document.getElementById("spotlight-title");
const spotlightBadgeEl = document.getElementById("spotlight-badge");
const spotlightAqiEl = document.getElementById("spotlight-aqi");
const spotlightPm25El = document.getElementById("spotlight-pm25");
const spotlightPm10El = document.getElementById("spotlight-pm10");
const spotlightAlertsEl = document.getElementById("spotlight-alerts");
const spotlightLocationEl = document.getElementById("spotlight-location");
const spotlightReadingTimeEl = document.getElementById("spotlight-reading-time");
const spotlightSummaryEl = document.getElementById("spotlight-summary");

let selectedStationId = null;
let trendChart = null;
let map = null;
let markers = [];
let isRefreshing = false;

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function severityClass(severity) {
  return `alert-sev-${String(severity || "low").toLowerCase()}`;
}

function severityBadgeClass(severity) {
  return `badge-${String(severity || "neutral").toLowerCase()}`;
}

function formatValue(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "N/A";
  }

  return Number(value).toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function formatDateTime(value) {
  if (!value) {
    return "Unavailable";
  }

  return new Date(value).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatNumberWithOptionalDecimal(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "N/A";
  }

  const digits = Number(value) % 1 === 0 ? 0 : 1;
  return formatValue(value, digits);
}

function buildStationCard(station) {
  const el = document.createElement("button");
  el.type = "button";
  el.className = `station-card ${station.station_id === selectedStationId ? "active" : ""}`;
  el.innerHTML = `
    <div class="station-row">
      <h3>${escapeHtml(station.station_name)}</h3>
      <span class="pill ${station.open_alert_count ? severityBadgeClass(station.dominant_severity) : "badge-good"}">
        ${station.open_alert_count ? `${station.open_alert_count} alert${station.open_alert_count === 1 ? "" : "s"}` : "stable"}
      </span>
    </div>
    <p class="station-meta">${escapeHtml(station.city)}</p>
    <div class="station-aqi">AQI ${formatNumberWithOptionalDecimal(station.latest_aqi)} | ${escapeHtml(station.latest_category || "Unknown")}</div>
    <div class="station-aqi">PM2.5 ${formatValue(station.latest_pm25, 1)} | PM10 ${formatValue(station.latest_pm10, 1)}</div>
    <div class="station-footer">Updated ${formatDateTime(station.latest_reading_at)}</div>
  `;
  el.addEventListener("click", async () => {
    selectedStationId = station.station_id;
    await renderDashboard({ preserveSelection: true });
  });
  return el;
}

function ensureMap() {
  if (map) {
    return;
  }

  map = L.map("map", { zoomControl: false }).setView([20.5937, 78.9629], 4);
  L.control.zoom({ position: "bottomright" }).addTo(map);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);
}

function renderMap(stations) {
  ensureMap();
  markers.forEach((marker) => map.removeLayer(marker));
  markers = [];

  stations.forEach((station) => {
    const marker = L.circleMarker([station.latitude, station.longitude], {
      radius: station.station_id === selectedStationId ? 10 : 8,
      weight: 2,
      color: station.open_alert_count ? "#ffb84d" : "#8dd3ff",
      fillColor: station.open_alert_count ? "#ff6a6a" : "#4cc9f0",
      fillOpacity: 0.82,
    }).addTo(map);

    marker.bindPopup(
      `<strong>${escapeHtml(station.station_name)}</strong><br/>AQI: ${formatNumberWithOptionalDecimal(station.latest_aqi)}<br/>${escapeHtml(station.city)}<br/>Alerts: ${station.open_alert_count}`
    );

    marker.on("click", async () => {
      selectedStationId = station.station_id;
      await renderDashboard({ preserveSelection: true });
    });

    markers.push(marker);
  });

  if (stations.length > 0) {
    const group = L.featureGroup(markers);
    map.fitBounds(group.getBounds().pad(0.22));
  }
}

function renderOverview(overview) {
  openAlertCountEl.textContent = formatNumberWithOptionalDecimal(overview.open_alerts);
  criticalAlertCopyEl.textContent = `${formatNumberWithOptionalDecimal(overview.critical_alerts)} critical incidents`;
  stationCountEl.textContent = formatNumberWithOptionalDecimal(overview.total_stations);
  cityCountEl.textContent = `${formatNumberWithOptionalDecimal(overview.city_count)} cities monitored`;
  averageAqiEl.textContent = formatNumberWithOptionalDecimal(overview.average_aqi);
  worstStationEl.textContent = overview.worst_station_name
    ? `${escapeHtml(overview.worst_station_name)} peaking at AQI ${formatNumberWithOptionalDecimal(overview.max_aqi)}`
    : "Worst station unavailable";
  subscriberCountEl.textContent = formatNumberWithOptionalDecimal(overview.total_subscribers);
  lastUpdatedEl.textContent = `Last sync ${formatDateTime(overview.last_updated)}`;
}

function renderSelectedStation(station) {
  if (!station) {
    spotlightTitleEl.textContent = "Awaiting station";
    spotlightBadgeEl.className = "badge badge-neutral";
    spotlightBadgeEl.textContent = "No data";
    spotlightAqiEl.textContent = "N/A";
    spotlightPm25El.textContent = "N/A";
    spotlightPm10El.textContent = "N/A";
    spotlightAlertsEl.textContent = "0";
    spotlightLocationEl.textContent = "Location unavailable";
    spotlightReadingTimeEl.textContent = "Latest reading unavailable";
    spotlightSummaryEl.textContent = "Select a station to inspect its recent particulate trend and local alert posture.";
    return;
  }

  spotlightTitleEl.textContent = station.station_name;
  spotlightBadgeEl.className = `badge ${station.open_alert_count ? severityBadgeClass(station.dominant_severity) : "badge-good"}`;
  spotlightBadgeEl.textContent = station.open_alert_count
    ? `${station.dominant_severity || "active"} alert posture`
    : "stable operation";
  spotlightAqiEl.textContent = formatNumberWithOptionalDecimal(station.latest_aqi);
  spotlightPm25El.textContent = formatValue(station.latest_pm25, 1);
  spotlightPm10El.textContent = formatValue(station.latest_pm10, 1);
  spotlightAlertsEl.textContent = formatNumberWithOptionalDecimal(station.open_alert_count);
  spotlightLocationEl.textContent = `${station.city} | ${station.latitude.toFixed(2)}, ${station.longitude.toFixed(2)}`;
  spotlightReadingTimeEl.textContent = `Latest reading ${formatDateTime(station.latest_reading_at)}`;
  spotlightSummaryEl.textContent = station.open_alert_count
    ? `${station.station_name} currently has ${station.open_alert_count} open alert${station.open_alert_count === 1 ? "" : "s"} and should be prioritized for operator review.`
    : `${station.station_name} is currently stable with no open alerts and recent particulate telemetry available.`;
}

function renderAlerts(alerts, stationsById) {
  alertFeedEl.innerHTML = "";
  if (!alerts.length) {
    alertFeedEl.innerHTML = "<div class='empty-state'>No open alerts. The network is currently stable.</div>";
    return;
  }

  alerts.forEach((alert) => {
    const station = stationsById.get(alert.station_id);
    const el = document.createElement("article");
    el.className = `alert-item ${severityClass(alert.severity)}`;
    el.innerHTML = `
      <div class="alert-row">
        <strong>${escapeHtml(station?.station_name || `Station ${alert.station_id}`)}</strong>
        <span class="pill ${severityBadgeClass(alert.severity)}">${escapeHtml(alert.severity)}</span>
      </div>
      <p>${escapeHtml(alert.pollutant)} | ${escapeHtml(station?.city || "Unknown city")}</p>
      <p>${escapeHtml(alert.message)}</p>
      <p>Opened ${formatDateTime(alert.started_at)}</p>
    `;
    alertFeedEl.appendChild(el);
  });
}

function renderCityInsights(cities) {
  cityGridEl.innerHTML = "";
  if (!cities.length) {
    cityGridEl.innerHTML = "<div class='empty-state'>City analytics will appear after the first station reports data.</div>";
    return;
  }

  cities.forEach((city) => {
    const el = document.createElement("article");
    el.className = "city-card";
    el.innerHTML = `
      <div class="city-row">
        <strong>${escapeHtml(city.city)}</strong>
        <span class="pill ${city.open_alerts ? "badge-high" : "badge-good"}">${city.open_alerts} open</span>
      </div>
      <p>${city.station_count} station${city.station_count === 1 ? "" : "s"}</p>
      <p>Average AQI ${formatNumberWithOptionalDecimal(city.average_aqi)}</p>
    `;
    cityGridEl.appendChild(el);
  });
}

function renderPollutantSnapshot(items) {
  pollutantGridEl.innerHTML = "";
  if (!items.length) {
    pollutantGridEl.innerHTML = "<div class='empty-state'>Pollutant snapshot unavailable.</div>";
    return;
  }

  items.forEach((item) => {
    const el = document.createElement("article");
    el.className = "pollutant-card";
    el.innerHTML = `
      <div class="pollutant-row">
        <strong>${escapeHtml(item.label)}</strong>
        <span class="pill badge-neutral">network</span>
      </div>
      <p>Average ${formatValue(item.average_value, 1)} ug/m3</p>
      <p>Peak ${formatValue(item.peak_value, 1)} ug/m3</p>
    `;
    pollutantGridEl.appendChild(el);
  });
}

async function renderTrend(stationId) {
  if (!stationId) {
    return;
  }

  const response = await fetch(`/stations/${stationId}/readings/recent?limit=40`);
  if (!response.ok) {
    throw new Error(`Trend request failed with status ${response.status}`);
  }

  const readings = await response.json();
  const ordered = [...readings].reverse();

  const labels = ordered.map((reading) => new Date(reading.timestamp).toLocaleTimeString());
  const pm25 = ordered.map((reading) => (reading.pollutant === "PM2.5" ? reading.value : null));
  const pm10 = ordered.map((reading) => (reading.pollutant === "PM10" ? reading.value : null));

  const ctx = document.getElementById("trend-chart");
  if (trendChart) {
    trendChart.destroy();
  }

  trendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "PM2.5",
          data: pm25,
          borderColor: "#ffb84d",
          backgroundColor: "rgba(255, 184, 77, 0.18)",
          borderWidth: 2,
          pointRadius: 2,
          fill: false,
          tension: 0.3,
          spanGaps: true,
        },
        {
          label: "PM10",
          data: pm10,
          borderColor: "#5fd0ff",
          backgroundColor: "rgba(95, 208, 255, 0.18)",
          borderWidth: 2,
          pointRadius: 2,
          fill: false,
          tension: 0.3,
          spanGaps: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: "#eff8ff", usePointStyle: true } },
      },
      scales: {
        x: { ticks: { color: "#b2cfdf", maxTicksLimit: 8 }, grid: { color: "rgba(255,255,255,0.06)" } },
        y: { ticks: { color: "#b2cfdf" }, grid: { color: "rgba(255,255,255,0.06)" } },
      },
    },
  });
}

async function renderDashboard(options = {}) {
  if (isRefreshing) {
    return;
  }

  isRefreshing = true;
  refreshStateEl.textContent = "Refreshing live data";

  try {
    const response = await fetch("/dashboard/summary");
    if (!response.ok) {
      throw new Error(`Dashboard summary request failed with status ${response.status}`);
    }

    const summary = await response.json();
    const stations = Array.isArray(summary.stations) ? summary.stations : [];
    const stationsById = new Map(stations.map((station) => [station.station_id, station]));

    if (!options.preserveSelection || !stationsById.has(selectedStationId)) {
      selectedStationId = stations[0]?.station_id ?? null;
    }

    renderOverview(summary.overview);

    stationListEl.innerHTML = "";
    if (!stations.length) {
      stationListEl.innerHTML = "<div class='empty-state'>No stations available. Create a station to activate the dashboard.</div>";
    } else {
      stations.forEach((station) => {
        stationListEl.appendChild(buildStationCard(station));
      });
    }

    renderSelectedStation(stationsById.get(selectedStationId));
    renderMap(stations);
    renderAlerts(summary.active_alerts || [], stationsById);
    renderCityInsights(summary.cities || []);
    renderPollutantSnapshot(summary.pollutant_snapshot || []);
    await renderTrend(selectedStationId);
    refreshStateEl.textContent = "Live data stream";
  } catch (error) {
    refreshStateEl.textContent = "Dashboard refresh failed";
    console.error(error);
  } finally {
    isRefreshing = false;
  }
}

refreshBtn.addEventListener("click", () => renderDashboard({ preserveSelection: true }));

renderDashboard();
setInterval(() => renderDashboard({ preserveSelection: true }), 15000);
