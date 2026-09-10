---
name: ncbi-ftp-bulk-data
description: Before hitting any live NCBI API in a loop for gene/PubMed/OMIM/homology/taxonomy data across many genes, check https://ftp.ncbi.nlm.nih.gov/ for a bulk flat file that already has it — avoids per-item rate limits and is often the authoritative source anyway. Use whenever a task needs NCBI-hosted data for more than a handful of genes.
---

# NCBI FTP first, live API second

NCBI publishes most of what its live E-utilities APIs serve as downloadable
bulk flat files on `https://ftp.ncbi.nlm.nih.gov/`. For anything touching
more than ~10-20 genes, download the relevant file once, cache it locally,
and filter/join in-process — one HTTP request instead of thousands, and no
3-requests/second throttling to work around. Reach for the live API
(`eutils.ncbi.nlm.nih.gov`) only for single ad hoc lookups, or for data that
genuinely isn't published in bulk (e.g. one-off `esummary` title lookups for
a handful of specific IDs).

## Bulk files already used and verified in this Dropbox

| What it gives you | URL | Format notes |
|---|---|---|
| Gene ↔ PubMed article links | `gene/DATA/gene2pubmed.gz` | tab-sep, columns `tax_id, GeneID, PubMed_ID`; filter `tax_id==9606` for human. Used by `gene-pubmed-count` skill Mode B and `LRR_searching/LRR_in_iMacs/pubmed_publication_rank.py`. |
| Gene ↔ OMIM MIM number mapping | `gene/DATA/mim2gene_medgen` | tab-sep, columns `MIM number, GeneID, type, Source, MedGenCUI, Comment`. `type` is `gene`, `phenotype`, or `gene/phenotype` — only `phenotype`/`gene/phenotype` rows are an actual disease association; a `gene`-type row is just the gene's own locus entry, not a disease. |
| GeneRIF one-sentence function summaries | `gene/GeneRIF/generifs_basic.gz` | tab-sep, columns `#Tax ID, Gene ID, PubMed ID (PMID) list, last update timestamp, GeneRIF text`. `PubMed ID list` is `|`-delimited if there's more than one PMID per GeneRIF — take the first for a single citation link. This is a human-curated one-liner, **not** the paper's abstract. |
| Symbol ↔ GeneID mapping, human | `gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz` | tab-sep, NCBI's own gene_info format (`GeneID`, `Symbol`, `Synonyms`, ...). |
| Cross-species ortholog groups (HomoloGene) | `pub/HomoloGene/build68/homologene.data` | tab-sep, columns `HID (group), TaxID, GeneID, Symbol, ProteinGI, ProteinAccession`. **NCBI retired the live HomoloGene database and its web UI** (`ncbi.nlm.nih.gov/homologene/<id>` now 301s to an unrelated page) — this frozen build 68 (2014) snapshot is the only way to get this data at all now. Build 68 covers ~21 reference organisms end-to-end (human, primates, common mammals/birds/fish, a few invertebrates, plants, and fungi/yeast) — check which taxids actually appear before assuming a species is covered. |

Each row above is a real, already-validated example from the LRR-333
characterization project (`LRR_searching/Rensvold et al. 2022
Nature_parody/`) — the scripts there (`classify_lrr_characterization.py`,
`build_lrr_wordclouds.py`, `build_interactive_wordclouds.py`) show the full
download+parse+cache pattern for each of these four files if a worked
example is more useful than the table.

## Finding a dataset not in the table above

Browse the FTP tree directly before assuming something isn't published in
bulk:
- `https://ftp.ncbi.nlm.nih.gov/` — top-level directory listing
- `https://ftp.ncbi.nlm.nih.gov/gene/DATA/` — most gene-centric bulk files
  live here (also has RefSeq, GO, and more `GENE_INFO/<taxonomic-group>/`
  subfolders for non-human organisms)
- `https://ftp.ncbi.nlm.nih.gov/pub/` — everything else NCBI publishes
  (taxonomy dumps, HomoloGene, RefSeq, PMC, ClinVar, dbSNP, etc.), organized
  by resource name

## Caching rule

Download once into a local cache directory, keyed by filename; only
re-download if the cached copy is missing, or the user explicitly wants a
fresh snapshot (these files range from under 1 MB to ~100+ MB and are slow
to re-fetch for no reason). This is the same rule `gene-pubmed-count` Mode B
already documents for `gene2pubmed.gz` — apply it to every file in the table
above, not just that one.
