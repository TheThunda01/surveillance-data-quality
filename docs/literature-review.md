# Rapid evidence and practice review — 2026-10-20

## Question and scope

What checks make a small, release-aware public surveillance audit easier to inspect and reuse without implying that complete-looking rows establish complete population surveillance? This bounded rapid review focuses on observation definitions, reporting revisions, and source metadata. It is not a systematic review of all surveillance methods, and it does not select an outbreak model.

### Round 2 update — same date, narrower implementation question

On 2026-10-20, the second pass asked how to make failures and row-review findings reusable by another script. This is a new software-contract question on the same inputs, not another surveillance period or data release. The original search record is preserved; the new record is [search-update-02.json](search-update-02.json).

## Search record

PubMed was searched first on 2026-10-20 with publication dates 2022/01/01–2026/10/20 and relevance sorting. The exact queries were:

- `"epidemic surveillance"[Title/Abstract] AND ("reporting delays"[Title/Abstract] OR "data revisions"[Title/Abstract])`: 5 reported results, all 5 returned at offset 0.
- `"Respiratory Virus Activity"[Title] AND "United States"[Title]`: 1 reported result, returned at offset 0.

All six unique records were screened using title/abstract metadata. Three were retained for this implementation decision. The first 24,000 full-text characters of each retained paper were obtained through PMC; all three responses were truncated. The accessible methods and rationale were appraised, but supplementary files and full reference trails were not comprehensively reviewed. The exact retrieval and exclusion decisions are in [search-log.json](search-log.json).

Supplementary inspection used the pinned CDC source metadata and the official Delphi repository at a resolved commit. These were targeted source lookups, not a web search with a known total result count.

### Round 2 retrieval

PubMed query `surveillance[Title] AND "data quality"[Title] AND (framework[Title] OR validation[Title])`, with publication dates 2022/01/01–2026/10/20, relevance sort, offset 0, and maximum 20 results, returned one record: PMID 38870031. It was screened and retained. The first 30,000 of 34,784 PMC full-text characters were returned; appraisal used the accessible workflow and results sections, without a supplementary review. RFC 9457 sections 1 and 3.1 were inspected as an official design source. Two attempts to access the Frictionless validation-report specification failed; no claims were drawn from that unavailable source.

## What the sources support

| Source | Type and access | Useful finding | Limit | Consequence here |
| --- | --- | --- | --- | --- |
| [Mellor et al., 2026, PMID 42832413](https://pubmed.ncbi.nlm.nih.gov/42832413/) | Peer-reviewed narrative methods review; partial PMC full text | Retrospective surveillance analysis should state coverage, reporting delays, and revisions. | Recommendations are not a validation of this dataset or software. | Keep capture timestamps explicit and retain the distinction between observation windows and historical availability. |
| [Tang et al., 2025, PMID 41264651](https://pubmed.ncbi.nlm.nih.gov/41264651/) | Peer-reviewed revision-forecasting methods study; partial PMC full text | Numerator and denominator revisions can behave differently, including changes in fractions in either direction. | Their forecasting experiments use different streams; those performance results do not transfer here. | Preserve counts separately and retain snapshot identity; no forecasting method was imported. |
| [Silk et al., 2026, PMID 41712508](https://pubmed.ncbi.nlm.nih.gov/41712508/) | Primary national surveillance report; partial PMC full text | NREVSS includes voluntary weekly aggregate laboratory reporting. | Its reporting period and laboratory inclusion differ from this 2026 extract. | Report extract coverage without relabelling it laboratory participation or population prevalence. |
| [CDC source metadata](../data/public/source_metadata.json), [capture manifest](../data/public/manifest.json) | Official primary dataset metadata, locally pinned and inspected | Records identify the dataset, named fields, and weekly update frequency. | A local digest detects divergence from that manifest, not authenticity or accuracy. | Validate metadata identity, fields, SHA-256, byte length, and supported selection in `snapshot_contract.py` and `load_snapshot`. |
| [Delphi V5 documentation](https://github.com/cmu-delphi/delphi-epidata/blob/603969199277177c2e3c612b13fa732f1698f99c/docs/api/v5.md) | Official repository docs, commit `603969199277177c2e3c612b13fa732f1698f99c`; full target file and MIT license inspected | Archive and snapshot endpoints explicitly distinguish changed rows from data available at a time. | This project does not implement Delphi's database, API, source coverage, or operational service. | Make the single-capture boundary visible and validate metadata before comparison. No code copied. |

The implementation inference is modest: require an explicit supported input contract before running the existing calculations. The literature motivates transparent data roles; it does not prescribe our exact schema, date parser, or thresholds.

### Round 2 source-to-change appraisal

| Source | Type and access | Finding relevant here | Limit | Implementation consequence |
| --- | --- | --- | --- | --- |
| [Hohman et al., 2024, PMID 38870031](https://pubmed.ncbi.nlm.nih.gov/38870031/) | Primary MENDS validation-process study; partial PMC full text | The workflow documented source and transformation problems and revisited them with data contributors. | Chronic-disease EHR surveillance differs from this aggregate laboratory extract; the study does not validate our taxonomy. | Keep distinguishable findings with explicit location and severity, so another reviewer can investigate them. |
| [RFC 9457, July 2023](https://www.rfc-editor.org/rfc/rfc9457.html) | Official IETF specification; selected sections inspected | A machine problem identifier is separate from human-readable detail. | Applies to HTTP APIs; our CLI is not RFC-conformant and imports no standard code. | Assign stable codes at the failing check instead of parsing message text. |

The choice of individual codes and severity levels is an engineering decision tested against this repository's actual failure cases, not a scientific conclusion supplied by either source.

## Changes made

Added `snapshot_contract.py` and a read-only `validate_snapshot.py` command. The existing public loader now applies the same manifest checks and validates the captured metadata identity and field list. A valid manifest with missing or invalid observations returns counts requiring review; malformed input fails with a clear nonzero exit. Tests cover incorrect metadata even when its replacement digest matches, required source-page identity, bad endpoint/scope/date/types, release dates after capture, and unchanged input bytes. The [practical-use contract](practical-use.md) documents both the checks and their limits. Existing data and result files are preserved.

### Round 2 implementation

Added the optional `--diagnostics-json` envelope, a machine-readable code catalog and exact-version JSON Schema. Typed exceptions cover manifest, identity, file integrity, chronology, JSON, CSV and scope failures. Completed row audits expose missing, suppressed, unavailable, duplicate, invalid-value and zero-denominator findings without changing existing totals or exclusion rules. Default output remains available. Regression tests exercise actual failing inputs, CLI exit behavior, and missing-versus-zero semantics. See the [diagnostic contract](diagnostics.md).

## Remaining work

Priority remains obtaining actual repeated releases, testing supported schema migrations, and documenting eligible laboratory denominators if public definitions become available. These would add evidence that a one-release audit cannot supply. Acceptance criteria are in [practical-use.md](practical-use.md#next-improvements).

### Round 2 status

The prior machine-readable-taxonomy task is implemented. A downstream consumer and real repeated captures remain future work, with acceptance criteria in [practical-use.md](practical-use.md#next-improvements). No new surveillance inference is enabled by the JSON envelope.

## Limits of this review

One reviewer performed a narrow, English-query search in one bibliographic database. No independent duplicate screening, formal risk-of-bias scoring, citation chasing, or comprehensive supplementary review was performed. Retrieved full texts were partial; claims above are confined to the inspected sections. Search counts describe the returned records, not the whole surveillance literature. Official code/documentation inspection is an implementation comparison, not scientific validation or endorsement.

### Round 2 limits

This was one narrow PubMed query and targeted official-document inspection, with one reviewer and truncated full text. It is not an updated systematic review, a completeness certification, or independent validation of the software. No new source snapshot or biological data were collected.
