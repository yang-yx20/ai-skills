---
name: viz-svg-for-illustrator
description: Save a matplotlib figure as an SVG (or PDF) whose text stays as editable, selectable text in Adobe Illustrator instead of being outlined to vector paths. Use whenever asked to export a figure for Illustrator, save an "editable" SVG/PDF, or when a previously-saved SVG opens in Illustrator with labels that can't be selected/edited as text.
---

# SVG/PDF export that keeps text as text (for Illustrator)

By default, matplotlib's SVG and PDF backends draw each character as an
outlined `<path>` (the glyph's shape), not a `<text>` element. That renders
identically everywhere, but once opened in Illustrator every label is a
blob of anchor points — not selectable or editable as text, and font
changes/typos can't be fixed without redrawing the shape.

## The fix: three `rcParams`, set before any `fig.savefig(...)`

```python
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Arial"    # a font that also exists on the AI machine,
                                          # so it isn't silently substituted
plt.rcParams["svg.fonttype"] = "none"    # SVG: keep glyphs as <text>, not outlined paths
plt.rcParams["pdf.fonttype"] = 42        # PDF: embed as TrueType so text stays editable too

fig.savefig("fig.svg")
fig.savefig("fig.pdf")   # optional, same rcParams make PDF text editable in Illustrator too
```

- `svg.fonttype = "none"` is the one that actually matters for SVG — it
  tells matplotlib to emit `<text>` elements with a `font-family` reference
  instead of drawing each glyph as a path. The default is `"path"`.
- `font.family` should be a font Illustrator/the target machine actually has
  (Arial is a safe cross-platform default) — otherwise the `<text>` renders
  fine in a browser (which substitutes a fallback) but may look wrong once
  opened in Illustrator on a machine without that exact font.
- `pdf.fonttype = 42` (TrueType) is the PDF equivalent; the alternative,
  `3` (the default, Type 3), draws bitmap/outline glyphs that are not
  text-editable in Illustrator either.
- Set these as global `rcParams` once near the top of the script (not
  per-`savefig` — there's no `savefig`-level override), so every figure the
  script produces inherits them.

## Reference implementation

`LRR_searching/Adrián César-Razquin et al. 2015 Cell_parody/scripts/01_figure1A_family_skewness.py`
sets all three near the top of the file, right after the `matplotlib.pyplot`
import, and calls `fig.savefig(...)` for several PNG + SVG variants from the
same rcParams.

## Verifying it actually worked

Don't just trust that the rcParams were set — grep the saved file for real
`<text>` elements (a `path`-outlined SVG has none):

```bash
grep -c '<text' fig.svg   # > 0 means text stayed as text
```

If this prints `0`, either `svg.fonttype` wasn't set before `savefig`, or
the figure was re-saved from a cached/closed figure object that predates
the rcParams change — re-run the whole script from a fresh process.

## Scope

This is a pure rendering/export setting — it does not change the figure's
appearance in PNG or on-screen, and it doesn't affect any data or layout.
Apply it to any matplotlib figure that will be handed off as an editable
source file (for a collaborator to retitle/restyle in Illustrator), not to
PNGs meant only for direct viewing/slides, where it has no effect anyway.
