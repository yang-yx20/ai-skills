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

## Statistics convention (use this, not limma / moderated t)

The style comes with the Kyn statistics. Use them unless the user asks for something else. Sources: Kyn `volcano.py` and `GSEA_ORA/step1_compute_per_protein_log2fc.py`.

| quantity | definition |
|---|---|
| log2FC | `log2(mean(linear S/N, group A) / mean(linear S/N, group B))`, i.e. a ratio of arithmetic means, **not** mean(log2) − mean(log2) |
| p | Welch t-test (`equal_var=False`) on the same **linear** S/N values |
| padj | Benjamini–Hochberg over all tested proteins |
| hit | p (or padj) < 0.05 **and** \|FC\| > 1.25 (\|log2FC\| > 0.32) |
| volcano versions | make both: `volcano_rawP` (y = −log10 p) and `volcano_padj` (y = −log10 padj) |
| GSEA | `gseapy.prerank` ranked by the **raw log2FC** above |

- Input is the TMT `"... sn sum"` columns. They are already equal-total normalised per channel, so do no extra scaling.
- Filter out decoys (`##`), `contaminant` rows (even familiar proteins such as CTSD that the search flagged) and rows with any zero channel.
- Keep the full-precision linear values in any saved table. Rounding to 2 decimals turns tiny S/N into 0, and a later log2 then gives −inf.
- A low-signal flag is still worth adding to the hit rule: max group mean S/N < 20. Without it, near-zero proteins produce huge fold changes.
- Spot-check 2–3 proteins by recomputing FC and Welch p by hand from the raw TSV.

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
   - A gene that wasn't quantified gets `np.nan`, which draws an "n.d." mark with no bar. Never silently drop a marker the user asked for. A label of `""` with `np.nan` leaves a blank spacer slot between gene groups.
   - Label markers by their common name with the symbol in parentheses, e.g. `CD11b (ITGAM)`. Mouse-only markers such as F4/80 have no human macrophage counterpart (EMR1 is an eosinophil marker, PMID 17823986), so show them as n.d. and say why.
   - If the user wants markers to "represent" a pathway, give references and verify each one against PubMed (E-utilities esearch with title words, first author and year, then esummary and a title comparison) before citing. Worked example: `xvivo_vs_rpmi/marker_barplots.py` + `results/references_lipid_panels.tsv`.

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
