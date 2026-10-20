# Surveillance data quality

A reproducible Python and SQLite project about a practical question: **what information do we actually have before interpreting a surveillance curve?**

## Why this project

**Start here:** [Background, rationale, and key themes](docs/project-context.md). Then read [the biology and concepts](docs/biology-and-concepts.md) for an explanation of the measurements.

The main worked example now uses a pinned **real CDC NREVSS aggregate dataset**. It checks weekly test counts and denominators, quantifies coverage of the requested extraction window, and shows how summaries change when recent weeks are left out. A separate version-history engine demonstrates how to reconstruct reports available by a given date without letting later revisions leak backward.

The original synthetic audit remains as a small, easy-to-inspect test case. The real data and synthetic examples are labeled separately throughout.

## What it does

The public audit verifies the capture contract, preserves absent and suppressed observations, checks count-derived percentages, and compares consecutive test denominators. Separate synthetic examples exercise SQL calendar joins and issue-date revision handling. No epidemiological model is fitted.

## Quick start

You need Python 3.12 or later. No third-party packages or network access are needed for the bundled analyses.

```sh
python src/public_audit.py
python src/vintage_audit.py
python src/audit.py
python -m unittest discover -s tests -v
```

Run these commands from the repository root. The public analysis verifies the pinned file's SHA-256 before reading it. The commands write to three separate output directories.

| Example | Input | What to read |
| --- | --- | --- |
| Real public-data audit | 123 CDC national series-week rows from January 3–October 10, 2026 | [Results and sensitivity analysis](results_public/report.md) |
| As-of report histories | Explicitly synthetic issue dates and revisions | [Vintage analysis](results_vintages/report.md) |
| Basic SQL audit | Explicitly synthetic clinic reports with planted errors | [Basic audit](results/report.md) |

The new preflight prints an aggregate contract check without writing files:

```sh
python src/validate_snapshot.py
```

[Expected preflight output](examples/snapshot_preflight.json) and [the input/output contract](docs/practical-use.md) explain what a passing check means.

## Example results

All **123 requested series-week records** were present and usable in the captured file: 41 weeks for each of three categories. Their count-derived percentages agreed with the source's displayed percentages within two-decimal rounding.

| CDC series | Positive tests / tests in the selected window | Pooled positivity |
| --- | ---: | ---: |
| Adenovirus | 21,057 / 799,289 | 2.634% |
| HMPV | 24,375 / 791,964 | 3.078% |
| PIV | 23,015 / 875,604 | 2.628% |

These are summaries of reported tests. A complete extract does not establish complete laboratory reporting, unique-patient coverage, population prevalence, or clinical validity. Each category keeps its own denominator; counts are never pooled across categories. This is a data-quality worked example, not an outbreak forecast.

![Weekly test positivity from the pinned CDC extract](results_public/weekly_positivity.svg)

The chart shows unsmoothed count ratios. The [trailing-window table](results_public/trailing_window_sensitivity.csv) reports what happens after excluding observations newer than 0, 7, 14, or 28 days before the analysis date. Every window uses the same release. This checks sensitivity to the observation window; it does not reconstruct earlier reporting vintages.

## Practical use and limitations

Use this as a reproducible extraction and review exercise. The [practical guide](docs/practical-use.md) distinguishes automated checks from source and scientific review.

### Inspect changing test denominators

The public audit now reports consecutive-week test-count ratios in each category. By default, it flags absolute changes **greater than 50%** for review. Flags do not exclude data or change validity decisions. The setting is illustrative, not a validated surveillance threshold.

```sh
python src/public_audit.py --denominator-change-threshold 0.2 --output results_denominator_20pct
```

The [week-level diagnostic](results_public/denominator_changes.csv) keeps counts, ratios, signed relative changes, and reasons a comparison was unavailable. Missing weeks are not bridged, and a zero previous denominator produces an undefined ratio. In the pinned extract, all 120 consecutive pairs are evaluable and none crosses the default 50% setting; that does not establish stable testing practices or unbiased reporting.

See [related tools and design choices](docs/tools-and-design-notes.md) for a practical comparison with Carnegie Mellon Delphi's version-aware epidemiological data infrastructure.

### Reconstruct synthetic report histories

The separate `vintage_audit.py` command selects the newest report issued on or before `--as-of`. It distinguishes reports that are not yet due from reports that are due but still absent. Revisions replace earlier counts, including downward corrections. Conflicting same-date versions fail validation, and an invalid newest report stays flagged rather than silently reverting to an older value.

```sh
python src/vintage_audit.py --as-of 2026-10-12 --grace-days 7 --output results_vintage_oct12
```

The included histories are invented. For the October 20 cutoff, eight of nine due slots have usable reports, one is absent, and three selected reports have revisions. The seven-day grace period is a demonstration choice. This is not a measurement of CDC reporting delays.

Mellor and colleagues' [2026 peer-reviewed review](https://doi.org/10.1371/journal.pdig.0001759) explains why reporting dates and backfilled revisions matter when judging surveillance data retrospectively. Our [methods](docs/public-data-methods.md) connect that reasoning to the implementation and make its limits explicit. The published [2026 MMWR NREVSS analysis](https://doi.org/10.15585/mmwr.mm7506a2) also discusses participation and representativeness constraints; this repository does not reproduce that article's results.

### Capture and compare a future release

Fetching is optional and requires an internet connection. The adapter downloads the same defined series and date window into a **new** directory, validates the schema, and records provenance. It refuses to overwrite an earlier capture.

```sh
python src/fetch_public.py --output snapshots/new_capture
python src/public_audit.py --snapshot snapshots/new_capture --output results_new_capture
python src/compare_snapshots.py --old data/public --new snapshots/new_capture --output results_comparison
```

The comparison keeps both releases and reports changed counts, percentages, and availability statuses. We currently include one real capture, so no historical revision rate is claimed. The source `posted` date is release metadata, not a specimen or individual laboratory submission date.

## Documentation

| Guide | What it covers |
| --- | --- |
| [Project context](docs/project-context.md) | Background, rationale, and key themes |
| [Biology and concepts](docs/biology-and-concepts.md) | What respiratory test positivity measures |
| [Public methods and references](docs/public-data-methods.md) | Calculation choices, limitations, and scientific sources |
| [Synthetic SQL methods](docs/methods.md) | Original audit methods and supporting references |
| [Public data dictionary](docs/public-data-dictionary.md) | Aggregate and report-vintage fields |
| [Synthetic dictionary](docs/data-dictionary.md) | Original synthetic clinic schema |
| [Data provenance](data/public/manifest.json) | Exact source query, hashes, timestamp, and reuse note |
| [Practical use](docs/practical-use.md) | Input/output contract, worked use, failure behavior, next steps |
| [Literature review](docs/literature-review.md) | Bounded evidence appraisal and implementation consequences |
| [Search log](docs/search-log.json) | Exact searches, retrieved IDs, and screening decisions |
| [Related tools](docs/tools-and-design-notes.md) | Comparison with Delphi's version-aware data infrastructure |

## Development and reuse

Run `python -m unittest discover -s tests -v`. Tests include malformed manifests, metadata/schema identity, unchanged input files, missing versus zero, duplicate quarantine, revision cutoffs, and undefined denominator ratios. Review [contribution and reproducibility expectations](CONTRIBUTING.md) before adapting the schema.

Source: **CDC NREVSS**. The raw public records are retained unedited and are also available free from the [CDC dataset](https://data.cdc.gov/Laboratory-Surveillance/Percent-positivity-of-respiratory-viruses-by-nucle/rgnm-fkqb). Use of these materials and links does not imply endorsement by CDC, HHS, or the U.S. government. See [CDC's reuse policy](https://www.cdc.gov/other/agencymaterials.html) and the manifest's license note. Repository code uses the MIT license; the synthetic fixtures were generated for this project.
