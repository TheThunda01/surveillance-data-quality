# Rapid evidence and practice review — 2026-10-20

## Question and scope

What checks make a small, release-aware public surveillance audit easier to inspect and reuse without implying that complete-looking rows establish complete population surveillance? This bounded rapid review focuses on observation definitions, reporting revisions, and source metadata. It is not a systematic review of all surveillance methods, and it does not select an outbreak model.

## Search record

PubMed was searched first on 2026-10-20 with publication dates 2022/01/01–2026/10/20 and relevance sorting. The exact queries were:

- `"epidemic surveillance"[Title/Abstract] AND ("reporting delays"[Title/Abstract] OR "data revisions"[Title/Abstract])`: 5 reported results, all 5 returned at offset 0.
- `"Respiratory Virus Activity"[Title] AND "United States"[Title]`: 1 reported result, returned at offset 0.

All six unique records were screened using title/abstract metadata. Three were retained for this implementation decision. The first 24,000 full-text characters of each retained paper were obtained through PMC; all three responses were truncated. The accessible methods and rationale were appraised, but supplementary files and full reference trails were not comprehensively reviewed. The exact retrieval and exclusion decisions are in [search-log.json](search-log.json).

Supplementary inspection used the pinned CDC source metadata and the official Delphi repository at a resolved commit. These were targeted source lookups, not a web search with a known total result count.

## What the sources support

| Source | Type and access | Useful finding | Limit | Consequence here |
| --- | --- | --- | --- | --- |
| [Mellor et al., 2026, PMID 42832413](https://pubmed.ncbi.nlm.nih.gov/42832413/) | Peer-reviewed narrative methods review; partial PMC full text | Retrospective surveillance analysis should state coverage, reporting delays, and revisions. | Recommendations are not a validation of this dataset or software. | Keep capture timestamps explicit and retain the distinction between observation windows and historical availability. |
| [Tang et al., 2025, PMID 41264651](https://pubmed.ncbi.nlm.nih.gov/41264651/) | Peer-reviewed revision-forecasting methods study; partial PMC full text | Numerator and denominator revisions can behave differently, including changes in fractions in either direction. | Their forecasting experiments use different streams; those performance results do not transfer here. | Preserve counts separately and retain snapshot identity; no forecasting method was imported. |
| [Silk et al., 2026, PMID 41712508](https://pubmed.ncbi.nlm.nih.gov/41712508/) | Primary national surveillance report; partial PMC full text | NREVSS includes voluntary weekly aggregate laboratory reporting. | Its reporting period and laboratory inclusion differ from this 2026 extract. | Report extract coverage without relabelling it laboratory participation or population prevalence. |
| [CDC source metadata](../data/public/source_metadata.json), [capture manifest](../data/public/manifest.json) | Official primary dataset metadata, locally pinned and inspected | Records identify the dataset, named fields, and weekly update frequency. | A local digest detects divergence from that manifest, not authenticity or accuracy. | Validate metadata identity, fields, SHA-256, byte length, and supported selection in `snapshot_contract.py` and `load_snapshot`. |
| [Delphi V5 documentation](https://github.com/cmu-delphi/delphi-epidata/blob/603969199277177c2e3c612b13fa732f1698f99c/docs/api/v5.md) | Official repository docs, commit `603969199277177c2e3c612b13fa732f1698f99c`; full target file and MIT license inspected | Archive and snapshot endpoints explicitly distinguish changed rows from data available at a time. | This project does not implement Delphi's database, API, source coverage, or operational service. | Make the single-capture boundary visible and validate metadata before comparison. No code copied. |

The implementation inference is modest: require an explicit supported input contract before running the existing calculations. The literature motivates transparent data roles; it does not prescribe our exact schema, date parser, or thresholds.

## Changes made

Added `snapshot_contract.py` and a read-only `validate_snapshot.py` command. The existing public loader now applies the same manifest checks and validates the captured metadata identity and field list. A valid manifest with missing or invalid observations returns counts requiring review; malformed input fails with a clear nonzero exit. Tests cover incorrect metadata even when its replacement digest matches, required source-page identity, bad endpoint/scope/date/types, release dates after capture, and unchanged input bytes. The [practical-use contract](practical-use.md) documents both the checks and their limits. Existing data and result files are preserved.

## Remaining work

Priority remains obtaining actual repeated releases, testing supported schema migrations, and documenting eligible laboratory denominators if public definitions become available. These would add evidence that a one-release audit cannot supply. Acceptance criteria are in [practical-use.md](practical-use.md#next-improvements).

## Limits of this review

One reviewer performed a narrow, English-query search in one bibliographic database. No independent duplicate screening, formal risk-of-bias scoring, citation chasing, or comprehensive supplementary review was performed. Retrieved full texts were partial; claims above are confined to the inspected sections. Search counts describe the returned records, not the whole surveillance literature. Official code/documentation inspection is an implementation comparison, not scientific validation or endorsement.
