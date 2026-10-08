# -*- coding: utf-8 -*-
"""Lab publication style for volcano plots and bar plots (matplotlib).

Distilled from iMac_stimuli/L-Kynurenine/Proteomics/12fractions_3replicates/
volcano.py and barplots.py. Copy this file next to an analysis script (so the
analysis folder stays self-contained) and `import pub_style as ps`.

    ps.volcano(ax, log2fc, padj, genes, up_mask, dn_mask, label_genes, ...)
    ps.hbar(ax, labels, values, sig_mask)          # NES / log2FC horizontal bars
    ps.vbar(ax, labels, values, sig_mask)          # log2FC vertical bars (gene panels)
    ps.gene_barplot(ax, groups, order, ref)        # per-gene FC vs ref, SEM, dots, stars
    ps.save(fig, stem)                             # -> stem.pdf + stem.svg
"""
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from scipy.stats import ttest_ind

matplotlib.rcParams["pdf.fonttype"] = 42      # editable text in Illustrator (PDF)
matplotlib.rcParams["svg.fonttype"] = "none"  # SVG: keep <text>, not outlined paths
matplotlib.rcParams["font.family"] = "Arial"

GRAY = "#D4D5D4"     # non-significant / reference group
RED = "#8D463F"      # significant (up, or the treated group)
BLUE = "#3F5F8D"     # significant down -- only for two-direction comparisons
FONT = {"family": "Arial", "size": 6}
LABEL_SIZE = 5       # gene labels inside volcanoes
S_NS, S_SIG = 20, 34 # volcano dot sizes
DASH = dict(color="k", linestyle=(0, (4, 4)), alpha=0.5, linewidth=0.5)
ARROW = dict(arrowstyle="-", color="gray", lw=0.3)


def style_axes(ax):
    """Open axes: no top/right spine, 0.5-lw spines, 3/0.5 ticks, 6 pt Arial ticks."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for s in ax.spines.values():
        s.set_linewidth(0.5)
    ax.tick_params(length=3, width=0.5)
    plt.setp(ax.get_xticklabels(), **FONT)
    plt.setp(ax.get_yticklabels(), **FONT)


def save(fig, stem):
    plt.tight_layout()
    fig.savefig(stem + ".pdf")
    fig.savefig(stem + ".svg")
    plt.close(fig)


def volcano(ax, log2fc, p, genes, up, dn, label_mask, fc_thr, p_thr=0.05,
            ylabel="-log$_{10}P_{adj}$", title=None, two_color=True):
    """Kyn-style volcano. `p` must be the same p (raw or adjusted) the hit rule uses,
    so the dashed horizontal line is the real cutoff. `up`/`dn`/`label_mask` are bool
    arrays aligned with log2fc. All labelled points go through adjustText."""
    from adjustText import adjust_text
    log2fc, p, genes = np.asarray(log2fc, float), np.asarray(p, float), np.asarray(genes)
    y = -np.log10(p)
    ns = ~(up | dn)
    ax.scatter(log2fc[ns], y[ns], c=GRAY, s=S_NS, linewidths=0, zorder=2)
    ax.scatter(log2fc[up], y[up], c=RED, s=S_SIG, linewidths=0, zorder=3)
    ax.scatter(log2fc[dn], y[dn], c=BLUE if two_color else RED, s=S_SIG, linewidths=0, zorder=3)
    ax.axhline(-np.log10(p_thr), **DASH)
    ax.axvline(fc_thr, **DASH)
    ax.axvline(-fc_thr, **DASH)
    ax.set_xlabel("log$_2$FC", fontdict=FONT)
    ax.set_ylabel(ylabel, fontdict=FONT)
    if title:
        ax.set_title(title, fontdict=FONT)
    xmax = float(np.ceil(np.nanmax(np.abs(log2fc))))
    ax.set_xlim(-xmax, xmax)
    ax.set_ylim(0, max(np.nanmax(y), -np.log10(p_thr)) * 1.08)
    style_axes(ax)
    texts = [ax.text(log2fc[i], y[i], genes[i], fontsize=LABEL_SIZE, fontfamily="Arial")
             for i in np.where(label_mask)[0]]
    if texts:
        # pass the scatter coordinates so labels are pushed off the dots as well
        adjust_text(texts, x=log2fc, y=y, ax=ax, arrowprops=ARROW,
                    expand=(1.2, 1.4), force_text=(0.3, 0.6), max_move=None)
    return texts


def _bar_colors(values, sig):
    values, sig = np.asarray(values, float), np.asarray(sig, bool)
    return np.where(~sig, GRAY, np.where(values > 0, RED, BLUE))


def short_label(s, n=60):
    """Trim long term names at a word boundary (for bar labels)."""
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"


def hbar(ax, labels, values, sig=None, xlabel="NES", title=None):
    """Horizontal bars (e.g. GSEA NES): red >0, blue <0, gray if not sig."""
    values = np.asarray(values, float)
    sig = np.ones(len(values), bool) if sig is None else np.asarray(sig, bool)
    yy = np.arange(len(values))
    ax.barh(yy, values, height=0.7, color=_bar_colors(values, sig), edgecolor="none", zorder=2)
    ax.axvline(0, color="k", lw=0.5, zorder=3)
    ax.set_yticks(yy)
    ax.set_yticklabels(labels, fontdict=FONT)
    ax.set_ylim(-0.6, len(values) - 0.4)
    ax.set_xlabel(xlabel, fontdict=FONT)
    ax.xaxis.set_major_locator(MaxNLocator(6))
    if title:
        ax.set_title(title, fontdict=FONT)
    style_axes(ax)
    ax.tick_params(axis="y", length=0)


def vbar(ax, labels, values, sig=None, ylabel="log$_2$FC", title=None):
    """Vertical bars per gene (e.g. log2FC panels): red >0, blue <0, gray if not sig.
    NaN values = not detected: no bar, an "n.d." mark sits on the zero line instead.
    An empty-string label leaves a blank slot (use it as a spacer between gene groups)."""
    labels, values = list(labels), np.asarray(values, float)
    sig = np.ones(len(values), bool) if sig is None else np.asarray(sig, bool)
    nd = np.isnan(values)
    xx = np.arange(len(values))
    ax.bar(xx[~nd], values[~nd], width=0.7, color=_bar_colors(values[~nd], sig[~nd]),
           edgecolor="none", zorder=2)
    for i in np.where(nd)[0]:
        if str(labels[i]):
            ax.text(xx[i], 0, "n.d.", ha="center", va="bottom", fontdict=FONT, color="0.4")
    ax.axhline(0, color="k", lw=0.5, zorder=3)
    ax.set_xticks(xx)
    ax.set_xticklabels(labels, fontdict=FONT, rotation=90)
    ax.set_xlim(-0.6, len(values) - 0.4)
    ax.set_ylabel(ylabel, fontdict=FONT)
    ax.yaxis.set_major_locator(MaxNLocator(6))
    if title:
        ax.set_title(title, fontdict=FONT)
    style_axes(ax)
    ax.tick_params(axis="x", length=0)
    plt.setp(ax.get_xticklabels(), rotation=90)


def _stars(p):
    return "***" if p < 1e-3 else "**" if p < 1e-2 else "*" if p < 0.05 else "ns"


def gene_barplot(ax, groups, order, ref, xlabel="", ylabel="fold change", seed=0):
    """Per-gene barplot (Kyn barplots.py): bar = mean FC vs mean(ref), SEM error bars,
    replicate dots (s=3, black, jittered), Welch-t stars vs ref on LINEAR values.
    `groups` = {name: 1-D array of linear replicate values}."""
    ref_mean = np.mean(groups[ref])
    fc = {g: np.asarray(groups[g], float) / ref_mean for g in order}
    x = np.arange(len(order))
    means = np.array([fc[g].mean() for g in order])
    sems = np.array([fc[g].std(ddof=1) / np.sqrt(len(fc[g])) for g in order])
    ax.bar(x, means, yerr=sems, width=0.7, color=[GRAY if g == ref else RED for g in order],
           edgecolor="none", zorder=2, error_kw=dict(elinewidth=0.5, capsize=2, capthick=0.5, zorder=3))
    rng = np.random.default_rng(seed)
    for xi, g in zip(x, order):
        ax.scatter(xi + (rng.random(len(fc[g])) - 0.5) * 0.28, fc[g], s=3, color="black",
                   linewidths=0, zorder=4)
    ymax = float((means + sems).max())
    pad = 0.05 * ymax
    for i, g in enumerate(order):
        if g == ref:
            continue
        s = _stars(ttest_ind(groups[g], groups[ref], equal_var=False).pvalue)
        if s != "ns":
            ax.text(i, max(means[i] + sems[i], fc[g].max()) + pad, s, ha="center", va="bottom", fontdict=FONT)
    ax.set_xticks(x)
    ax.set_xticklabels(order, fontdict=FONT)
    ax.set_xlabel(xlabel, fontdict=FONT)
    ax.set_ylabel(ylabel, fontdict=FONT)
    ax.set_ylim(0, (ymax + pad) * 1.18)
    style_axes(ax)
