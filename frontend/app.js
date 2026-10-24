/* Driver / operator UI. All backend calls go through api(); all visible text goes through t().
   API contract: docs/design/backend-outline.md §3 (the backend wins if this file differs). */
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const api = async (path, method = "GET", body) => {
  const r = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json", ...(token && { Authorization: "Bearer " + token }) },
    body: body ? JSON.stringify(body) : undefined,
  });
  const j = await r.json().catch(() => ({}));
  if (r.status === 401 && token && !path.startsWith("/api/operator")) setSession(null); // session gone (logout, dev reset)
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
  renderPicked();
  loadOp(); refreshHw();
}

// ---------- state
let token = localStorage.getItem("token"), me = null;
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
  if (name === "res") renderPicked();
  if (name === "map" && lastDetail) showDetail(...lastDetail); // fresh slot list after booking or cancelling
  window.scrollTo({ top: 0 });
}
window.showTab = showTab;

// ---------- map + GoingElectric
// The browser fetches GoingElectric directly with the key from /api/config (terms: device fetches, no backend copy).
// No key: sample stations. Our test bay is not in GoingElectric, so its pin always comes from the sample [GAP C8 Q4].
const GE = "https://api.goingelectric.de/chargepoints/";
const GE_MIN_ZOOM = 12; // ponytail: no server clustering; below this zoom the box can exceed 500 stations
const pinIcon = () => L.divIcon({
  className: "",
  html: `<div style="width:34px;height:34px;border-radius:50%;background:#C8E847;border:3px solid #0F1419;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px;box-shadow:0 0 0 6px rgba(200,232,71,.4)">⚡</div>`,
  iconSize: [34, 34], iconAnchor: [17, 17],
});
// Our bays link to a station by geId; until the bays carry one, the sample's reservable station holds them [GAP C8 Q4]
const isOurs = (s) => bays.some((b) => b.geId === s.ge_id) || (s.reservable && !bays.some((b) => b.geId != null));

function addPin(layer, s) {
  const ours = isOurs(s);
  const maxp = Math.max(0, ...s.chargepoints.map((p) => p.power));
  const m = ours
    ? L.marker([s.coordinates.lat, s.coordinates.lng], { icon: pinIcon(), zIndexOffset: 1000 })
    : L.circleMarker([s.coordinates.lat, s.coordinates.lng], { radius: 8, color: "#F5F4F1", weight: 2, fillColor: maxp >= 50 ? "#0F1419" : "#5A1DF0", fillOpacity: 1 });
  m.addTo(layer).on("click", () => showDetail(s, ours));
}

/** All stations in the box; follows `startkey` pages (max 500 per page). */
async function geBox(key, b) {
  const params = new URLSearchParams({ key, sw_lat: b.getSouth(), sw_lng: b.getWest(), ne_lat: b.getNorth(), ne_lng: b.getEast() });
  const out = [];
  for (let page = 0; page < 4; page++) { // ponytail: 2000-station cap so a bad box cannot hammer the API
    const j = await (await fetch(GE + "?" + params)).json();
    if (j.status !== "ok") throw new Error(j.status);
    out.push(...j.chargelocations);
    if (j.startkey == null) break;
    params.set("startkey", j.startkey);
  }
  return out;
}

async function initMap() {
  const [sample, cfg] = await Promise.all([
    fetch("/static/sample_chargepoints.json").then((r) => r.json()),
    api("/api/config").catch(() => ({})),
  ]);
  const locs = sample.chargelocations;
  station = locs.find(isOurs) || locs[0];
  map = L.map("map", { zoomControl: false }).setView([station.coordinates.lat, station.coordinates.lng], 14);
  L.control.zoom({ position: "topright" }).addTo(map);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OpenStreetMap contributors", maxZoom: 19 }).addTo(map);
  const key = cfg.goingelectricKey;
  if (!key) {
    $("#sample").textContent = t("map.sample");
    locs.forEach((s) => addPin(map, s));
    return;
  }
  locs.filter((s) => s.reservable).forEach((s) => addPin(map, s));
  const live = L.layerGroup().addTo(map);
  let seq = 0, timer;
  const load = async () => {
    const my = ++seq;
    if (map.getZoom() < GE_MIN_ZOOM) { live.clearLayers(); $("#sample").textContent = t("map.zoomIn"); return; }
    try {
      const found = await geBox(key, map.getBounds());
      if (my !== seq) return; // a newer move already started
      live.clearLayers();
      found.forEach((s) => addPin(live, s));
      $("#sample").textContent = "";
    } catch { if (my === seq) $("#sample").textContent = t("map.liveError"); }
  };
  map.on("moveend", () => { clearTimeout(timer); timer = setTimeout(load, 400); }); // debounce: terms ask not to load the API unnecessarily
  load();
}

const BAY_STATUS = { free: ["bay.free", "free"], reserved: ["bay.reserved", "warn"], occupied: ["bay.occupied", "warn"], unverified: ["bay.unverified", "warn"], out_of_service: ["bay.outOfService", "warn"] };

async function showDetail(s, ours) {
  lastDetail = [s, ours];
  $("#map-hint").classList.add("hidden");
  const d = $("#detail");
  d.classList.remove("hidden");
  const plugs = s.chargepoints.map((p) => `<span class="chip">${esc(p.count)}× ${esc(p.type)} · ${esc(p.power)} kW</span>`).join("");
  const fault = s.fault_report ? `<span class="chip bad">${t("detail.fault")}</span>` : `<span class="chip v">${t("detail.noFault")}</span>`;
  let bay = `<p class="legalnote">${t("detail.notReservable")}</p>`;
  if (ours) {
    bays = await api("/api/bays");
    await Promise.all(bays.map(async (b) => { bookSlots[b.id] = await api(`/api/bays/${b.id}/slots`).catch(() => []); }));
    const still = picked && bookSlots[picked.bayId]?.find((x) => x.available && x.start === picked.slot.start);
    picked = still ? { bayId: picked.bayId, slot: still } : null;
    bay = `<div id="baycards"></div><p class="legalnote">${t("slots.note")}</p>`;
  }
  d.innerHTML = `<span class="eyebrow">${esc(s.network || t("detail.defaultNetwork"))}</span>
    <h3 style="margin-top:8px">${esc(s.name)}</h3>
    <div class="muted" style="margin-top:6px">${esc(s.address.street)}, ${esc(s.address.postcode)} ${esc(s.address.city)}</div>
    <div class="chips">${plugs}${fault}</div>${bay}
    <p class="legalnote">${t("detail.stationData")} <a href="https:${esc(s.url)}" target="_blank" rel="noopener">GoingElectric.de ↗</a></p>`;
  if (ours) renderBays();
}

// ---------- time slots per bay: start/end + fee come from the backend (GET /api/bays/:id/slots); start null = now
let bookSlots = {}, picked = null; // picked = { bayId, slot }
const money = (cents) => new Intl.NumberFormat(lang, { style: "currency", currency: "EUR" }).format(cents / 100);
const hhmm = (iso) => new Date(iso).toLocaleTimeString(lang, { hour: "2-digit", minute: "2-digit" });
const span = (start, end) => `${start ? hhmm(start) : t("slots.now")} – ${hhmm(end)}`; // one format everywhere: 05:30 – 06:00

function bayCard(b) {
  // unknown camera health or a broken bay is said out loud, never hidden behind "free" slots
  const warn = ["out_of_service", "unverified"].includes(b.status) ? ` <span class="chip bad">${t(BAY_STATUS[b.status][0])}</span>` : "";
  const low = Math.min(...bookSlots[b.id].map((x) => x.feeCents));
  const list = b.status === "out_of_service" ? "" : `<div class="slotlist" data-bay="${esc(b.id)}">${bookSlots[b.id].map((x, i) => {
    const on = picked?.bayId === b.id && picked.slot === x;
    return `<button class="srow ${on ? "on" : ""} ${x.feeCents > low ? "peak" : ""}" ${x.available ? "" : "disabled"} onclick="pickSlot('${esc(b.id)}', ${i})">
      <span class="tm">${span(x.start, x.end)}</span><span class="st">${t(x.available ? "slots.free" : "slots.booked")}</span><span class="fee">${money(x.feeCents)}</span></button>`;
  }).join("")}</div>`;
  const mine = picked?.bayId === b.id;
  return `<div class="bayrow"><div class="l">${t("detail.live")} · ${esc(b.name)}${warn}</div>${list}
    <div class="pick"><div class="price">${mine ? money(picked.slot.feeCents) : "–"}<small>${mine ? span(picked.slot.start, picked.slot.end) : t("slots.pickOne")}</small></div>
    <button class="btn btn-primary" ${mine ? "" : "disabled"} onclick="showTab('res')">${t("detail.reserveBtn")}</button></div></div>`;
}
function renderBays() {
  const el = $("#baycards");
  if (!el) return;
  const keep = Object.fromEntries([...el.querySelectorAll(".slotlist")].map((l) => [l.dataset.bay, l.scrollTop]));
  el.innerHTML = bays.map(bayCard).join("");
  el.querySelectorAll(".slotlist").forEach((l) => (l.scrollTop = keep[l.dataset.bay] || 0));
}
window.pickSlot = (bayId, i) => { picked = { bayId, slot: bookSlots[bayId][i] }; renderBays(); };
function renderPicked() {
  $("#picked").innerHTML = picked
    ? `<div class="k">${esc(bayName(picked.bayId))}</div><div class="tm">${span(picked.slot.start, picked.slot.end)}</div><div class="price">${money(picked.slot.feeCents)}</div>`
    : `<p class="muted">${t("slots.pickOnMap")}</p><button class="btn" onclick="showTab('map')">${t("nav.map")}</button>`;
  $("#btn-reserve").disabled = !picked;
}

// ---------- session (email + password; token in localStorage)
function setSession(tok, driver = null) {
  token = tok; me = driver;
  tok ? localStorage.setItem("token", tok) : localStorage.removeItem("token");
  $("#login-card").classList.toggle("hidden", !!me);
  $("#reserve-card").classList.toggle("hidden", !me);
  if (me) $("#who").textContent = `${me.name} · ${me.plate}`;
}
$("#login-card").onsubmit = async (e) => {
  e.preventDefault();
  $("#login-err").textContent = "";
  try {
    const r = await api("/api/login", "POST", { email: $("#f-email").value, password: $("#f-pass").value });
    $("#f-pass").value = "";
    setSession(r.token, r.driver);
    resumeRes();
  } catch (err) { $("#login-err").textContent = tErr(err.message); }
};
$("#btn-logout").onclick = async () => {
  await api("/api/logout", "POST").catch(() => {});
  setSession(null);
  window.newRes();
};

// ---------- reservation

$("#btn-reserve").onclick = async () => {
  $("#res-err").textContent = "";
  try {
    const plate = $("#f-plate").value.trim() || undefined; // empty = driver's profile plate
    const r = await api("/api/reservations", "POST", { bayId: picked.bayId, plate, slotStart: picked.slot.start });
    resId = r.id;
    picked = null;
    pollRes();
  } catch (e) { $("#res-err").textContent = t("err.prefix") + tErr(e.message); }
};

// Visual class per state (text comes from i18n: state.<STATE>.title / .sub)
const STATE_CLS = { SCHEDULED: "ok", RESERVED: "ok", PLATE_MISMATCH: "warn", BLOCKED: "bad", UNVERIFIED: "warn", ARRIVED: "ok", CHARGING: "ok", COMPLETED: "ok", NO_SHOW: "bad", FAILED: "bad", FAULT_REPORTED: "warn" };
const STEPS = ["reserved", "arrived", "charging", "done"];
const STEP_OF = { SCHEDULED: 0, REQUESTED: 0, RESERVED: 0, PLATE_MISMATCH: 0, BLOCKED: 0, UNVERIFIED: 0, ARRIVED: 1, CHARGING: 2, COMPLETED: 3 };
const fmt = (s) => {
  s = Math.max(0, Math.round(s));
  const p = (n) => String(n).padStart(2, "0");
  return s >= 3600 ? `${Math.floor(s / 3600)}:${p(Math.floor(s / 60) % 60)}:${p(s % 60)}` : `${Math.floor(s / 60)}:${p(s % 60)}`;
};

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
  if (token && !me) { try { setSession(token, await api("/api/me")); } catch { setSession(null); } }
  if (!token) { setSession(null); resId = null; return pollRes(); }
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
window.newRes = () => { resId = null; pollRes(); renderPicked(); };

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
  if (r.state === "SCHEDULED") {
    big = `<div class="big">${fmt(secs(r.slotStart) - secs(r.serverTime))}</div><div class="k">${t("timer.untilSlot")}</div>`;
  } else if (r.state === "RESERVED" && r.graceDeadline) {
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
    <div class="meta"><div><div class="k">${t("meta.bay")}</div><div class="v">${esc(bayName(r.bayId))}</div></div><div><div class="k">${t("meta.plate")}</div><div class="v">${esc(r.plate)}</div></div>
      <div><div class="k">${t("meta.slot")}</div><div class="v">${r.graceDeadline ? span(r.slotStart, r.graceDeadline) : t("slots.now")}</div></div><div><div class="k">${t("meta.fee")}</div><div class="v">${r.feeCents == null ? "–" : money(r.feeCents)}</div></div></div>
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
