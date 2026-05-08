/* Plain JS GitHub Pages dashboard (no deps). */

const KNOWN_DEVICES = [
  "sim_gateway_001",
  "sim_gateway_network_flaky",
  "sim_infotainment_001",
  "sim_infotainment_screen_failure",
  "sim_sensor_hub_degraded",
  "sim_vehicle_001",
  "sim_vehicle_low_battery",
  "sim_vehicle_unstable_ota",
];

const RUNTIME_BASE = "runtime_state/simulated_devices";

function $(id) {
  return document.getElementById(id);
}

function isObject(v) {
  return v !== null && typeof v === "object" && !Array.isArray(v);
}

function deepGet(obj, paths) {
  for (const p of paths) {
    const parts = p.split(".");
    let cur = obj;
    let ok = true;
    for (const part of parts) {
      if (!cur || typeof cur !== "object" || !(part in cur)) {
        ok = false;
        break;
      }
      cur = cur[part];
    }
    if (ok) return cur;
  }
  return undefined;
}

function normalizeString(v) {
  if (v === undefined || v === null) return "";
  return String(v).trim();
}

function toLower(v) {
  return normalizeString(v).toLowerCase();
}

function safeJsonStringify(v) {
  try {
    return JSON.stringify(v, null, 2);
  } catch {
    return String(v);
  }
}

function parseDateMaybe(v) {
  if (!v) return null;
  if (typeof v === "number") {
    const d = new Date(v);
    return Number.isNaN(d.getTime()) ? null : d;
  }
  if (typeof v === "string") {
    const d = new Date(v);
    return Number.isNaN(d.getTime()) ? null : d;
  }
  return null;
}

function formatDateShort(d) {
  if (!d) return "—";
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(d);
}

function badgeClass(kind) {
  if (kind === "good") return "badge badge--good";
  if (kind === "warn") return "badge badge--warn";
  if (kind === "bad") return "badge badge--bad";
  if (kind === "info") return "badge badge--info";
  return "badge badge--muted";
}

function classifyHealth(healthStr) {
  const s = toLower(healthStr);
  if (!s) return { label: "unknown", kind: "muted" };
  if (["healthy", "ok", "pass", "passed", "good", "green"].includes(s)) {
    return { label: healthStr, kind: "good" };
  }
  if (["degraded", "warning", "warn", "flaky", "unstable"].includes(s)) {
    return { label: healthStr, kind: "warn" };
  }
  if (["failed", "fail", "error", "critical", "down", "offline"].includes(s)) {
    return { label: healthStr, kind: "bad" };
  }
  if (["testing", "running", "in_progress"].includes(s)) {
    return { label: healthStr, kind: "warn" };
  }
  return { label: healthStr, kind: "muted" };
}

function classifyPower(powerStr) {
  const s = toLower(powerStr);
  if (!s) return { label: "unknown", kind: "muted" };
  if (["on", "powered_on", "power_on", "true", "1"].includes(s)) {
    return { label: powerStr, kind: "good" };
  }
  if (["off", "powered_off", "power_off", "false", "0"].includes(s)) {
    return { label: powerStr, kind: "bad" };
  }
  return { label: powerStr, kind: "muted" };
}

function classifyStatus(statusStr) {
  const s = toLower(statusStr);
  if (!s) return { label: "unknown", kind: "muted" };
  if (["available", "online", "ready", "active", "running"].includes(s)) {
    return { label: statusStr, kind: "good" };
  }
  if (["testing", "provisioning", "updating", "restarting"].includes(s)) {
    return { label: statusStr, kind: "warn" };
  }
  if (["unavailable", "offline", "error", "failed"].includes(s)) {
    return { label: statusStr, kind: "bad" };
  }
  return { label: statusStr, kind: "muted" };
}

function classifyTestResult(resultStr) {
  const s = toLower(resultStr);
  if (!s) return { label: "—", kind: "muted" };
  if (["pass", "passed", "ok", "success", "successful"].includes(s)) {
    return { label: resultStr, kind: "good" };
  }
  if (["warn", "warning", "flaky", "skipped"].includes(s)) {
    return { label: resultStr, kind: "warn" };
  }
  if (["fail", "failed", "error"].includes(s)) {
    return { label: resultStr, kind: "bad" };
  }
  return { label: resultStr, kind: "muted" };
}

function classifyOta(otaStr) {
  const s = toLower(otaStr);
  if (!s) return { label: "—", kind: "muted" };
  if (["idle", "none", "up_to_date", "uptodate", "complete", "completed"].includes(s)) {
    return { label: otaStr, kind: "good" };
  }
  if (["downloading", "installing", "applying", "in_progress", "pending", "queued"].includes(s)) {
    return { label: otaStr, kind: "warn" };
  }
  if (["failed", "error", "rollback", "stuck"].includes(s)) {
    return { label: otaStr, kind: "bad" };
  }
  return { label: otaStr, kind: "muted" };
}

async function fetchJsonOrNull(path) {
  try {
    const res = await fetch(path, { cache: "no-store" });
    if (!res.ok) return null;
    const data = await res.json();
    return data;
  } catch {
    return null;
  }
}

function deriveFields({ deviceName, twin, state }) {
  const merged = {
    device: deviceName,
    twin: twin || null,
    state: state || null,
    available: Boolean(twin || state),
  };

  const deviceId =
    normalizeString(
      deepGet(twin, ["device_id", "deviceId", "device.id", "identity.device_id", "identity.id"])
    ) ||
    normalizeString(
      deepGet(state, ["device_id", "deviceId", "device.id", "identity.device_id", "identity.id"])
    ) ||
    deviceName;

  const simulator =
    normalizeString(deepGet(twin, ["simulator", "simulator_name", "metadata.simulator"])) ||
    normalizeString(deepGet(state, ["simulator", "simulator_name", "metadata.simulator"])) ||
    deviceName;

  const deviceType =
    normalizeString(deepGet(twin, ["device_type", "deviceType", "type", "metadata.device_type"])) ||
    normalizeString(deepGet(state, ["device_type", "deviceType", "type", "metadata.device_type"])) ||
    (deviceName.includes("vehicle")
      ? "vehicle"
      : deviceName.includes("gateway")
        ? "gateway"
        : deviceName.includes("infotainment")
          ? "infotainment"
          : deviceName.includes("sensor")
            ? "sensor_hub"
            : "simulated");

  const status =
    normalizeString(
      deepGet(state, ["status", "runtime.status", "connection.status", "device.status"])
    ) ||
    (merged.available ? "available" : "unavailable");

  const health =
    normalizeString(
      deepGet(state, ["health", "runtime.health", "device.health", "summary.health", "status.health"])
    ) ||
    normalizeString(deepGet(twin, ["health", "desired.health", "reported.health"])) ||
    (merged.available ? "unknown" : "unavailable");

  const powerRaw =
    deepGet(state, ["power", "power.state", "runtime.power", "device.power", "reported.power"]) ??
    deepGet(twin, ["power", "desired.power", "reported.power"]);
  const power =
    typeof powerRaw === "boolean"
      ? powerRaw
        ? "on"
        : "off"
      : normalizeString(powerRaw) || (merged.available ? "unknown" : "unavailable");

  const otaStatus =
    normalizeString(
      deepGet(state, [
        "ota_status",
        "ota.status",
        "runtime.ota.status",
        "ota.state",
        "updates.ota.status",
      ])
    ) ||
    normalizeString(deepGet(twin, ["ota_status", "ota.status", "desired.ota.status", "reported.ota.status"])) ||
    "";

  const lastTestResult =
    normalizeString(
      deepGet(state, [
        "last_test_result",
        "tests.last_result",
        "test.last_result",
        "runtime.tests.last_result",
        "runtime.test.last_result",
      ])
    ) ||
    normalizeString(deepGet(twin, ["last_test_result", "tests.last_result", "test.last_result"])) ||
    "";

  const updatedAt =
    parseDateMaybe(
      deepGet(state, [
        "last_updated",
        "lastUpdated",
        "updated_at",
        "updatedAt",
        "runtime.updated_at",
        "metadata.updated_at",
        "timestamp",
      ])
    ) ||
    parseDateMaybe(
      deepGet(twin, ["last_updated", "updated_at", "updatedAt", "metadata.updated_at", "timestamp"])
    ) ||
    null;

  return {
    ...merged,
    deviceId,
    simulator,
    deviceType,
    status,
    health,
    power,
    otaStatus,
    lastTestResult,
    updatedAt,
  };
}

function renderBadge(text, classifierFn) {
  const cls = classifierFn(text);
  const span = document.createElement("span");
  span.className = badgeClass(cls.kind);
  span.textContent = cls.label || "—";
  return span;
}

function clearChildren(el) {
  while (el.firstChild) el.removeChild(el.firstChild);
}

function computeSummary(devices) {
  const total = devices.length;
  let healthy = 0;
  let attention = 0;
  let testing = 0;
  let poweredOn = 0;

  for (const d of devices) {
    const health = toLower(d.health);
    const status = toLower(d.status);
    const power = toLower(d.power);

    if (["healthy", "ok", "good", "pass", "passed"].includes(health)) healthy += 1;
    if (
      ["failed", "fail", "error", "critical", "offline", "unavailable"].includes(health) ||
      ["failed", "error", "offline", "unavailable"].includes(status)
    ) {
      attention += 1;
    }
    if (["testing", "running", "in_progress"].includes(health) || status === "testing") testing += 1;
    if (["on", "powered_on", "true", "1"].includes(power)) poweredOn += 1;
  }

  return { total, healthy, attention, testing, poweredOn };
}

function renderDetails(device) {
  const detailBody = $("detailBody");
  const detailHint = $("detailHint");
  clearChildren(detailBody);

  if (!device) {
    detailHint.textContent = "Select a device row to view details.";
    const empty = document.createElement("div");
    empty.className = "detail__empty muted";
    empty.textContent = "No device selected.";
    detailBody.appendChild(empty);
    return;
  }

  detailHint.textContent = device.available ? "Merged twin/state view." : "JSON not found (unavailable).";

  const kv = document.createElement("div");
  kv.className = "kv";

  const rows = [
    ["Device ID", device.deviceId],
    ["Simulator", device.simulator],
    ["Device Type", device.deviceType],
    ["Status", device.status],
    ["Health", device.health],
    ["Power", device.power],
    ["OTA Status", device.otaStatus || "—"],
    ["Last Test Result", device.lastTestResult || "—"],
    ["Last Updated", device.updatedAt ? formatDateShort(device.updatedAt) : "—"],
    ["Twin path", `${RUNTIME_BASE}/${device.device}/twin.json`],
    ["State path", `${RUNTIME_BASE}/${device.device}/state.json`],
  ];

  for (const [k, v] of rows) {
    const row = document.createElement("div");
    row.className = "kv__row";

    const key = document.createElement("div");
    key.className = "kv__key";
    key.textContent = k;

    const val = document.createElement("div");
    val.className = "kv__value";
    val.textContent = normalizeString(v) || "—";

    row.appendChild(key);
    row.appendChild(val);
    kv.appendChild(row);
  }

  const rawTitle = document.createElement("h3");
  rawTitle.className = "detail__sectionTitle";
  rawTitle.textContent = "Raw JSON";

  const raw = document.createElement("div");
  raw.className = "jsonBlock";
  const pre = document.createElement("pre");
  pre.textContent = safeJsonStringify({
    device: device.device,
    deviceId: device.deviceId,
    simulator: device.simulator,
    derived: {
      status: device.status,
      health: device.health,
      power: device.power,
      otaStatus: device.otaStatus,
      lastTestResult: device.lastTestResult,
      updatedAt: device.updatedAt ? device.updatedAt.toISOString() : null,
      available: device.available,
    },
    twin: device.twin,
    state: device.state,
  });
  raw.appendChild(pre);

  detailBody.appendChild(kv);
  detailBody.appendChild(rawTitle);
  detailBody.appendChild(raw);
}

function renderFleet(devices) {
  const tbody = $("fleetTbody");
  clearChildren(tbody);

  if (!devices.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 9;
    td.className = "muted";
    td.textContent = "No devices.";
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }

  for (const d of devices) {
    const tr = document.createElement("tr");
    tr.dataset.device = d.device;

    const tdSimulator = document.createElement("td");
    tdSimulator.textContent = d.simulator;

    const tdId = document.createElement("td");
    tdId.textContent = d.deviceId;

    const tdType = document.createElement("td");
    tdType.textContent = d.deviceType;

    const tdStatus = document.createElement("td");
    tdStatus.appendChild(renderBadge(d.status, classifyStatus));

    const tdHealth = document.createElement("td");
    tdHealth.appendChild(renderBadge(d.health, classifyHealth));

    const tdPower = document.createElement("td");
    tdPower.appendChild(renderBadge(d.power, classifyPower));

    const tdOta = document.createElement("td");
    tdOta.appendChild(renderBadge(d.otaStatus || "—", classifyOta));

    const tdTest = document.createElement("td");
    tdTest.appendChild(renderBadge(d.lastTestResult || "—", classifyTestResult));

    const tdUpdated = document.createElement("td");
    tdUpdated.textContent = d.updatedAt ? formatDateShort(d.updatedAt) : "—";

    tr.appendChild(tdSimulator);
    tr.appendChild(tdId);
    tr.appendChild(tdType);
    tr.appendChild(tdStatus);
    tr.appendChild(tdHealth);
    tr.appendChild(tdPower);
    tr.appendChild(tdOta);
    tr.appendChild(tdTest);
    tr.appendChild(tdUpdated);

    tbody.appendChild(tr);
  }
}

function attachRowHandlers(devices) {
  const tbody = $("fleetTbody");
  let selected = null;

  const selectDevice = (deviceName) => {
    selected = deviceName;
    for (const tr of tbody.querySelectorAll("tr")) {
      tr.classList.toggle("is-selected", tr.dataset.device === selected);
    }
    const device = devices.find((d) => d.device === selected) || null;
    renderDetails(device);
  };

  tbody.onclick = (ev) => {
    const tr = ev.target && ev.target.closest ? ev.target.closest("tr") : null;
    if (!tr || !tr.dataset.device) return;
    selectDevice(tr.dataset.device);
  };

  tbody.onkeydown = (ev) => {
    if (ev.key !== "Enter" && ev.key !== " ") return;
    const tr = ev.target && ev.target.closest ? ev.target.closest("tr") : null;
    if (!tr || !tr.dataset.device) return;
    ev.preventDefault();
    selectDevice(tr.dataset.device);
  };

  for (const tr of tbody.querySelectorAll("tr")) {
    tr.tabIndex = 0;
  }

  return { selectDevice };
}

async function loadAllDevices() {
  $("loadHint").textContent = "Loading…";
  renderDetails(null);

  const loadStarted = new Date();
  $("lastLoaded").textContent = formatDateShort(loadStarted);

  const deviceNames = [...KNOWN_DEVICES].sort((a, b) => a.localeCompare(b));

  const results = await Promise.all(
    deviceNames.map(async (deviceName) => {
      const twinPath = `${RUNTIME_BASE}/${deviceName}/twin.json`;
      const statePath = `${RUNTIME_BASE}/${deviceName}/state.json`;
      const [twin, state] = await Promise.all([fetchJsonOrNull(twinPath), fetchJsonOrNull(statePath)]);
      return deriveFields({ deviceName, twin, state });
    })
  );

  results.sort((a, b) => a.deviceId.localeCompare(b.deviceId));
  renderFleet(results);

  const summary = computeSummary(results);
  $("cardTotal").textContent = String(summary.total);
  $("cardHealthy").textContent = String(summary.healthy);
  $("cardAttention").textContent = String(summary.attention);
  $("cardTesting").textContent = String(summary.testing);
  $("cardPoweredOn").textContent = String(summary.poweredOn);

  const unavailable = results.filter((d) => !d.available).length;
  $("loadHint").textContent =
    unavailable > 0 ? `Loaded (${unavailable} unavailable)` : "Loaded";

  const { selectDevice } = attachRowHandlers(results);
  const firstAvailable = results.find((d) => d.available) || results[0];
  if (firstAvailable) selectDevice(firstAvailable.device);
}

function boot() {
  const refreshBtn = $("refreshBtn");
  refreshBtn.onclick = async () => {
    refreshBtn.disabled = true;
    refreshBtn.textContent = "Refreshing…";
    try {
      await loadAllDevices();
    } finally {
      refreshBtn.disabled = false;
      refreshBtn.textContent = "Refresh";
    }
  };

  loadAllDevices().catch(() => {
    $("loadHint").textContent = "Failed to load (see console).";
  });
}

document.addEventListener("DOMContentLoaded", boot);
