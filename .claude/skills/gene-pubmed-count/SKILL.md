---
name: gene-pubmed-count
description: Count how many PubMed articles are linked to a gene via NCBI's gene_pubmed link (elink.fcgi), for one gene or in bulk across many genes. Use whenever the user asks "how many papers/publications on gene X" or wants to rank/filter genes by publication count.
---

# Gene → PubMed publication count

Two modes. Pick based on how many genes are being asked about.

## Mode A — single gene, ad hoc (live elink)

For one gene (or a handful), call NCBI's `elink.fcgi` directly and count the
returned PubMed IDs. No download needed.

```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi
    ?dbfrom=gene&db=pubmed&id={geneid}&linkname=gene_pubmed
    &tool=claude-code&email={your_email}
```

`{geneid}` must be an NCBI **Entrez Gene ID** (a number), not a gene symbol. If
the user gives a symbol (e.g. `EGFR`), resolve it first:

```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
    ?db=gene&term={symbol}[sym]+AND+human[orgn]&retmode=json
    &tool=claude-code&email={your_email}
```
→ take `esearchresult.idlist[0]` as the gene ID.

Then count the `<Id>` elements inside the `<LinkSetDb>` whose `<LinkName>` is
`gene_pubmed` in the elink XML response. Minimal example:

```python
import urllib.request
import xml.etree.ElementTree as ET

EMAIL = "your_email@example.com"  # ask the user for one if it matters to them

def gene_pubmed_count(gene_id: int) -> int:
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
        f"?dbfrom=gene&db=pubmed&id={gene_id}&linkname=gene_pubmed"
        f"&tool=claude-code&email={EMAIL}"
    )
    with urllib.request.urlopen(url) as resp:
        root = ET.fromstring(resp.read())
    for linkset_db in root.iter("LinkSetDb"):
        if linkset_db.findtext("LinkName") == "gene_pubmed":
            return len(linkset_db.findall("Link"))
    return 0
```

NCBI etiquette: without an API key, stay at ≤3 requests/second; with one
(`&api_key=...`), ≤10/second. For more than ~10-20 genes, switch to Mode B
instead of looping this call — it's both faster and avoids rate limits.

## Mode B — many genes / bulk ranking (local gene2pubmed cache)

For batches of genes (tens to genome-wide), download NCBI's bulk
`gene2pubmed.gz` once, cache it locally, and count from that file instead of
hitting the API per gene.

Reference implementation already in this Dropbox:
`LRR_searching/LRR_in_iMacs/pubmed_publication_rank.py` — it:
1. Downloads and caches `gene2pubmed.gz`
   (`https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2pubmed.gz`) and
   `Homo_sapiens.gene_info.gz` (for symbol ↔ GeneID mapping).
2. Filters `gene2pubmed` to `tax_id == 9606` (human) and counts unique PMIDs
   per `gene_id` (`human_pub_counts()` in that file).
3. Cross-checks a handful of genes against live elink counts (see the
   `EXPECTED` dict in that script) as a sanity check — counts drift over time
   as NCBI adds text-mining-derived links, so don't expect exact matches to
   old snapshots, only the same order of magnitude and consistent ranking.

Reuse that script's `fetch()` / `human_pub_counts()` pattern rather than
re-downloading or re-implementing the parsing logic. Re-download the gzip
only if the cached copy is missing or the user explicitly wants a fresh
snapshot (the file is ~35M rows and slow to re-fetch/parse).

## Choosing a mode

- 1-10 genes, one-off question → Mode A (simpler, always current).
- Many genes, ranking, or repeated queries over time → Mode B (cache pays
  for itself after the first run, and avoids NCBI rate limits).
