---
name: viz-interactive-cluster-html
description: Build a single self-contained interactive HTML page (zoom/pan SVG, hover tooltip, gene search, click-to-isolate cluster legend with member list, click-to-highlight neighbours) for clustering results — either a network (nodes + edges, e.g. co-expression/STRING communities) or an embedding scatter (UMAP/PCA/t-SNE with Leiden clusters) — via a Python builder that fills a placeholder template. Use whenever asked to make an interactive / clickable / zoomable HTML of clusters, a network, or a UMAP, or to turn a static cluster PNG into an explorable page.
---

# Interactive cluster HTML (network or scatter)

The house style for explorable cluster figures in this Dropbox: a Python script computes
positions and writes **one self-contained `.html`** next to the static PNG it mirrors.
Inline `<style>` + `<script>`, data as an inline JSON blob, no CDN, no `fetch()` — so it
opens offline from Dropbox, survives email, and never breaks when a CDN moves.

## 1. Decide: network or scatter?

| Your data | Use | Reference implementation |
|---|---|---|
| Nodes **and edges** (co-expression, STRING, PPI) — position comes from a layout you compute | **network** | `LRR_searching/Adrián César-Razquin et al. 2015 Cell_parody/scripts/10_build_interactive_network.py` (co-expression), `32_build_interactive_string_network.py` (STRING; same JS engine, different edge legend) |
| Points with **coordinates from an embedding** (UMAP/PCA), clusters from Leiden/k-means, no edges | **scatter** | `interactive_scatter.py` in this folder (generic, importable); applied in `LRR_searching/ESM/sae_analysis/04_build_interactive_umap.py` |

Both share the same skeleton and interactions (§2); they differ only in what's drawn and in
what "neighbours" means (graph edges vs. k nearest by similarity).

## 2. Shared skeleton (keep these conventions)

- **Builder pattern**: a `_TEMPLATE` string with `__PLACEHOLDER__` tokens
  (`__DATA_JSON__`, `__LEGEND_HTML__`, `__WIDTH__`, ...) filled by `str.replace`; assert no
  token is left over before writing.
- **Layout**: left sidebar (title, one-line subtitle with n and data source, search box,
  legend, notes/hint) + main SVG filling the rest. Below 760px the sidebar stacks on top.
- **Interactions** (all vanilla JS):
  - zoom/pan by rewriting the SVG `viewBox` (wheel at cursor, +/− buttons, drag empty space, "Reset view");
  - hover tooltip (build it with `textContent`, never `innerHTML` — gene names are data);
  - click a point → keep it + its neighbours, dim everything else (`.dimmed { opacity: .06–.08 }`);
  - click a legend row → isolate that cluster and list its members (the table view);
  - search → exact-then-prefix match, highlight, zoom to it.
- **Network only**: drag-a-node damped spring simulation (script 10 lines ~435–560;
  springs along real edges + weak anchor, no pairwise repulsion — it blows up in dense
  communities; velocity clamp as safety net).
- **Scatter only**: points are `<g>` with CSS `transform: translate()` so switching views
  animates; counter-scale marks/labels by `viewBox width / full width` so they keep a constant
  on-screen size when zoomed; gene labels appear only when zoomed in or highlighted;
  neighbour lines use `vector-effect: non-scaling-stroke`.
- **Colors** — load the `dataviz` skill first. Use its reference categorical palette
  (`#2a78d6 #eb6834 #1baf7a #eda100 #e87ba4 #008300 #4a3aa7 #e34948`, dark-mode steps in
  `interactive_scatter.py`) as CSS variables with a dark-mode block. Never generate a 9th hue:
  - network (script 10): clusters 9+ fold into an "Other" gray;
  - scatter with many clusters: **composite encoding** — hue = slot `i % 8`, marker shape =
    `i // 8` (circle/square/triangle/diamond), plus cluster numbers drawn at centroids;
  - "unknown"/NA categories: hollow gray ring; magnitudes (e.g. PubMed): one-hue blue ramp, log10.
  A scatter is an all-pairs color context (only 3 slots are CVD-safe against every other), so
  the secondary encodings (shape, on-plot numbers, tooltip, isolate) are required, not optional.

## 3. Scatter: how to call the generic builder

```python
import sys; sys.path.insert(0, "<Yuexuan>/.claude/skills/viz-interactive-cluster-html")
from interactive_scatter import build_interactive_scatter

nodes = pd.DataFrame({"label": genes, "class": cls, "pubmed": n_pubs}, index=accessions)
views = {"tfidf": dict(label="TF-IDF (primary)",
                       coords=umap_df[["umap1", "umap2"]],          # indexed like nodes
                       cluster=leiden_series,                       # id -> int
                       cluster_names={0: "Ig-like ectodomain", ...},# optional
                       neighbors={id: [(other_id, cos_sim), ...]})} # optional, e.g. top-10
build_interactive_scatter("figures/x_interactive.html", nodes, views,
                          title="...", subtitle="n · model · source",
                          categorical=["class"], sequential=["pubmed"],
                          tooltip_cols=["class", "pubmed"], notes_html="<p>method/metrics</p>")
```

Several `views` (e.g. two feature weightings, two resolutions) become a toggle; color-by
modes are "Cluster" (of the active view) + each `categorical` + each `sequential` column.

## 4. Gotchas already hit once

- Script 10: inside the edge loop don't name coordinates `x1/y1` — the `sx()/sy()` closures read
  the outer `x1/y1` bounds, and shadowing them corrupts every later coordinate.
- Sort set members before any seeded layout (`sorted(component)`); hash randomization otherwise
  changes `spring_layout` output run to run.
- A node's `click` must `stopPropagation()`, or the SVG background click handler clears the
  highlight it just set. Treat a mouseup that moved < 4px as a click, not a pan/drag.
- Without counter-scaling, zooming 4x makes 6px dots 24px blobs and labels unreadable (scatter).
- Check the rendered page, not just the code: `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --window-size=1500,950 --virtual-time-budget=3000 --screenshot=out.png file:///abs/path.html`. To screenshot another state, `sed` a copy whose last init line also calls e.g. `toggleIsolate(3)` or sets `mode`.

## 5. Decision guide

- Have edges you want to show → **network**: copy script 10's builder, swap the data loading,
  edge-color legend and subtitle (that's exactly how script 32 was made).
- Only coordinates + labels → **scatter**: import `interactive_scatter.py`; don't copy its template.
- Static figure for a paper → keep the matplotlib PNG; the HTML is the exploration companion
  and should reproduce the same layout/colors so the two can be cross-referenced.
