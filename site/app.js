// Singing Materials: pick a material, element, temperature and sound; play it with Strudel;
// draw the DOS and fitted peaks; show the Strudel code and a strudel.cc link.
// Data comes from scripts/build_site_data.py (site/data/).
"use strict";

const $ = (id) => document.getElementById(id);
const SVG = "http://www.w3.org/2000/svg";

const state = {
  index: [],       // site/data/index.json
  methods: [],     // site/data/methods.json
  data: null,      // site/data/materials/<mp_id>.json for the chosen material
  mpId: null,
  element: null,
  temp: "athermal",
  chosen: ["chord"], // sonification methods to play together, in methods.json order
  playing: false,
};
const loaded = new Map(); // mp_id -> material data
let strudelReady = null;  // promise from initStrudel()
let audioReady = null;    // promise from strudel.initAudio()

const tempName = (t) => (t === "athermal" ? "none" : t.replace("K", " K"));
const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

async function getJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: ${r.status}`);
  return r.json();
}

// ---- the code: MP2Strudel's data block + the method from sonify.js + the line that plays it ----

// "all" plays and draws the total DOS, fitted on its own (by_temp[t].total, label "total")
const ALL = "all";
const isAll = () => state.element === ALL;
const current = () => (isAll() ? state.data.by_temp[state.temp].total : state.data.by_temp[state.temp]);
const currentLabel = () => (isAll() ? "total" : state.element);

function currentCode() {
  const chosen = state.methods.filter((m) => state.chosen.includes(m.name));
  if (!chosen.length) return `${current().strudel}\n\n// choose a sound above\n`;
  // each method's code is its helpers and itself, as blocks separated by blank lines; methods share
  // helpers (e.g. ringTime), and a const can only be declared once, so keep each block once
  const blocks = [...new Set(chosen.flatMap((m) => m.code.split("\n\n")))];
  const plays = chosen.map((m) => m.play.replace("{x}", currentLabel()));
  const play = plays.length === 1
    ? plays[0]
    : `stack(\n  ${plays.join(",\n  ")},\n).postgain(${(1 / Math.sqrt(plays.length)).toFixed(2)})  // turned down, as the sounds add up`;
  const names = chosen.map((m) => m.name).join(" + ");
  return `${current().strudel}\n\n// sound: ${names} (from MP2Strudel's sonify.js)\n${blocks.join("\n\n")}\n\n${play}\n`;
}

function strudelLink(code) {
  // strudel.cc reads encodeURIComponent(base64(UTF-8 code)) from the hash, as MP2Strudel's strudel_url
  const bytes = new TextEncoder().encode(code);
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return "https://strudel.cc/#" + encodeURIComponent(btoa(bin));
}

// ---- sound ----

function initStrudelOnce() {
  if (!strudelReady) {
    if (typeof window.initStrudel !== "function") return Promise.reject(new Error("Strudel did not load"));
    strudelReady = window.initStrudel();
  }
  return strudelReady;
}

async function play() {
  if (!state.chosen.length) return stop();
  const status = $("status");
  try {
    // resume audio inside the click (Strudel only unlocks audio on mousedown, so keyboard users need this)
    if (window.strudel) window.strudel.getAudioContext().resume();
    status.textContent = strudelReady ? "" : "Loading sounds…";
    await initStrudelOnce();
    audioReady ??= window.strudel.initAudio();
    await audioReady;
    await window.strudel.evaluate(currentCode());
    state.playing = true;
    status.textContent = "";
  } catch (e) {
    console.error(e);
    status.textContent = "Sorry, the sound couldn't start. Try the strudel.cc link below.";
    state.playing = false;
  }
  updatePlayButton();
}

function stop() {
  try {
    window.strudel.hush(); // stops new notes; notes already playing would ring on (a slow chord for seconds)
    window.strudel.getSuperdoughAudioController().reset(); // so cut them: Strudel rebuilds its output on the next Play
  } catch (e) { console.error(e); }
  state.playing = false;
  updatePlayButton();
}

function updatePlayButton() {
  $("play").textContent = state.playing ? "Stop" : "Play";
  $("play").disabled = !state.playing && !state.chosen.length;
}

// ---- chart: DOS curve with each fitted peak as a pale Gaussian; hover or tab to a peak for its values ----

function niceStep(range, target) {
  const raw = range / target;
  const p = 10 ** Math.floor(Math.log10(raw));
  return [1, 2, 2.5, 5, 10].map((m) => m * p).find((s) => s >= raw);
}

function fmt(v) {
  if (v === 0) return "0";
  if (Math.abs(v) >= 100) return v.toFixed(0);
  if (Math.abs(v) >= 1) return v.toPrecision(3).replace(/\.?0+$/, "");
  return v.toPrecision(2);
}

function el(name, attrs = {}, parent) {
  const e = document.createElementNS(SVG, name);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (parent) parent.appendChild(e);
  return e;
}

function drawChart() {
  const wrap = $("chart");
  wrap.replaceChildren();
  const { x_THz } = current().chart;
  const lab = current().chart.labels[currentLabel()];
  const thermal = state.temp !== "athermal";
  const yName = thermal ? "occupied DOS" : "DOS";
  const whose = isAll() ? "all elements" : state.element;

  const W = 800, H = 340, L = 64, R = 16, T = 12, B = 48;
  const step = x_THz.length > 1 ? x_THz[1] - x_THz[0] : 1;
  const xMax = x_THz[x_THz.length - 1] + step / 2;
  const yTop = Math.max(...lab.dos, ...lab.peaks.map((p) => p.dos)) * 1.08 || 1;
  const sx = (f) => L + (f / xMax) * (W - L - R);
  const sy = (d) => H - B - (d / yTop) * (H - T - B);

  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "group", "aria-label": `${yName} of ${whose} against frequency, with fitted peaks` });

  // axes and ticks
  el("line", { class: "axis", x1: L, y1: H - B, x2: W - R, y2: H - B }, svg);
  el("line", { class: "axis", x1: L, y1: T, x2: L, y2: H - B }, svg);
  const xs = niceStep(xMax, 8);
  for (let v = 0; v <= xMax + 1e-9; v += xs) {
    el("line", { class: "axis", x1: sx(v), y1: H - B, x2: sx(v), y2: H - B + 5 }, svg);
    el("text", { x: sx(v), y: H - B + 20, "text-anchor": "middle" }, svg).textContent = fmt(v);
  }
  const ys = niceStep(yTop, 5);
  for (let v = 0; v <= yTop + 1e-12; v += ys) {
    el("line", { class: "axis", x1: L - 5, y1: sy(v), x2: L, y2: sy(v) }, svg);
    el("text", { x: L - 9, y: sy(v) + 4, "text-anchor": "end" }, svg).textContent = fmt(v);
  }
  el("text", { x: (L + W - R) / 2, y: H - 6, "text-anchor": "middle" }, svg).textContent = "frequency (THz)";
  el("text", { x: 14, y: (T + H - B) / 2, "text-anchor": "middle", transform: `rotate(-90 14 ${(T + H - B) / 2})` }, svg)
    .textContent = `${yName} (states/THz)`;

  // peaks: broad ones first so narrow ones sit on top and stay reachable
  const order = lab.peaks.map((p, i) => i).sort((a, b) => lab.peaks[b].fwhm_THz - lab.peaks[a].fwhm_THz);
  const drop = el("line", { class: "drop", visibility: "hidden" });
  const tip = document.createElement("div");
  tip.className = "tooltip";
  tip.hidden = true;

  const peakEls = [];
  for (const i of order) {
    const p = lab.peaks[i];
    const lo = Math.max(0, p.freq_THz - 1.6 * p.fwhm_THz), hi = Math.min(xMax, p.freq_THz + 1.6 * p.fwhm_THz);
    let d = `M${sx(lo).toFixed(1)},${sy(0).toFixed(1)}`;
    for (let k = 0; k <= 60; k++) {
      const f = lo + ((hi - lo) * k) / 60;
      const g = p.dos * Math.exp((-4 * Math.LN2 * (f - p.freq_THz) ** 2) / p.fwhm_THz ** 2);
      d += `L${sx(f).toFixed(1)},${sy(g).toFixed(1)}`;
    }
    d += `L${sx(hi).toFixed(1)},${sy(0).toFixed(1)}Z`;
    const n = i + 1;
    const text = `Peak ${n} · ${fmt(p.freq_THz)} THz · ${yName} ${fmt(p.dos)} states/THz · width (FWHM) ${fmt(p.fwhm_THz)} THz · sounds at ${fmt(p.audible_Hz)} Hz`;
    const path = el("path", { class: "peak", d, tabindex: 0, role: "img", "aria-label": text }, svg);
    peakEls[i] = path;

    const show = () => {
      path.classList.add("on");
      drop.setAttribute("x1", sx(p.freq_THz)); drop.setAttribute("x2", sx(p.freq_THz));
      drop.setAttribute("y1", sy(p.dos)); drop.setAttribute("y2", sy(0));
      drop.setAttribute("visibility", "visible");
      tip.innerHTML = `Peak ${n} · ${esc(fmt(p.freq_THz))} THz<br>${yName} ${esc(fmt(p.dos))} states/THz<br>width (FWHM) ${esc(fmt(p.fwhm_THz))} THz<br>sounds at ${esc(fmt(p.audible_Hz))} Hz`;
      const xf = sx(p.freq_THz) / W; // keep the box inside the chart near its edges
      tip.style.left = `${xf * 100}%`;
      tip.style.transform = `translate(${xf < 0.25 ? -10 : xf > 0.75 ? -90 : -50}%, calc(-100% - 10px))`;
      tip.style.top = `${(sy(p.dos) / H) * 100}%`;
      tip.hidden = false;
    };
    const hide = () => {
      path.classList.remove("on");
      drop.setAttribute("visibility", "hidden");
      tip.hidden = true;
    };
    path.addEventListener("mouseenter", show);
    path.addEventListener("mouseleave", hide);
    path.addEventListener("focus", show);
    path.addEventListener("blur", hide);
  }

  // the DOS curve on top of the pale peaks, not catching the mouse
  let c = "";
  x_THz.forEach((f, k) => { c += `${k ? "L" : "M"}${sx(f).toFixed(1)},${sy(lab.dos[k]).toFixed(1)}`; });
  el("path", { class: "curve", d: c, "pointer-events": "none" }, svg);
  svg.appendChild(drop);

  wrap.append(svg, tip);
}

// ---- page ----

function update() {
  if (!state.data) return;
  const code = currentCode();
  $("code").textContent = code;
  $("strudel-link").href = strudelLink(code);
  drawChart();
  $("method-desc").replaceChildren(...state.methods.filter((m) => state.chosen.includes(m.name)).map((m) => {
    const line = document.createElement("span");
    line.textContent = state.chosen.length > 1 ? `${m.name}: ${m.describe}` : m.describe;
    return line;
  }));
  if (!state.chosen.length) $("method-desc").textContent = "Choose at least one sound.";
  const params = new URLSearchParams({ m: state.mpId, e: state.element, t: state.temp, s: state.chosen.join(",") });
  history.replaceState(null, "", `?${params}`);
  if (state.playing) play();
  updatePlayButton();
}

function fillSelect(select, values, names, chosen) {
  select.replaceChildren(...values.map((v, i) => new Option(names[i], v, false, v === chosen)));
}

async function selectMaterial(mpId, prefer = {}) {
  const m = state.index.find((x) => x.mp_id === mpId);
  if (!m) return;
  state.mpId = mpId;
  $("material").value = mpId;
  $("description").textContent = m.description;
  $("mp-link").href = `https://next-gen.materialsproject.org/materials/${encodeURIComponent(mpId)}`;
  if (!loaded.has(mpId)) loaded.set(mpId, await getJSON(`data/materials/${mpId}.json`));
  if (state.mpId !== mpId) return; // another material was chosen while this one loaded
  state.data = loaded.get(mpId);

  // "all" (the total DOS) first, for materials with more than one element; one-element materials
  // would only repeat the same spectrum. Files built before "all" existed have no total.
  const labels = state.data.labels;
  const hasTotal = labels.length > 1 && Object.values(state.data.by_temp).every((t) => t.total);
  const options = hasTotal ? [ALL, ...labels] : labels;
  state.element = [prefer.element, state.element].find((e) => options.includes(e)) ?? options[0];
  fillSelect($("element"), options, options.map((e) => (e === ALL ? "all (total DOS)" : e)), state.element);

  const temps = state.data.temps;
  state.temp = [prefer.temp, state.temp].find((t) => temps.includes(t)) ?? temps[0];
  fillSelect($("temp"), temps, temps.map(tempName), state.temp);
  update();
}

function buildMaterialSelect() {
  const select = $("material");
  const groups = new Map();
  for (const m of state.index) {
    if (!groups.has(m.group)) {
      const g = document.createElement("optgroup");
      g.label = m.group;
      groups.set(m.group, g);
    }
    groups.get(m.group).append(new Option(`${m.name} (${m.formula})`, m.mp_id));
  }
  select.replaceChildren(...groups.values());
  select.disabled = false;
}

function buildMethods() {
  // one checkbox per method; ticked ones play together
  const box = $("methods");
  const boxes = state.methods.map((m) => {
    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = m.name;
    input.checked = state.chosen.includes(m.name);
    const label = document.createElement("label");
    label.append(input, m.name);
    return label;
  });
  box.replaceChildren(...boxes);
  box.addEventListener("change", () => {
    state.chosen = [...box.querySelectorAll("input:checked")].map((i) => i.value);
    update();
  });
}

async function main() {
  try {
    [state.index, state.methods] = await Promise.all([getJSON("data/index.json"), getJSON("data/methods.json")]);
  } catch (e) {
    console.error(e);
    $("status").textContent = "Sorry, the materials couldn't be loaded.";
    return;
  }
  const q = new URLSearchParams(location.search);
  if (q.has("s")) state.chosen = q.get("s").split(",").filter((s) => state.methods.some((m) => m.name === s));
  buildMaterialSelect();
  buildMethods();

  $("material").addEventListener("change", (e) => selectMaterial(e.target.value));
  $("element").addEventListener("change", (e) => { state.element = e.target.value; update(); });
  $("temp").addEventListener("change", (e) => { state.temp = e.target.value; update(); });
  $("play").addEventListener("click", () => (state.playing ? stop() : play()));

  const first = state.index.some((x) => x.mp_id === q.get("m")) ? q.get("m") : state.index[0].mp_id;
  await selectMaterial(first, { element: q.get("e"), temp: q.get("t") });
  updatePlayButton();
  initStrudelOnce().catch((e) => {
    console.error(e);
    $("status").textContent = "The sound library didn't load, but the strudel.cc link below still works.";
  });
}

main();
