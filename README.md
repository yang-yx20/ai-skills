# ai-skills

A portable set of [Claude Code](https://claude.com/claude-code) **skills**: reusable, plain-text procedures for
recurring bioinformatics tasks, so they don't have to be worked out again in each session or on each machine.

The source of truth is a Dropbox folder (`Xiao_Lab_Stanford Team Folder/1_Data/Yuexuan/`) that syncs across
computers. This git repo mirrors it for machines without Dropbox, such as HPC clusters. Only `CLAUDE.md`,
`README.md` and `.claude/` are tracked; everything else in that folder is lab data and is ignored on purpose.

## Skills

| Skill | What it does | Use it when |
|---|---|---|
| [`gene-pubmed-count`](.claude/skills/gene-pubmed-count/SKILL.md) | Counts PubMed articles linked to a gene, either with a live NCBI `elink` call or from the bulk `gene2pubmed` file | "How many papers are there on gene X?", or ranking/filtering genes by publication count |
| [`ncbi-ftp-bulk-data`](.claude/skills/ncbi-ftp-bulk-data/SKILL.md) | Checks `ftp.ncbi.nlm.nih.gov` for a bulk flat file before looping a live API (catalogs gene2pubmed, mim2gene_medgen, GeneRIF, HomoloGene, gene_info) | Any task that needs NCBI data for more than a handful of genes |
| [`viz-interactive-cluster-html`](.claude/skills/viz-interactive-cluster-html/SKILL.md) | Builds one self-contained interactive HTML (zoom/pan, tooltip, gene search, click-to-isolate clusters, neighbour highlight) for a cluster network or a UMAP/embedding scatter; ships a generic scatter builder | "Make an interactive / clickable HTML of these clusters / this network / this UMAP" |
| [`meta-skill-authoring`](.claude/skills/meta-skill-authoring/SKILL.md) | Template and conventions for writing a new skill here, plus the commit/push steps | Adding or reorganizing a skill |

**Naming prefixes:** `ncbi-*` / `gene-*` for NCBI, PubMed and gene-database lookups; `analysis-*` for how to
analyze an assay; `fileformat-*` for reading a file format; `meta-*` for skills about Claude Code itself; `viz-*` for building a kind of figure or interactive visualization.

## Using it on another machine

```bash
git clone git@github.com:yang-yx20/ai-skills.git
```

Then use either option below.

- **Option A:** open the cloned folder as the Claude Code working directory. `CLAUDE.md` and
  `.claude/skills/` are picked up automatically.
- **Option B:** make the skills available in every project by linking them into your user skills folder:

  ```bash
  mkdir -p ~/.claude/skills
  ln -s "$PWD/ai-skills/.claude/skills/"* ~/.claude/skills/
  ```

To update later, run `git pull`. Edit skills in the Dropbox copy and push from there, so the two copies don't
diverge.

## Adding a skill

1. Follow [`meta-skill-authoring`](.claude/skills/meta-skill-authoring/SKILL.md): create
   `.claude/skills/<prefix>-<name>/SKILL.md` with a specific one-line `description` in the frontmatter. That
   description is what Claude matches against future requests.
2. Add the skill to the list in `CLAUDE.md` and to the table above.
3. Stage only the files you mean to add, then commit and push. **Never use `git add -A` or `git add .`.** The
   `.gitignore` is a whitelist (`*` plus explicit exceptions), so the surrounding lab data can never be
   committed.
