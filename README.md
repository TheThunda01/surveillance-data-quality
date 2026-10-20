# Surveillance data quality

A small Python and SQLite project about a practical question: **what can we safely summarize when a weekly reporting table is incomplete or inconsistent?**

The included data are entirely synthetic. The clinics, test results, dates, and planted errors are invented for this demonstration. This is a completed software example, not an analysis of a real surveillance system.

## Run it

You need Python 3.12 or later. There are no packages to install and the analysis makes no network requests.

```sh
python src/audit.py
python -m unittest discover -s tests -v
```

Run these commands from this repository's root. The first command audits `data/reports.csv` against `data/calendar.csv` and writes four files into `results/`. To compare the clean fixture:

```sh
python src/audit.py --reports data/reports_clean.csv --output results_clean
```

The `clean` fixture has no invalid rows; its deliberately late report remains a review item. To rebuild both input examples from their deterministic recipe, run `python src/generate_demo.py`. This overwrites the bundled fixtures, so keep your own files elsewhere.

## What the demo shows

| Check | Result in the bundled example |
| --- | --- |
| Expected site-weeks | 12 |
| Site-weeks with at least one submitted row | 11 |
| Missing site-weeks | 1 |
| Invalid site-weeks | 4 |
| Usable site-weeks | 7 |
| Excluded input rows | 5 |
| Usable reports flagged as late | 1 |
| Positive tests / tests in usable records | 14 / 360, or 3.89% |

The duplicate site-week contributes two excluded rows but only one invalid site-week. That distinction is intentional. The example also includes a valid zero-positive report, a valid zero-test report, and one absent report. Those are three different situations.

The 3.89% figure describes the usable synthetic test results only. It does not estimate disease prevalence, evaluate a diagnostic test, or tell us anything about an actual population.

## How it works

Python checks the CSV schema, dates, counts, expected keys, and duplicate keys before passing the rows to SQLite. The SQL files are part of the analysis, not decorative examples: they create the tables, join submitted records to the expected calendar, and pool the usable counts.

- `calendar.csv` defines which site-week reports should exist. Missing submissions are found with a left join.
- Invalid rows are quarantined from numerical summaries. Every row sharing a duplicated key is excluded; the script never guesses which version is correct.
- `positive_tests` must be between zero and `tests_performed`. This is a rule for this toy laboratory-report schema; not every real surveillance case definition has this relationship.
- Positivity is the sum of positive tests divided by the sum of tests across usable records. It is not an unweighted mean of site percentages. A zero denominator produces `null`, not zero.
- Delay is measured from the end of the reporting week to submission. The seven-day late flag is an example setting, not an evidence-based performance standard.

CDC's evaluation guidance treats completeness, validity, and timeliness as distinct surveillance considerations. WHO's dashboard documentation illustrates why test-positivity summaries need clearly matched numerator and denominator definitions. The [methods and sources](docs/methods.md) explain how those ideas inform this example and where the analogy stops.

## Read the outputs

- [Human-readable report](results/report.md)
- [Expected site-week status table](results/slots.csv)
- [Row-level findings](results/findings.csv), with source CSV line numbers
- [Machine-readable audit and SHA-256 input fingerprints](results/audit.json)

See the [data dictionary](docs/data-dictionary.md) before using your own aggregate table. For a custom run, pass `--reports`, `--calendar`, and a separate `--output` directory. Inspect findings before making corrections; a passing audit only means these programmed checks found no problem.

## What this demonstrates

CSV validation, defensive parsing, relational joins, explicit denominators, missingness handling, reproducible audit records, command-line software, and tests that exercise analytical failure modes.

This is a focused portfolio project. It does not implement case ascertainment, nowcasting, outbreak detection, record linkage, patient privacy review, or deployment controls. Real data require local definitions and governance before this workflow could be adapted.

Code is offered under the repository's MIT license. The synthetic fixtures were generated for this project; they are not copied from CDC or WHO.
