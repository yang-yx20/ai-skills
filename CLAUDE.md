# Yuexuan's Claude Code knowledge folder

This folder lives in Dropbox, so `.claude/skills/` and this file sync to any
computer where this same path is opened as the Claude Code working directory.
That's the intended mechanism for cross-machine reuse — the global
`~/.claude/skills/` directory does *not* sync between machines, so anything
meant to be reusable across computers belongs here instead, not there.

This folder is also mirrored to a git repo, github.com/yang-yx20/ai-skills
(see `README.md`), so it can be `git clone`d on clusters that don't run Dropbox.

## Skills

Reusable procedures live under `.claude/skills/<name>/SKILL.md`. Each one
should have a specific, accurate one-line `description` in its frontmatter —
that's what gets matched against future requests, so a vague description
means the skill never gets picked up automatically.

Naming convention (extend as new categories show up):
- `ncbi-*` / `gene-*` — NCBI/PubMed/gene-database queries and lookups
- `analysis-*` — how to analyze a specific data type/assay
- `fileformat-*` — how to read/interpret a specific file format
- `meta-*` — process/authoring skills about Claude Code itself
- `viz-*` — how to build a specific kind of figure / interactive visualization deliverable

Current skills:
- `gene-pubmed-count` — count PubMed articles linked to a gene (single live
  lookup or bulk cached lookup).
- `meta-skill-authoring` — template/conventions for writing a new skill in
  this folder (naming, frontmatter, structure, git commit/push steps).
- `ncbi-ftp-bulk-data` — check ftp.ncbi.nlm.nih.gov for a bulk file before
  looping a live NCBI API call across many genes; catalogs the bulk files
  already used (gene2pubmed, mim2gene_medgen, GeneRIF, HomoloGene, gene_info).
- `viz-interactive-cluster-html` — self-contained interactive HTML (zoom/pan,
  tooltip, search, click-to-isolate clusters) for a cluster network or a
  UMAP/embedding scatter; includes the generic scatter builder
  `interactive_scatter.py`.
- `viz-svg-for-illustrator` — matplotlib `rcParams` (`svg.fonttype`,
  `pdf.fonttype`, `font.family`) that keep SVG/PDF text as editable `<text>`
  instead of outlined paths when opened in Illustrator.
- `viz-volcano-barplot-style` — lab (L-Kynurenine) publication style for
  volcano plots and NES / log2FC / per-gene fold-change bar plots; drop-in
  helper `pub_style.py` (adjustText labels, PDF+SVG).

When a new recurring task comes up that's worth not re-deriving next time,
add a new skill folder here rather than relying on session memory — skills
are plain files, so they're the portable option.
