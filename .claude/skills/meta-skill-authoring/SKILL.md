---
name: meta-skill-authoring
description: Template and conventions for writing a new skill in this Yuexuan knowledge folder (.claude/skills/) — frontmatter format, naming prefixes, body structure, and the git commit/push steps. Use whenever asked to create, add, or write a new Claude Code skill here, or to reorganize/rename an existing one.
---

# How to author a skill in this folder

This distills the pattern already used by `gene-pubmed-count/SKILL.md` (the
first skill in this collection) into a checklist, so every new skill looks
and behaves the same way instead of each one improvising its own shape.

## 1. Naming

- Folder name = `name:` in frontmatter = kebab-case, prefixed by category:
  - `ncbi-*` / `gene-*` — NCBI/PubMed/gene-database queries and lookups
  - `analysis-*` — how to analyze a specific data type/assay
  - `fileformat-*` — how to read/interpret a specific file format
  - `meta-*` — process/authoring skills about Claude Code itself (this one is
    the first)
  - Hit a task that doesn't fit any of these? Pick a new short prefix,
    **and add it to the list above and in `CLAUDE.md`** in the same commit —
    the prefix list is only useful if it stays current.
- Path is always `.claude/skills/<name>/SKILL.md` in this folder (which is
  the git repo root — see §4).

## 2. Frontmatter

```yaml
---
name: <same-as-folder-name>
description: <one sentence, specific enough to semantically match a real future request>
---
```

The `description` is what gets matched against future prompts — this is the
single highest-leverage sentence in the file. Write it as: *what the skill
does* + *when to use it* (a "use whenever ..." clause with concrete trigger
phrasing), not a vague summary. A description that could describe five other
skills equally well will never get picked up automatically.

## 3. Body structure

1. `# Title` matching the skill's purpose.
2. If there's more than one way to do the task, open with the *decision*
   ("N modes/approaches, pick based on X") before diving into either one —
   don't make the reader discover the fork halfway through.
3. For each approach: concrete, runnable material — an actual URL pattern,
   a minimal code snippet, exact field names/positions. Not prose describing
   what *could* be done; the thing to actually do.
4. **If a reference implementation already exists in this Dropbox, point at
   its file path instead of re-describing or re-implementing the logic.**
   (Example: `gene-pubmed-count`'s Mode B points at
   `LRR_searching/LRR_in_iMacs/pubmed_publication_rank.py` rather than
   re-explaining its parsing logic inline.) Skills are meant to save
   re-derivation, not duplicate code that will drift out of sync with it.
5. Close with an explicit decision guide when there was a fork in step 2
   ("use approach A when ..., approach B when ...").

## 4. Saving and publishing it

This whole folder (`/Users/yuexuanyang/.../1_Data/Yuexuan`) is a git repo
mirrored to `git@github.com:yang-yx20/ai-skills.git` (branch `main`). Its
`.gitignore` scopes the repo to **only** `.gitignore`, `CLAUDE.md`, and
`.claude/**` — the rest of this Dropbox folder (lab data, plasmids, meeting
notes, etc.) must never enter this repo.

After writing/editing a skill file:

```bash
cd "/Users/yuexuanyang/Library/CloudStorage/Dropbox-Xiao_Lab_Stanford/Xiao_Lab_Stanford Team Folder/1_Data/Yuexuan"
git add .claude/skills/<name>/SKILL.md CLAUDE.md   # name the files explicitly
git commit -m "Add <name> skill: <one-line summary>"
git push origin main
```

**Never `git add -A` or `git add .` in this repo** — the `.gitignore` comment
says so explicitly, and an accidental broad add here would try to stage
unrelated lab data sitting alongside it in Dropbox.

Also update `CLAUDE.md`'s "Current skills" list with a one-line entry for
the new skill, in the same commit — that list is the human-readable index of
what exists, and it drifting out of sync defeats its purpose.

## 5. Verifying

- `git status` before committing: confirm only the intended files are
  staged.
- After pushing: `git log --oneline -3` locally vs. `git ls-remote origin`
  should show the same HEAD commit hash.
- Sanity-check the `description` by imagining a real future one-line request
  and asking whether it would plausibly match — if it's ambiguous with an
  existing skill's description, tighten both.
