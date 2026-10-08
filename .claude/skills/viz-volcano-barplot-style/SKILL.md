---
name: viz-volcano-barplot-style
description: Lab publication style for proteomics/omics volcano plots and bar plots in matplotlib (Arial 6 pt, gray #D4D5D4 / dark-red #8D463F / dark-blue #3F5F8D, 0.5-lw open axes, dashed threshold lines, adjustText gene labels, PDF+SVG editable in Illustrator) with a drop-in helper pub_style.py. Use whenever asked to make or restyle a volcano plot, a GSEA NES / log2FC bar plot, or a per-gene fold-change barplot "in our style" / "like the Kynurenine figures".
---

# Volcano + bar plot style (Kynurenine-proteomics style)

The canonical figures come from the L-Kynurenine TMT project:
- `iMac_stimuli/L-Kynurenine/Proteomics/12fractions_3replicates/volcano.py`
- `iMac_stimuli/L-Kynurenine/Proteomics/12fractions_3replicates/barplots.py`

`pub_style.py` in this folder packages that style as helpers. **Copy it next to the analysis script** so the analysis folder stays self-contained when shared, then `import pub_style as ps`. Don't import it from this skills folder. A second worked example that uses it with two-direction colors and many labels is `Collaborators/ChloeMark_Alun_BassikLab/Chloe_Mark_Me/xvivo_vs_rpmi/analysis.py`.

## Style spec (shared by every figure)

| element | value |
|---|---|
| rcParams | `pdf.fonttype=42`, `svg.fonttype="none"`, `font.family="Arial"` (see [[viz-svg-for-illustrator]]) |
| text | everything 6 pt Arial; gene labels in volcanoes 5 pt |
| colors | non-sig / reference group `#D4D5D4`; sig (or up, or treated group) `#8D463F`; second direction `#3F5F8D` |
| axes | top/right spines hidden, spines lw 0.5, ticks `length=3, width=0.5` |
| bars | `edgecolor="none"`, width/height 0.7; zero line black lw 0.5 |
| output | always `stem.pdf` + `stem.svg` (no PNG); one figure per file, not multi-panel grids |

## Volcano — `ps.volcano(...)`

- figsize **3.4 × 3.4**; dots `s=20` (non-sig) / `s=34` (sig), `linewidths=0`, zorder 2/3.
- Dashed lines `(0,(4,4))`, black, alpha 0.5, lw 0.5: a horizontal line at p = 0.05 and vertical lines at ±log2 FC threshold.
- x-limits symmetric `±ceil(max|log2FC|)`; y-limit = max × 1.08.
- **The y axis must be the same p the hit rule uses.** If hits are FDR<0.05, plot −log10 FDR (`ylabel="-log$_{10}P_{adj}$"` or `"-log$_{10}$FDR"`). If hits use raw p, plot raw p. Otherwise the dashed line is not the real cutoff.
- **Colors:** a one-sided "treatment vs control" uses red only (`two_color=False`, Kyn default). A two-condition comparison (A vs B, both directions meaningful) uses red = up and blue = down.

### Labeling
- Always use adjustText (`pip install adjustText`; 1.x API):
  ```python
  adjust_text(texts, x=all_x, y=all_y, ax=ax,
              arrowprops=dict(arrowstyle="-", color="gray", lw=0.3),
              expand=(1.2, 1.4), force_text=(0.3, 0.6), max_move=None)
  ```
  Passing `x=`/`y=` of **all** points pushes labels off the dots, not just off each other.
- How many labels is the user's call. Kyn used ≤30, ranked by `negLogP × |log2FC|`. For dense comparisons the user preferred **top 20 per side by |FC|** (40 total). Don't silently cut the label count to make it "clean". If 40 labels won't fit at 3.4", widen the figure (≤ 4.5") instead.
- **Exception — highlight variant with many labels on a dense background:** pass `x=`/`y=` of only the **highlighted** points (`x=x[hl], y=y[hl]`), add `ensure_inside_axes=True`, and use `expand=(1.3, 1.6), force_text=(0.4, 0.8), force_static=(0.4, 0.8)`. With thousands of background dots as obstacles, adjustText has nowhere to put the labels and pushes them all into the axes corners. Example: `xvivo_vs_rpmi/volcano_LAM_genes.py`.
- Highlight-a-gene-set variant (LRR / AhR targets / one gene): gray background, set members that are also significant in red and labeled. If the user asks to label a fixed gene list "with its change", label every member as `GENE (+4.4)`, i.e. log2FC to one decimal. Draw members with `edgecolors="k", linewidths=0.4`: red or blue when they pass the hit rule, gray fill when not. Single-gene variant: red dot with `edgecolors="k", linewidths=0.4`, always labeled. See the `plot_volcano_lrr` and `plot_volcano_chi3l1` functions in Kyn `volcano.py`.

## Bar plots

1. **Per-gene fold-change barplot — `ps.gene_barplot(...)`** (Kyn `barplots.py`)
   - figsize 1.6 × 1.6; one gene per file.
   - Bar = mean fold change vs the reference group's mean (reference bar gray, others red). Error bar = SEM (`elinewidth=0.5, capsize=2`).
   - Replicate dots: `s=3`, black, jitter ±0.14.
   - Welch t-test on **linear** values vs the reference, shown as `*`/`**`/`***` (ns not drawn).
2. **Horizontal NES / score bars — `ps.hbar(...)`** for GSEA results
   - width 3.4", height `0.6 + 0.12 × n_terms`.
   - Red for NES > 0, blue for < 0. Trim term names with `ps.short_label` (breaks at a word boundary) and strip Reactome `R-HSA-…` IDs.
3. **Per-gene log2FC panel bars — `ps.vbar(...)`** for a themed gene list
   - width `0.4 + 0.11 × n_genes`, height 1.6.
   - Colored only if significant: red up, blue down, gray otherwise. Gene names rotated 90°.

## Quick start
```python
import pub_style as ps, matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(3.4, 3.4))
ps.volcano(ax, df.log2FC, df.padj, df.gene, up_mask, dn_mask, label_mask,
           fc_thr=1, ylabel="-log$_{10}P_{adj}$", title="A vs B")
ps.save(fig, "figures/volcano_A_vs_B")
```

## Checks before handing over
- Open the PDF and check that labels don't overlap and every intended label is present.
- `grep -c "<text" fig.svg` should be at least the number of labels plus the tick labels. Text was outlined if it's ~0.
