# Yuexuan's Claude Code knowledge folder

This folder lives in Dropbox, so `.claude/skills/` and this file sync to any
computer where this same path is opened as the Claude Code working directory.
That's the intended mechanism for cross-machine reuse — the global
`~/.claude/skills/` directory does *not* sync between machines, so anything
meant to be reusable across computers belongs here instead, not there.

This folder is also mirrored to a git repo (see `.claude/README.md` once set
up) so it can be `git clone`d on clusters that don't run Dropbox.

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

Current skills:
- `gene-pubmed-count` — count PubMed articles linked to a gene (single live
  lookup or bulk cached lookup).
- `meta-skill-authoring` — template/conventions for writing a new skill in
  this folder (naming, frontmatter, structure, git commit/push steps).
- `ncbi-ftp-bulk-data` — check ftp.ncbi.nlm.nih.gov for a bulk file before
  looping a live NCBI API call across many genes; catalogs the bulk files
  already used (gene2pubmed, mim2gene_medgen, GeneRIF, HomoloGene, gene_info).

When a new recurring task comes up that's worth not re-deriving next time,
add a new skill folder here rather than relying on session memory — skills
are plain files, so they're the portable option.
