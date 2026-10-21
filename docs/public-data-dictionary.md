# Public and vintage data dictionaries

## Pinned real CDC extract

`data/public/nrevss_national_2026.csv` is the unedited CSV returned by the filtered API URL in `manifest.json`.

| Field | Meaning and treatment |
| --- | --- |
| `mmwrweek_end` | Saturday ending the source-assigned surveillance reference week. Its midnight-valued calendar field is used as a date, not an exact testing time. The project does not infer individual collection or testing dates. |
| `level` | Must equal `National` for this selection. |
| `state` | Blank for this national selection; no state inference is made. |
| `pathogen` | Source category; the bundled selection contains Adenovirus, human metapneumovirus (HMPV), and parainfluenza viruses (PIV). |
| `subtype` | Must equal `Combined Type`; individual subtypes are not pooled by this program. |
| `tests` | Reported nucleic acid amplification test (NAAT) count, not unique patients. |
| `detections` | Reported positive count corresponding to the test pool. |
| `percent_pos` | Source percentage, checked against $`100\,\frac{\text{detections}}{\text{tests}}`$ with rounding tolerance. |
| `posted` | Treated by this adapter as a release/update date. The captured metadata identify a calendar field without a complete semantic definition. Never used as an individual reporting delay. |
| `tests_3wma`, `detections_5wma`, `percent_pos_3wma` | Preserved source columns. Not used or substituted for raw counts in this analysis. |

`*` is suppressed; `.` is unavailable. A blank required value is also unavailable. All are retained as missing information, not filled with zero. The selected frozen rows contain usable unsuppressed counts, but tests exercise both missing-value pathways.

### Generated public audit columns

`status` is `usable`, `absent_from_extract`, `suppressed`, `unavailable`, or `invalid`. `source_line` identifies the header-plus-record index in the original comma-separated values (CSV) file. It matches the physical line for this single-line-record fixture; a quoted multiline record can differ. `percent_difference_pp` is the absolute arithmetic difference in percentage points. Values from an invalid record remain visible for review but never enter pooled summaries.

`usable_week_coverage` measures coverage of the declared series-week grid only. `retained_test_denominator_fraction` compares tests remaining after a trailing-window exclusion with tests in the full usable window, within the same series and same release. It is not population or laboratory coverage.

## Synthetic report-vintage fixture

`data/vintage_demo.csv` contains invented report histories. `data/vintage_expected.csv` is its expected site-week grid. It is separate from CDC data.

| Field | Rule |
| --- | --- |
| `site_id` | Fictional reporting site; must exist in the expected calendar. |
| `week_end` | Saturday ending the observation week. |
| `issued_on` | Date that this full replacement report became available. Must be on or after week end. |
| `positive_tests`, `tests_performed` | Nonnegative integer counts; positivity uses matching numerator and denominator. |

The key of a version is `(site_id, week_end, issued_on)`. Multiple versions on different dates are expected. Duplicate keys on the same date fail instead of being arbitrarily ordered. The `source_line` is the header-plus-record index of the selected version, so changing input row order changes that locator but not numerical results.

For each cutoff, `available_versions` counts only issued versions on or before it. `first_delay_days` and `selected_delay_days` are defined only from those available versions. `revision_*_delta` compares the selected version with the first available version when both have valid counts and can be negative. A delta is a difference; a negative correction is not a negative test count. No future values enter the calculation. $`\text{due\_on}=\text{week\_end}+\text{grace\_days}`$; grace is an explicit user choice.

## Consecutive-week denominator diagnostics

`results_public/denominator_changes.csv` compares each usable week with exactly the previous calendar week in the same category. `test_count_ratio` is $`\frac{\text{current tests}}{\text{previous tests}}`$; `relative_test_count_change` is $`\frac{\text{current}-\text{previous}}{\text{previous}}`$. The flag uses the absolute relative change and is strict: exactly 50% does not exceed a 0.5 threshold. It is a review aid, not a validity judgment or exclusion rule.

`diagnostic_status` distinguishes evaluated pairs, no preceding calendar week, an unusable current or previous week, and a zero previous test count. Undefined ratios and flags remain blank in CSV and null in JSON. The series-level summary reports evaluable and flagged pair counts; unevaluable pairs are not silently counted as unflagged observations.

Source identities and notation are documented in [references](references.md); limits of the source-field verification are in the [reference audit](reference-audit.json). See [assumptions](assumptions.md) for date interpretations and [glossary](glossary.md) for vocabulary.
