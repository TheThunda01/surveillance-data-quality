# Original synthetic site-week data dictionary

This page describes only `data/calendar.csv`, `data/reports.csv`, and `data/reports_clean.csv`, the original synthetic site-week example. In those files, `demo_A`, `demo_B`, and `demo_C` are invented labels. The separate [public and report-vintage data dictionary](public-data-dictionary.md) documents the real CDC extract and the synthetic version-history fixture.

| File / field | Type and rule | Meaning |
| --- | --- | --- |
| Both: `site_id` | Nonblank text; exact match to calendar | Fictional reporting site |
| Both: `week_start` | `YYYY-MM-DD`, Monday | First date of seven-day reporting interval |
| Reports: `positive_tests` | Nonnegative base-10 integer | Positive test results from the denominator's pool |
| Reports: `tests_performed` | Nonnegative base-10 integer; at least positive_tests | Tests in the same site-week pool |
| Reports: `reported_on` | `YYYY-MM-DD`; on or after week end | Submission date for this version of the aggregate report |

Files must have exactly the named columns. Blank counts, decimals, signed values, leading zeros, and surrounding spaces in counts are rejected rather than interpreted. Integers must fit SQLite's signed 64-bit integer range. No patient-level columns are included or expected.

The calendar must have unique keys. The reporting table may contain duplicate keys so the audit can show them, but all such rows are quarantined. Unknown site-week keys are flagged. If a malformed reporting-week value cannot match the calendar, the intended slot can also appear missing; the tool does not infer which week was intended.

## Outputs

`slots.csv` contains one row per expected key. `status` is `missing`, `invalid`, or `usable`; count fields are blank when unusable. Zero tests are valid and produce blank positivity. `delay_days` is `reported_on − (week_start + 6 days)` and appears only for usable rows.

`findings.csv` contains one row per finding. `row` is the header-plus-record index in the original comma-separated values (CSV) file. It matches the physical line for this fixture; quoted multiline records can differ. `error` excludes that input row from summaries; `review` flags a late usable report. Multiple errors may belong to one row.

`audit.json` includes the same tables, summary counts, a method label, and SHA-256 checksums (file fingerprints) of the inputs. JSON uses `null` where a ratio or delay is undefined. `usable_fraction` is $`\frac{\text{usable expected slots}}{\text{expected slots}}`$. `pooled_positivity` is a proportion between zero and one, not a percentage; multiply by 100 for display.

Open exported CSVs as data, not executable spreadsheet formulas, when adapting this tool to arbitrary external identifiers. The demo identifiers contain no formulas.

See the [glossary](glossary.md) for computing and statistical terms, and [assumptions](assumptions.md) for the expected calendar and reporting-delay definitions.
