/* Driver / operator UI. All backend calls go through api(); all visible text goes through t().
   API contract: docs/design/backend-outline.md §3 (the backend wins if this file differs). */
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const api = async (path, method = "GET", body) => {
  const r = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json", "X-Driver-Id": driver },
    body: body ? JSON.stringify(body) : undefined,
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error?.code || r.statusText);
  return j;
};
const secs = (iso) => Date.parse(iso) / 1000;

// ---------- i18n
const LANGS = ["en", "de"];
let lang = localStorage.getItem("lang") || ((navigator.language || "en").toLowerCase().startsWith("de") ? "de" : "en");
const dict = {};
async function loadDicts() {
  await Promise.all(LANGS.map(async (l) => { dict[l] = await (await fetch(`/static/i18n/${l}.json`)).json(); }));
}
/** t("key", {var: value}) -> translated string; falls back to English, then to the key itself. */
function t(key, vars = {}) {
  const s = dict[lang]?.[key] ?? dict.en?.[key] ?? key;
  return s.replace(/\{(\w+)\}/g, (_, k) => (vars[k] !== undefined ? vars[k] : `{${k}}`));
}
/** Translate a backend error code (e.g. "bay_taken"); unknown codes are shown as-is. */
const tErr = (code) => (dict[lang]?.["err." + code] !== undefined ? t("err." + code) : code);
function applyStatic() {
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => (el.innerHTML = t(el.dataset.i18n)));
  $("#lang").textContent = lang === "en" ? "DE" : "EN"; // shows the language you can switch TO
  document.title = lang === "de" ? "Platz reservieren" : "Reserve a bay";
}
async function switchLang() {
  lang = lang === "en" ? "de" : "en";
  localStorage.setItem("lang", lang);
  applyStatic();
  if (lastRes) renderRes(lastRes);
  if (lastDetail) showDetail(...lastDetail);
  loadOp(); refreshHw();
}

// ---------- state
// ponytail: demo drivers seeded by the backend (db.DRIVERS) until the login decision (#5)
let driver = localStorage.getItem("driver") || "d1";
let map, resId = null, bays = [], station = null, tab = "map", lastRes = null, lastDetail = null;
const bayName = (id) => bays.find((b) => b.id === id)?.name || id;

// ---------- tabs
document.querySelectorAll(".tabbar button").forEach((b) => (b.onclick = () => showTab(b.dataset.tab)));
function showTab(name) {
  tab = name;
  ["map", "res", "op"].forEach((x) => $("#tab-" + x).classList.toggle("hidden", x !== name));
  document.querySelectorAll(".tabbar button").forEach((b) => b.classList.toggle("on", b.dataset.tab === name));
  if (name === "map" && map) setTimeout(() => map.invalidateSize(), 50);
  if (name === "op") loadOp();
  window.scrollTo({ top: 0 });
}
window.showTab = showTab;

// ---------- map + GoingElectric
// ponytail: sample stations only. GoingElectric terms want the device to fetch directly with our key;
// add the live call here once the key and the visible-key question are answered [GAP C8].
const pinIcon = () => L.divIcon({
  className: "",
  html: `<div style="width:34px;height:34px;border-radius:50%;background:#C8E847;border:3px solid #0F1419;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px;box-shadow:0 0 0 6px rgba(200,232,71,.4)">⚡</div>`,
  iconSize: [34, 34], iconAnchor: [17, 17],
});

async function initMap() {
  const data = await (await fetch("/static/sample_chargepoints.json")).json();
  $("#sample").textContent = t("map.sample");
  const locs = data.chargelocations;
  // Our bays link to a station by geId; until the bays carry one, the sample's reservable station holds them [GAP C8 Q4]
  const isOurs = (s) => bays.some((b) => b.geId === s.ge_id) || (s.reservable && !bays.some((b) => b.geId != null));
  station = locs.find(isOurs) || locs[0];
  map = L.map("map", { zoomControl: false }).setView([station.coordinates.lat, station.coordinates.lng], 14);
  L.control.zoom({ position: "topright" }).addTo(map);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", { attribution: "© OpenStreetMap · © CARTO", maxZoom: 19 }).addTo(map);
  locs.forEach((s) => {
    const ours = isOurs(s);
    const maxp = Math.max(...s.chargepoints.map((p) => p.power));
    const m = ours
      ? L.marker([s.coordinates.lat, s.coordinates.lng], { icon: pinIcon(), zIndexOffset: 1000 })
      : L.circleMarker([s.coordinates.lat, s.coordinates.lng], { radius: 8, color: "#F5F4F1", weight: 2, fillColor: maxp >= 50 ? "#0F1419" : "#5A1DF0", fillOpacity: 1 });
    m.addTo(map).on("click", () => showDetail(s, ours));
  });
}

const BAY_STATUS = { free: ["bay.free", "free"], reserved: ["bay.reserved", "warn"], occupied: ["bay.occupied", "warn"], unverified: ["bay.unverified", "warn"], out_of_service: ["bay.outOfService", "warn"] };

async function showDetail(s, ours) {
  lastDetail = [s, ours];
  $("#map-hint").classList.add("hidden");
  const d = $("#detail");
  d.classList.remove("hidden");
  const plugs = s.chargepoints.map((p) => `<span class="chip">${p.count}× ${esc(p.type)} · ${p.power} kW</span>`).join("");
  const fault = s.fault_report ? `<span class="chip bad">${t("detail.fault")}</span>` : `<span class="chip v">${t("detail.noFault")}</span>`;
  let bay = `<p class="legalnote">${t("detail.notReservable")}</p>`;
  if (ours) {
    bays = await api("/api/bays");
    bay = bays.map((b) => {
      const [key, cls] = BAY_STATUS[b.status] || BAY_STATUS.unverified; // unknown status is never "free"
      return `<div class="bayrow"><div class="l">${t("detail.live")} · ${esc(b.name)}</div><div class="s ${cls}">${t(key)}</div>
        <button class="btn btn-primary btn-block" ${b.status === "free" ? "" : "disabled"} onclick="pickBay('${esc(b.id)}')">${t("detail.reserveBtn")}</button></div>`;
    }).join("");
  }
  d.innerHTML = `<span class="eyebrow">${esc(s.network || t("detail.defaultNetwork"))}</span>
    <h3 style="margin-top:8px">${esc(s.name)}</h3>
    <div class="muted" style="margin-top:6px">${esc(s.address.street)}, ${esc(s.address.postcode)} ${esc(s.address.city)}</div>
    <div class="chips">${plugs}${fault}</div>${bay}
    <p class="legalnote">${t("detail.stationData")} <a href="https:${esc(s.url)}" target="_blank" rel="noopener">GoingElectric.de ↗</a></p>`;
}
let pickedBay = null;
window.pickBay = (id) => { pickedBay = id; showTab("res"); };

// ---------- reservation
$("#f-driver").value = driver;
$("#f-driver").onchange = (e) => { driver = e.target.value; localStorage.setItem("driver", driver); resumeRes(); };

$("#btn-reserve").onclick = async () => {
  $("#res-err").textContent = "";
  try {
    const bayId = pickedBay || bays.find((b) => b.status === "free")?.id || bays[0]?.id;
    const plate = $("#f-plate").value.trim() || undefined; // empty = driver's profile plate
    const r = await api("/api/reservations", "POST", { bayId, plate });
    resId = r.id;
    pollRes();
  } catch (e) { $("#res-err").textContent = t("err.prefix") + tErr(e.message); }
};

// Visual class per state (text comes from i18n: state.<STATE>.title / .sub)
const STATE_CLS = { RESERVED: "ok", PLATE_MISMATCH: "warn", BLOCKED: "bad", UNVERIFIED: "warn", ARRIVED: "ok", CHARGING: "ok", COMPLETED: "ok", NO_SHOW: "bad", FAILED: "bad", FAULT_REPORTED: "warn" };
const STEPS = ["reserved", "arrived", "charging", "done"];
const STEP_OF = { REQUESTED: 0, RESERVED: 0, PLATE_MISMATCH: 0, BLOCKED: 0, UNVERIFIED: 0, ARRIVED: 1, CHARGING: 2, COMPLETED: 3 };
const fmt = (s) => { s = Math.max(0, Math.round(s)); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`; };

let pollT;
async function pollRes() {
  clearTimeout(pollT);
  if (!resId) { lastRes = null; renderRes(null); }
  else {
    try { lastRes = await api("/api/reservations/" + resId); renderRes(lastRes); }
    catch { lastRes = null; renderRes(null); resId = null; }
  }
  refreshHw();
  pollT = setTimeout(pollRes, 1500);
}
async function resumeRes() {
  try { resId = (await api("/api/me/reservations?active=true"))[0]?.id || null; } catch { resId = null; }
  pollRes();
}
// allowedActions (backend) -> route + body. Buttons only appear for actions the backend allows.
const ACTIONS = {
  cancel: ["cancel"],
  start_charging: ["charging", { action: "start" }],
  stop_charging: ["charging", { action: "stop" }],
  confirm_arrival: ["confirm-arrival"],
  deny_arrival: ["deny-arrival"],
  report_fault: ["fault", { reason: "no_power" }],
};
const act = (action) => {
  const [path, body] = ACTIONS[action];
  return api(`/api/reservations/${resId}/${path}`, "POST", body).then(pollRes).catch((e) => alert(tErr(e.message)));
};
window.act = act;
window.newRes = () => { resId = null; pollRes(); };

function renderRes(r) {
  $("#res-empty").classList.toggle("hidden", !!r);
  const v = $("#res-view");
  v.classList.toggle("hidden", !r);
  $("#res-dot").classList.toggle("show", !!r && ["PLATE_MISMATCH", "BLOCKED", "UNVERIFIED"].includes(r.state));
  if (!r) return;
  const cls = STATE_CLS[r.state] || "";
  const can = (a) => r.allowedActions.includes(a);
  const btn = (a, label, kind = "") => (can(a) ? `<button class="btn ${kind}" onclick="act('${a}')">${t(label)}</button>` : "");
  let big = "", btns = "";
  if (r.state === "RESERVED" && r.graceDeadline) {
    big = `<div class="big">${fmt(secs(r.graceDeadline) - secs(r.serverTime))}</div><div class="k">${t("timer.untilGrace")}</div>`;
  } else if (r.state === "CHARGING") {
    // ponytail: updatedAt = when CHARGING started, as nothing else updates the row in this state
    big = `<div class="big">${fmt(secs(r.serverTime) - secs(r.updatedAt))}</div><div class="k">${t("timer.charging")}</div>`;
  }
  if (r.state === "RESERVED") btns += `<button class="btn btn-primary" onclick="window.open('https://www.google.com/maps?q=${station.coordinates.lat},${station.coordinates.lng}')">${t("btn.navigate")}</button>`;
  btns += btn("confirm_arrival", "btn.confirmMe", "btn-primary") + btn("deny_arrival", "btn.no")
    + btn("start_charging", "btn.startCharging", "btn-primary") + btn("stop_charging", "btn.stopCharging")
    + btn("cancel", "btn.cancel", "btn-danger") + btn("report_fault", "btn.fault");
  if (["BLOCKED", "UNVERIFIED"].includes(r.state)) btns += `<button class="btn" onclick="showTab('map')">${t("btn.alternatives")}</button>`;
  if (!r.allowedActions.length && r.state !== "REQUESTED") btns = `<button class="btn btn-primary" onclick="newRes()">${t("btn.again")}</button>`;
  const idx = STEP_OF[r.state];
  const steps = idx === undefined ? "" : `<div class="steps">${STEPS.map((_, i) => `<div class="${i <= idx ? "on" : ""}"></div>`).join("")}</div>
    <div class="steplabels">${STEPS.map((s) => `<span>${t("steps." + s)}</span>`).join("")}</div>`;
  v.innerHTML = `<div class="status dark ${cls}">
    <span class="eyebrow">${esc(r.state.replace("_", " "))}</span>
    <div class="st">${t(`state.${r.state}.title`)}</div><div class="sub">${t(`state.${r.state}.sub`)}</div>
    ${big}${steps}
    <div class="meta"><div><div class="k">${t("meta.bay")}</div><div class="v">${esc(bayName(r.bayId))}</div></div><div><div class="k">${t("meta.plate")}</div><div class="v">${esc(r.plate)}</div></div></div>
    <div class="row">${btns}</div></div>`;
}

// ---------- header: bay status
async function refreshHw() {
  try {
    bays = await api("/api/bays");
    const ok = bays.length && bays.every((b) => b.status !== "unverified");
    $("#hw").classList.toggle("ok", ok);
    $("#hw-text").textContent = ok ? t("hw.online") : t("hw.bayOffline");
  } catch { $("#hw").classList.remove("ok"); $("#hw-text").textContent = t("hw.serverOffline"); }
}

// ---------- operator
async function loadOp() {
  if (tab !== "op") return;
  let events;
  try { events = await api("/api/operator/events?limit=100"); }
  catch (e) { $("#tab-op").innerHTML = `<div class="card err">${esc(tErr(e.message))}</div>`; return; }
  const rows = (a, f) => a.map(f).join("");
  $("#tab-op").innerHTML = `
  <div class="sheet"><span class="eyebrow">${t("op.eyebrow")}</span></div>
  <div class="kpis">${rows(bays, (b) => `<div class="kpi"><div class="n">${t((BAY_STATUS[b.status] || BAY_STATUS.unverified)[0])}</div><div class="k">${esc(b.name)}</div></div>`)}</div>
  <div class="card"><span class="eyebrow">${t("op.events")}</span><table>${rows(events, (e) => {
    const p = e.payload;
    return `<tr><td class="t">${esc(e.ts.slice(11, 19))}</td><td class="k">${esc(e.kind)}</td><td>${esc(p.to ? (p.frm || "") + " → " + p.to : JSON.stringify(p))}</td></tr>`;
  })}</table></div>`;
}
window.api = api; window.loadOp = loadOp;
setInterval(loadOp, 2000);

// ---------- demo panel (mock adapter only; /api/dev/* does not exist with ADAPTER=ecurious)
const devBay = () => lastRes?.bayId || bays[0]?.id;
const dev = (path, body) => api("/api/dev/" + path, "POST", body).catch((e) => alert(tErr(e.message)));
$("#d-ok").onclick = () => (lastRes ? dev("plate", { bayId: lastRes.bayId, plate: lastRes.plate }) : alert(t("dev.noRes")));
$("#d-other").onclick = () => dev("plate", { bayId: devBay(), plate: "B XY 999" });
$("#d-leave").onclick = () => dev("presence", { bayId: devBay(), occupied: false });
$("#d-reset").onclick = async () => { await dev("reset"); window.newRes(); };
$("#lang").onclick = switchLang;

// ---------- boot
(async () => {
  await loadDicts();
  applyStatic();
  $("#hw-text").textContent = t("hw.connecting");
  await refreshHw();
  await initMap();
  resumeRes();
})();
