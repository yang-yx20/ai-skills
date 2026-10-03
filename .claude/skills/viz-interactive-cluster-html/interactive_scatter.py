"""
Generic builder: one self-contained interactive HTML for an embedding scatter
(UMAP / PCA / t-SNE) with cluster labels -- the scatter counterpart of the
network pages in LRR_searching/Adrián César-Razquin et al. 2015 Cell_parody/
scripts/10_build_interactive_network.py (same conventions: inline style/script,
inline JSON data blob, no CDN, no fetch; Python fills __PLACEHOLDER__ tokens).

Features: one or more "views" (alternative layouts/clusterings, e.g. two
feature weightings) switchable in the sidebar with animated transitions;
color-by modes (the active view's clusters, any categorical column, any
numeric column on a one-hue sequential ramp); viewBox zoom/pan; hover
tooltip; gene search; click a point -> highlight it and its k nearest
neighbours (lines drawn); click a legend row -> isolate that group and list
its members (the table view); gene labels appear when zoomed in; light/dark.

Color follows the dataviz skill's reference palette. A scatter is an
"all-pairs" context, so >8 categories never get generated hues: they use
composite encoding (8 hues x marker shape), plus on-plot cluster numbers,
tooltip and isolate as secondary encoding. Values in `neutral_values`
(e.g. "unknown") are drawn as muted gray rings.

Usage (see SKILL.md):
    from interactive_scatter import build_interactive_scatter
    build_interactive_scatter("out.html", nodes, views, title="...",
                              categorical=["class"], sequential=["pubmed"])
  nodes : DataFrame indexed by point id; column "label" (display name) plus
          any attribute columns. tooltip_cols are shown on hover.
  views : dict view_key -> dict(
              label="TF-IDF (primary)",
              coords=DataFrame[x, y] indexed by id,
              cluster=Series id -> int cluster id,
              cluster_names={cid: "short name"},     # optional
              neighbors={id: [(other_id, similarity), ...]})  # optional
"""
import json
import math

import numpy as np
import pandas as pd

W, H, MARGIN = 1400.0, 1000.0, 60.0


def _scale(coords):
    x, y = coords.iloc[:, 0].astype(float), coords.iloc[:, 1].astype(float)
    x0, x1, y0, y1 = x.min(), x.max(), y.min(), y.max()
    # keep aspect ratio so distances are not distorted
    s = min((W - 2 * MARGIN) / (x1 - x0 + 1e-9), (H - 2 * MARGIN) / (y1 - y0 + 1e-9))
    ox = (W - s * (x1 - x0)) / 2
    oy = (H - s * (y1 - y0)) / 2
    return {i: [round(ox + (xi - x0) * s, 1), round(H - oy - (yi - y0) * s, 1)]
            for i, xi, yi in zip(coords.index, x, y)}


def _jsonable(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    return v


def build_interactive_scatter(out_html, nodes, views, *, title, subtitle="", categorical=(),
                              neutral_values=("unknown",), sequential=(), log_sequential=True,
                              tooltip_cols=(), notes_html="", search_placeholder="e.g. TLR4"):
    nodes = nodes.copy()
    data = {"nodes": {}, "views": {}, "modes": [], "neutral": list(neutral_values)}
    for i, r in nodes.iterrows():
        data["nodes"][str(i)] = {
            "label": str(r["label"]),
            "attrs": {c: _jsonable(r[c]) for c in list(categorical) + list(sequential)},
            "tip": [[c, _jsonable(r[c])] for c in tooltip_cols],
        }
    for key, v in views.items():
        cl = v["cluster"].astype(int)
        pos = _scale(v["coords"])
        cent = {int(c): [round(float(np.mean([pos[i][0] for i in cl.index[cl == c]])), 1),
                         round(float(np.mean([pos[i][1] for i in cl.index[cl == c]])), 1)]
                for c in sorted(cl.unique())}
        data["views"][key] = {
            "label": v["label"],
            "pos": {str(i): p for i, p in pos.items()},
            "cl": {str(i): int(c) for i, c in cl.items()},
            "names": {int(c): str(n) for c, n in (v.get("cluster_names") or {}).items()},
            "nn": {str(i): [[str(j), round(float(s), 3)] for j, s in nn]
                   for i, nn in (v.get("neighbors") or {}).items()},
            "cent": cent,
        }
    data["modes"].append({"key": "__cluster__", "label": "Cluster", "type": "cluster"})
    for c in categorical:
        vals = nodes[c].fillna(neutral_values[0] if neutral_values else "NA").astype(str)
        order = [x for x in vals.value_counts().index if x not in neutral_values] + \
                [x for x in neutral_values if x in set(vals)]
        data["modes"].append({"key": c, "label": c, "type": "categorical", "values": order})
    for c in sequential:
        v = pd.to_numeric(nodes[c], errors="coerce")
        t = np.log10(v + 1) if log_sequential else v
        data["modes"].append({"key": c, "label": (f"log10({c} + 1)" if log_sequential else c),
                              "type": "sequential", "log": bool(log_sequential),
                              "min": float(t.min()), "max": float(t.max())})

    view_buttons = "".join(
        f'<button class="seg" data-view="{k}">{v["label"]}</button>' for k, v in views.items())
    html = (_TEMPLATE
            .replace("__TITLE__", title)
            .replace("__SUBTITLE__", subtitle)
            .replace("__NOTES_HTML__", notes_html)
            .replace("__SEARCH_PLACEHOLDER__", search_placeholder)
            .replace("__VIEW_BUTTONS__", view_buttons)
            .replace("__WIDTH__", str(int(W)))
            .replace("__HEIGHT__", str(int(H)))
            .replace("__DATA_JSON__", json.dumps(data, separators=(",", ":"))))
    leftover = [t for t in ("__TITLE__", "__DATA_JSON__", "__VIEW_BUTTONS__") if t in html]
    assert not leftover, leftover
    with open(out_html, "w") as f:
        f.write(html)
    return out_html


_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root {
    color-scheme: light;
    --surface-1: #fcfcfb; --surface-2: #f3f2ef;
    --text-primary: #0b0b0b; --text-secondary: #52514e; --muted: #898781;
    --border: rgba(11,11,11,0.10); --wash: rgba(11,11,11,0.05); --active: rgba(42,120,214,0.12);
    --c1:#2a78d6; --c2:#eb6834; --c3:#1baf7a; --c4:#eda100;
    --c5:#e87ba4; --c6:#008300; --c7:#4a3aa7; --c8:#e34948; --other:#898781;
    --q1:#86b6ef; --q2:#6da7ec; --q3:#5598e7; --q4:#3987e5; --q5:#2a78d6; --q6:#1c5cab; --q7:#104281;
    --nn-line: rgba(11,11,11,0.35);
  }
  @media (prefers-color-scheme: dark) {
    :root:where(:not([data-theme="light"])) {
      color-scheme: dark;
      --surface-1: #1a1a19; --surface-2: #242423;
      --text-primary: #ffffff; --text-secondary: #c3c2b7; --muted: #8f8e88;
      --border: rgba(255,255,255,0.12); --wash: rgba(255,255,255,0.06); --active: rgba(57,135,229,0.22);
      --c1:#3987e5; --c2:#d95926; --c3:#199e70; --c4:#c98500;
      --c5:#d55181; --c6:#008300; --c7:#9085e9; --c8:#e66767; --other:#8f8e88;
      --q1:#184f95; --q2:#1c5cab; --q3:#256abf; --q4:#2a78d6; --q5:#5598e7; --q6:#86b6ef; --q7:#b7d3f6;
      --nn-line: rgba(255,255,255,0.40);
    }
  }
  :root[data-theme="dark"] {
    color-scheme: dark;
    --surface-1: #1a1a19; --surface-2: #242423;
    --text-primary: #ffffff; --text-secondary: #c3c2b7; --muted: #8f8e88;
    --border: rgba(255,255,255,0.12); --wash: rgba(255,255,255,0.06); --active: rgba(57,135,229,0.22);
    --c1:#3987e5; --c2:#d95926; --c3:#199e70; --c4:#c98500;
    --c5:#d55181; --c6:#008300; --c7:#9085e9; --c8:#e66767; --other:#8f8e88;
    --q1:#184f95; --q2:#1c5cab; --q3:#256abf; --q4:#2a78d6; --q5:#5598e7; --q6:#86b6ef; --q7:#b7d3f6;
    --nn-line: rgba(255,255,255,0.40);
  }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
         color: var(--text-primary); background: var(--surface-1); }
  #app { display: flex; height: 100vh; }
  #sidebar { width: 320px; flex-shrink: 0; border-right: 1px solid var(--border);
             padding: 16px; overflow-y: auto; }
  #sidebar h1 { font-size: 15px; margin: 0 0 4px; }
  .subtitle { font-size: 11.5px; color: var(--text-secondary); margin-bottom: 10px; line-height: 1.5; }
  #main { flex: 1; position: relative; overflow: hidden; min-height: 60vh; }
  svg#plot { width: 100%; height: 100%; display: block; cursor: grab; background: var(--surface-1); }
  svg#plot.dragging { cursor: grabbing; }
  h2.section { font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em;
               color: var(--muted); margin: 16px 0 6px; }
  .segs { display: flex; flex-wrap: wrap; gap: 4px; }
  button.seg { font: inherit; font-size: 12px; padding: 4px 9px; border-radius: 6px; cursor: pointer;
               border: 1px solid var(--border); background: var(--surface-1); color: var(--text-primary); }
  button.seg:hover { background: var(--wash); }
  button.seg.on { background: var(--active); border-color: transparent; font-weight: 600; }
  #search { width: 100%; padding: 6px 8px; font-size: 13px; border: 1px solid var(--border);
            border-radius: 6px; background: var(--surface-1); color: var(--text-primary); }
  #searchResult { font-size: 11.5px; color: var(--text-secondary); min-height: 16px; margin-top: 3px; }
  .legend-row { display: flex; align-items: center; gap: 8px; padding: 4px; border-radius: 6px;
                cursor: pointer; font-size: 12.5px; line-height: 1.3; }
  .legend-row:hover { background: var(--wash); }
  .legend-row.active { background: var(--active); }
  .legend-n { color: var(--muted); font-size: 11px; }
  .legend-row svg { flex-shrink: 0; overflow: visible; }
  .seqbar { height: 10px; border-radius: 3px; margin: 4px 0 2px;
            background: linear-gradient(90deg, var(--q1), var(--q2), var(--q3), var(--q4), var(--q5), var(--q6), var(--q7)); }
  .seqticks { display: flex; justify-content: space-between; font-size: 11px; color: var(--text-secondary); }
  #members { font-size: 12px; color: var(--text-secondary); line-height: 1.6; }
  #members a { color: var(--text-primary); cursor: pointer; text-decoration: none; border-bottom: 1px dotted var(--muted); }
  .hint, .notes { font-size: 11.5px; color: var(--text-secondary); line-height: 1.55; }
  .notes table { border-collapse: collapse; margin: 4px 0; font-size: 11.5px; }
  .notes td, .notes th { padding: 1px 6px 1px 0; text-align: left; font-variant-numeric: tabular-nums; }
  button.ctrl { width: 30px; height: 30px; border-radius: 6px; border: 1px solid var(--border);
                background: var(--surface-1); color: var(--text-primary); font-size: 16px; cursor: pointer; margin-right: 4px; }
  #zoomCtrls { position: absolute; top: 12px; left: 12px; z-index: 5; }
  #resetBtn { position: absolute; top: 12px; right: 12px; z-index: 5; padding: 6px 12px; border-radius: 6px;
              border: 1px solid var(--border); background: var(--surface-1); color: var(--text-primary); cursor: pointer; font-size: 12.5px; }
  button.ctrl:hover, #resetBtn:hover { background: var(--wash); }
  #tooltip { position: fixed; pointer-events: none; background: var(--surface-1); color: var(--text-primary);
             border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px; font-size: 12px;
             box-shadow: 0 4px 14px rgba(0,0,0,0.18); display: none; z-index: 10; max-width: 300px; line-height: 1.5; }
  #tooltip .t-head { font-weight: 700; font-size: 13px; }
  #tooltip .t-k { color: var(--text-secondary); }
  .pt { transition: transform 0.6s ease, opacity 0.15s; cursor: pointer; }
  .pt .mk { stroke: var(--surface-1); stroke-width: 1.2; }
  .pt .mk.neutral { fill: none !important; stroke: var(--other); stroke-width: 1.6; }
  .pt .hit { fill: transparent; }
  .pt .lab { font-size: 10px; fill: var(--text-primary); paint-order: stroke; stroke: var(--surface-1);
             stroke-width: 3px; stroke-linejoin: round; display: none; pointer-events: none; }
  svg.zoomed .pt .lab, .pt.labeled .lab { display: inline; }
  .pt.dimmed { opacity: 0.08; }
  .pt.focus .mk { stroke: var(--text-primary); stroke-width: 2; }
  .cl-lab { font-size: 20px; font-weight: 700; fill: var(--text-primary); paint-order: stroke;
            stroke: var(--surface-1); stroke-width: calc(4px * var(--k, 1)); stroke-linejoin: round; pointer-events: none;
            transition: opacity 0.15s; }
  .cl-lab.dimmed { opacity: 0.1; }
  .nnline { stroke: var(--nn-line); stroke-width: 1; vector-effect: non-scaling-stroke; pointer-events: none; }
  @media (max-width: 760px) {
    #app { flex-direction: column; height: auto; }
    #sidebar { width: 100%; border-right: none; border-bottom: 1px solid var(--border); max-height: 50vh; }
    #main { height: 70vh; }
  }
</style>
</head>
<body>
<div id="app">
  <div id="sidebar">
    <h1>__TITLE__</h1>
    <div class="subtitle">__SUBTITLE__</div>

    <h2 class="section">Layout / clustering</h2>
    <div class="segs" id="viewSegs">__VIEW_BUTTONS__</div>

    <h2 class="section">Color by</h2>
    <div class="segs" id="modeSegs"></div>

    <h2 class="section">Search a gene</h2>
    <input id="search" type="text" placeholder="__SEARCH_PLACEHOLDER__" aria-label="search">
    <div id="searchResult"></div>

    <h2 class="section" id="legendTitle">Legend</h2>
    <div id="legend"></div>
    <div id="members"></div>

    <div class="notes">__NOTES_HTML__</div>
    <div class="hint" style="margin-top:12px">
      Scroll to zoom, drag to pan; gene names appear when zoomed in. Hover a point for details;
      click it to highlight its nearest neighbours (lines). Click a legend row to isolate that
      group and list its members. Marker shape + on-plot cluster numbers carry cluster identity
      beyond the 8 palette hues.
    </div>
  </div>
  <div id="main">
    <div id="zoomCtrls">
      <button class="ctrl" onclick="zoomBy(0.8)" aria-label="zoom in">+</button>
      <button class="ctrl" onclick="zoomBy(1.25)" aria-label="zoom out">&minus;</button>
    </div>
    <button id="resetBtn" onclick="resetView()">Reset view</button>
    <svg id="plot" viewBox="0 0 __WIDTH__ __HEIGHT__" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="embedding scatter">
      <g id="nnLayer"></g>
      <g id="ptLayer"></g>
      <g id="clLayer"></g>
    </svg>
  </div>
</div>
<div id="tooltip"></div>

<script>
const DATA = __DATA_JSON__;
const NS = "http://www.w3.org/2000/svg";
const FULL = [0, 0, __WIDTH__, __HEIGHT__];
const svg = document.getElementById("plot");
const tooltip = document.getElementById("tooltip");
const ids = Object.keys(DATA.nodes);
const viewKeys = Object.keys(DATA.views);
let view = viewKeys[0], mode = DATA.modes[0].key;
let viewBox = FULL.slice(), isolated = null, focusId = null;
const R = 6;

// ---------- marker shapes (composite encoding: hue slot x shape) ----------
function shapePath(k, r) {
  if (k === 1) return `M${-r*0.88},${-r*0.88}h${r*1.76}v${r*1.76}h${-r*1.76}z`;            // square
  if (k === 2) return `M0,${-r*1.15}L${r*1.05},${r*0.7}L${-r*1.05},${r*0.7}z`;               // triangle
  if (k === 3) return `M0,${-r*1.2}L${r*1.1},0L0,${r*1.2}L${-r*1.1},0z`;                     // diamond
  return `M${-r},0a${r},${r} 0 1,0 ${2*r},0a${r},${r} 0 1,0 ${-2*r},0`;                       // circle
}
function catStyle(i) { return { color: `var(--c${(i % 8) + 1})`, shape: Math.floor(i / 8) % 4 }; }

// ---------- build points once ----------
const ptEls = {};
const layer = document.getElementById("ptLayer");
for (const id of ids) {
  const g = document.createElementNS(NS, "g"); g.setAttribute("class", "pt"); g.dataset.id = id;
  const hit = document.createElementNS(NS, "circle"); hit.setAttribute("class", "hit"); hit.setAttribute("r", 12);
  const mk = document.createElementNS(NS, "path"); mk.setAttribute("class", "mk");
  const lab = document.createElementNS(NS, "text"); lab.setAttribute("class", "lab");
  lab.setAttribute("x", 8); lab.setAttribute("y", 3.5); lab.textContent = DATA.nodes[id].label;
  const inner = document.createElementNS(NS, "g");
  inner.append(hit, mk, lab); g.appendChild(inner); layer.appendChild(g); ptEls[id] = { g, mk, inner };
  g.addEventListener("pointerenter", e => showTip(e, id));
  g.addEventListener("pointermove", e => showTip(e, id));
  g.addEventListener("pointerleave", hideTip);
  g.addEventListener("click", e => { e.stopPropagation(); if (focusId === id) clearFocus(); else setFocus(id); });
}

function placePoints() {
  const P = DATA.views[view].pos;
  for (const id of ids) { const p = P[id]; ptEls[id].g.style.transform = p ? `translate(${p[0]}px,${p[1]}px)` : "scale(0)"; }
  const cl = document.getElementById("clLayer"); cl.textContent = "";
  const k = viewBox[2] / FULL[2];
  for (const [c, xy] of Object.entries(DATA.views[view].cent)) {
    const t = document.createElementNS(NS, "text"); t.setAttribute("class", "cl-lab");
    t.setAttribute("x", xy[0]); t.setAttribute("y", xy[1]); t.setAttribute("text-anchor", "middle");
    t.setAttribute("dominant-baseline", "middle"); t.dataset.c = c; t.textContent = c; t.style.fontSize = (20 * k) + "px"; cl.appendChild(t);
  }
  document.getElementById("clLayer").style.display = mode === "__cluster__" ? "" : "none";
}

// group key + style of a node under the current mode
function modeDef() { return DATA.modes.find(m => m.key === mode); }
function groupOf(id) {
  const m = modeDef();
  if (m.type === "cluster") return DATA.views[view].cl[id];
  const v = DATA.nodes[id].attrs[m.key];
  if (m.type === "categorical") return v == null ? DATA.neutral[0] : String(v);
  return null;
}
function clusterIds() { return [...new Set(Object.values(DATA.views[view].cl))].sort((a, b) => a - b); }
function styleOfGroup(g) {
  const m = modeDef();
  if (m.type === "cluster") return catStyle(clusterIds().indexOf(g));
  if (DATA.neutral.includes(g)) return { color: "var(--other)", shape: 0, neutral: true };
  return catStyle(m.values.filter(v => !DATA.neutral.includes(v)).indexOf(g));
}
function seqColor(v) {
  const m = modeDef();
  if (v == null) return "var(--other)";
  const t = m.log ? Math.log10(v + 1) : v;
  const k = Math.min(6, Math.max(0, Math.floor((t - m.min) / (m.max - m.min + 1e-9) * 7)));
  return `var(--q${k + 1})`;
}

function paint() {
  const m = modeDef();
  for (const id of ids) {
    const { mk } = ptEls[id];
    if (m.type === "sequential") {
      mk.setAttribute("d", shapePath(0, R)); mk.style.fill = seqColor(DATA.nodes[id].attrs[m.key]);
      mk.classList.remove("neutral");
    } else {
      const s = styleOfGroup(groupOf(id));
      mk.setAttribute("d", shapePath(s.shape, R)); mk.style.fill = s.color;
      mk.classList.toggle("neutral", !!s.neutral);
    }
  }
  document.getElementById("clLayer").style.display = m.type === "cluster" ? "" : "none";
  buildLegend();
  applyDim();
}

// ---------- legend (= isolate control + table view) ----------
function swatch(s) {
  const sv = document.createElementNS(NS, "svg"); sv.setAttribute("width", 14); sv.setAttribute("height", 14);
  sv.setAttribute("viewBox", "-7 -7 14 14");
  const p = document.createElementNS(NS, "path"); p.setAttribute("d", shapePath(s.shape, 5.5));
  if (s.neutral) { p.style.fill = "none"; p.style.stroke = "var(--other)"; p.style.strokeWidth = 1.6; }
  else p.style.fill = s.color;
  sv.appendChild(p); return sv;
}
function buildLegend() {
  const m = modeDef(), box = document.getElementById("legend"); box.textContent = "";
  document.getElementById("legendTitle").textContent =
    m.type === "cluster" ? "Clusters (click to isolate)" : m.type === "categorical" ? m.label + " (click to isolate)" : m.label;
  if (m.type === "sequential") {
    const bar = document.createElement("div"); bar.className = "seqbar";
    const ticks = document.createElement("div"); ticks.className = "seqticks";
    const lo = document.createElement("span"), hi = document.createElement("span");
    lo.textContent = m.log ? Math.round(10 ** m.min - 1) : m.min.toFixed(2);
    hi.textContent = m.log ? Math.round(10 ** m.max - 1) : m.max.toFixed(2);
    ticks.append(lo, hi); box.append(bar, ticks); return;
  }
  const groups = m.type === "cluster" ? clusterIds() : m.values;
  const counts = {}; for (const id of ids) { const g = groupOf(id); counts[g] = (counts[g] || 0) + 1; }
  for (const g of groups) {
    if (!counts[g]) continue;
    const row = document.createElement("div"); row.className = "legend-row"; row.dataset.g = g;
    if (isolated !== null && String(isolated) === String(g)) row.classList.add("active");
    const txt = document.createElement("span");
    const name = m.type === "cluster" ? `C${g}` + (DATA.views[view].names[g] ? " · " + DATA.views[view].names[g] : "") : g;
    txt.textContent = name + " ";
    const n = document.createElement("span"); n.className = "legend-n"; n.textContent = `(n=${counts[g]})`;
    txt.appendChild(n);
    row.append(swatch(styleOfGroup(g)), txt);
    row.addEventListener("click", () => toggleIsolate(g));
    box.appendChild(row);
  }
  showMembers();
}
function toggleIsolate(g) { isolated = (isolated !== null && String(isolated) === String(g)) ? null : g; buildLegend(); applyDim(); }
function showMembers() {
  const box = document.getElementById("members"); box.textContent = "";
  if (isolated === null) return;
  const mem = ids.filter(id => String(groupOf(id)) === String(isolated))
                 .sort((a, b) => DATA.nodes[a].label.localeCompare(DATA.nodes[b].label));
  const h = document.createElement("div"); h.style.margin = "8px 0 2px"; h.style.fontWeight = 600;
  h.textContent = `Members (${mem.length})`; box.appendChild(h);
  mem.forEach((id, i) => {
    const a = document.createElement("a"); a.textContent = DATA.nodes[id].label;
    a.addEventListener("click", () => { setFocus(id); zoomTo(id); });
    box.appendChild(a); if (i < mem.length - 1) box.appendChild(document.createTextNode(", "));
  });
}

// ---------- dim / focus ----------
function applyDim() {
  const keep = focusId ? new Set([focusId, ...(DATA.views[view].nn[focusId] || []).map(x => x[0])]) : null;
  for (const id of ids) {
    const inIso = isolated === null || String(groupOf(id)) === String(isolated);
    const inFocus = !keep || keep.has(id);
    ptEls[id].g.classList.toggle("dimmed", !(inIso && inFocus));
    ptEls[id].g.classList.toggle("labeled", !!keep && keep.has(id));
    ptEls[id].g.classList.toggle("focus", id === focusId);
  }
  document.querySelectorAll(".cl-lab").forEach(t =>
    t.classList.toggle("dimmed", (isolated !== null && modeDef().type === "cluster" && t.dataset.c !== String(isolated)) || !!keep));
  drawNN();
}
function drawNN() {
  const L = document.getElementById("nnLayer"); L.textContent = "";
  if (!focusId) return;
  const P = DATA.views[view].pos, a = P[focusId]; if (!a) return;
  for (const [j] of (DATA.views[view].nn[focusId] || [])) {
    const b = P[j]; if (!b) continue;
    const l = document.createElementNS(NS, "line"); l.setAttribute("class", "nnline");
    l.setAttribute("x1", a[0]); l.setAttribute("y1", a[1]); l.setAttribute("x2", b[0]); l.setAttribute("y2", b[1]);
    L.appendChild(l);
  }
}
function setFocus(id) { focusId = id; applyDim(); }
function clearFocus() { focusId = null; applyDim(); }

// ---------- tooltip (textContent only: labels are data) ----------
function addLine(k, v) {
  const d = document.createElement("div");
  const ks = document.createElement("span"); ks.className = "t-k"; ks.textContent = k + ": ";
  d.append(ks, document.createTextNode(v == null ? "–" : String(v))); tooltip.appendChild(d);
}
function showTip(e, id) {
  const n = DATA.nodes[id], V = DATA.views[view]; tooltip.textContent = "";
  const h = document.createElement("div"); h.className = "t-head"; h.textContent = n.label; tooltip.appendChild(h);
  const c = V.cl[id]; addLine("cluster", `C${c}` + (V.names[c] ? " · " + V.names[c] : ""));
  for (const [k, v] of n.tip) addLine(k, v);
  const nn = (V.nn[id] || []).slice(0, 5).map(([j, s]) => `${DATA.nodes[j].label} (${s.toFixed(2)})`);
  if (nn.length) addLine("nearest", nn.join(", "));
  tooltip.style.display = "block";
  const x = Math.min(e.clientX + 14, window.innerWidth - 310);
  tooltip.style.left = x + "px"; tooltip.style.top = (e.clientY + 14) + "px";
}
function hideTip() { tooltip.style.display = "none"; }

// ---------- zoom / pan (viewBox) ----------
// marks, labels and line widths keep a constant on-screen size: counter-scale them by the zoom factor
function setViewBox() {
  svg.setAttribute("viewBox", viewBox.join(" "));
  svg.classList.toggle("zoomed", viewBox[2] < FULL[2] * 0.45);
  const k = viewBox[2] / FULL[2];
  for (const id of ids) ptEls[id].inner.setAttribute("transform", `scale(${k})`);
  document.querySelectorAll(".cl-lab").forEach(t => t.style.fontSize = (20 * k) + "px");
  svg.style.setProperty("--k", k);
}
function svgPoint(evt) { const pt = svg.createSVGPoint(); pt.x = evt.clientX; pt.y = evt.clientY; return pt.matrixTransform(svg.getScreenCTM().inverse()); }
function zoomAt(f, cx, cy) {
  let [x, y, w, h] = viewBox; const nw = Math.max(80, Math.min(FULL[2] * 3, w * f)), nh = nw * (h / w);
  viewBox = [cx - (cx - x) / w * nw, cy - (cy - y) / h * nh, nw, nh]; setViewBox();
}
function zoomBy(f) { zoomAt(f, viewBox[0] + viewBox[2] / 2, viewBox[1] + viewBox[3] / 2); }
function zoomTo(id) {
  const p = DATA.views[view].pos[id]; if (!p) return;
  const w = 420, h = w * FULL[3] / FULL[2]; viewBox = [p[0] - w / 2, p[1] - h / 2, w, h]; setViewBox();
}
svg.addEventListener("wheel", e => { e.preventDefault(); const p = svgPoint(e); zoomAt(e.deltaY > 0 ? 1.12 : 0.89, p.x, p.y); }, { passive: false });
let dragging = false, moved = 0, d0 = null, vb0 = null;
svg.addEventListener("pointerdown", e => { dragging = true; moved = 0; d0 = { x: e.clientX, y: e.clientY }; vb0 = viewBox.slice(); svg.classList.add("dragging"); });
window.addEventListener("pointermove", e => {
  if (!dragging) return; const s = vb0[2] / svg.clientWidth;
  moved = Math.hypot(e.clientX - d0.x, e.clientY - d0.y);
  viewBox = [vb0[0] - (e.clientX - d0.x) * s, vb0[1] - (e.clientY - d0.y) * s, vb0[2], vb0[3]]; setViewBox();
});
window.addEventListener("pointerup", () => { dragging = false; svg.classList.remove("dragging"); });
svg.addEventListener("click", () => { if (moved < 4) clearFocus(); });
function resetView() { viewBox = FULL.slice(); setViewBox(); isolated = null; focusId = null; buildLegend(); applyDim(); }

// ---------- controls ----------
const modeSegs = document.getElementById("modeSegs");
for (const m of DATA.modes) {
  const b = document.createElement("button"); b.className = "seg"; b.dataset.mode = m.key; b.textContent = m.label;
  b.addEventListener("click", () => { mode = m.key; isolated = null; syncSegs(); paint(); }); modeSegs.appendChild(b);
}
document.querySelectorAll("#viewSegs .seg").forEach(b => b.addEventListener("click", () => {
  view = b.dataset.view; if (modeDef().type === "cluster") isolated = null; syncSegs(); placePoints(); paint();
}));
function syncSegs() {
  document.querySelectorAll("#viewSegs .seg").forEach(b => b.classList.toggle("on", b.dataset.view === view));
  document.querySelectorAll("#modeSegs .seg").forEach(b => b.classList.toggle("on", b.dataset.mode === mode));
}
const searchBox = document.getElementById("search"), searchResult = document.getElementById("searchResult");
searchBox.addEventListener("input", () => {
  const q = searchBox.value.trim().toUpperCase(); if (!q) { searchResult.textContent = ""; return; }
  const hit = ids.find(id => DATA.nodes[id].label.toUpperCase() === q || id.toUpperCase() === q) ||
              ids.find(id => DATA.nodes[id].label.toUpperCase().startsWith(q));
  if (!hit) { searchResult.textContent = "no match"; return; }
  const c = DATA.views[view].cl[hit];
  searchResult.textContent = `found: ${DATA.nodes[hit].label} (C${c})`;
  setFocus(hit); zoomTo(hit);
});

syncSegs(); placePoints(); paint();
</script>
</body>
</html>
"""
