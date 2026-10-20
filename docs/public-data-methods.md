# Public data, report vintages, and what the checks mean

The [practical-use contract](practical-use.md) now documents a read-only preflight for the public snapshot. Before parsing observations, the loader checks the manifest's supported source endpoints, UTC capture timestamp, selection, exact byte length/digests, and captured metadata identity/columns. This detects contract mismatches; it does not authenticate edited files or establish complete surveillance. The [bounded evidence review](literature-review.md) records the rationale and inspected sources.

## The question

Can a small, reproducible audit make the observation window, available reports, and test denominators visible before anyone interprets a surveillance curve?

There are two complementary analyses here. The public-data analysis checks one downloaded release of CDC aggregate laboratory results. The report-vintage analysis checks what was available by different dates in an explicitly synthetic version history. The second does not manufacture historical versions of the first.

## Real public-data source

The source is CDC's **Percent positivity of respiratory viruses by nucleic acid amplification tests (NAATs), as reported on the National Respiratory and Enteric Virus Surveillance System (NREVSS) Dashboard**, Socrata identifier `rgnm-fkqb` [1]. The pinned file contains national, Combined Type records for Adenovirus, HMPV, and PIV, for the 41 Saturday-ending weeks from January 3 through October 10, 2026. It was retrieved on October 20, 2026. These three series were chosen because this selection supplies explicit counts and a reported percentage; this is a workflow case study, not a representative sample of every NREVSS product.

The raw API response is retained without editing. The manifest records the exact filtered URL, retrieval time, byte length, SHA-256, date window, and category selection. A compact metadata capture records source column definitions and access metadata. The source's `licenseId` is unset; no dataset-specific Creative Commons license is invented. CDC's agency-materials policy describes public-domain reuse with exceptions and requires attribution and a non-endorsement notice [4]. The original records are freely available from the linked source. The MIT license covers this repository's code, not a new license imposed on CDC data.

## Audit rules and denominators

One expected record is one selected series-week. The calendar comes from the declared date window, not from whichever rows happened to be returned. Counts must be nonnegative integers, detections cannot exceed tests, and duplicate series-week keys are quarantined. `*` remains suppressed and `.` remains unavailable; neither is treated as zero. Percentages computed from counts must agree with the source percentage within 0.005 percentage points, allowing two-decimal rounding. No outlier cutoff removes biologically plausible values.

Coverage is usable series-weeks / expected series-weeks **within this extract**. It is not the fraction of all laboratories reporting, patients tested, infections detected, or the population represented. A complete-looking national row may aggregate incomplete or selectively submitted laboratory data. CDC describes NREVSS as voluntary, with provisional data, changes to participation and testing, and possible repeated specimens from a person [1]. Consequently, positivity is a proportion of reported tests, not population prevalence. The 2026 MMWR analysis likewise discusses representativeness limits of NREVSS [3].

Pooled positivity is `100 × sum(detections) / sum(tests)` separately for each series. Pooling across the three series could double count tests or people and is not performed. A zero test denominator yields an undefined ratio. Arithmetic agreement checks do not establish clinical accuracy or representativeness.

## Trailing-window sensitivity

The public analysis repeats the summary after excluding observations newer than 0, 7, 14, or 28 days before its analysis date. It reports the number of eligible weeks, the retained test-denominator fraction, and the change in pooled positivity in percentage points. These choices illustrate a reproducible sensitivity analysis; they are not recommended universal delay corrections.

Every window uses the same downloaded release. Excluding recent observation weeks does **not** reconstruct the data available on a past date. The tool refuses an `--as-of` date before this snapshot's capture date to avoid that interpretation. Its `posted` column is release metadata, not an individual specimen date or laboratory receipt time. It therefore cannot estimate laboratory reporting-delay distributions from this single file.

## Consecutive-week denominator changes

A review diagnostic compares test counts only when consecutive calendar weeks are usable in the same series and the previous count is positive. The signed relative change is `(current tests − previous tests) / previous tests`. Its absolute value is compared strictly with a configurable threshold, default 0.5. This is a transparent demonstration setting, not a validated universal standard. It does not remove records, alter their validity status, estimate incidence, or explain why a denominator changed. Missing or suppressed weeks are not bridged, and zero previous denominators yield an undefined ratio. The output reports both counts so a flagged change can be investigated in context.

## Genuine as-of selection and revision comparison

`vintage_audit.py` accepts a separate table with an explicit `issued_on` for each full replacement report. It selects the newest version issued on or before the requested date and excludes later versions. A revised count is a replacement, not an additional count; downward corrections are allowed. Two records with the same key and issue date are ambiguous and fail validation. An invalid newest version is flagged rather than silently replaced with an older, valid-looking value.

A configurable grace period defines when an expected slot is due. Before that deadline it is `not_due`; after it, absence is `not_yet_available`. These are reporting statuses, not zero observations. The shipped version history is wholly synthetic and does not describe CDC reporting performance.

For real future releases, `compare_snapshots.py` compares two pinned, verified extracts with the same selection and ordered capture times. It flags changed values, status changes, and signed count differences. It cannot identify changes that happened between the captures. We currently ship only one real release and claim no measured historical revision rate.

The distinction between observation time and information availability follows Mellor and colleagues' 2026 narrative review: reporting delays and backfilled revisions can make retrospective surveillance analyses appear more useful than the data would have been in real time [2]. That paper motivates this design; it does not validate our software or supply a delay model for these records.

## References and their roles

1. Centers for Disease Control and Prevention. [NREVSS aggregate NAAT dataset and data notes](https://data.cdc.gov/Laboratory-Surveillance/Percent-positivity-of-respiratory-viruses-by-nucle/rgnm-fkqb). Retrieved October 20, 2026. **Role:** actual input data, category definitions, missing-value notation, and source limitations.
2. Mellor J, Tang M, Paton RS, Ward T. Recommendations for the analysis of leading indicators in epidemic surveillance. *PLOS Digital Health*. 2026;5(10):e0001759. [doi:10.1371/journal.pdig.0001759](https://doi.org/10.1371/journal.pdig.0001759). Published October 5, 2026. **Role:** peer-reviewed methodological context for reporting dates, revisions, and retrospective interpretation. This project does not implement a leading-indicator or forecast model.
3. Silk BJ, Prill MM, Winn AK, et al. Respiratory Virus Activity — United States, July 1, 2024–June 30, 2025. *MMWR Morbidity and Mortality Weekly Report*. 2026;75:77–84. [doi:10.15585/mmwr.mm7506a2](https://doi.org/10.15585/mmwr.mm7506a2). **Role:** current published context for NREVSS surveillance and representativeness limitations. Its study period differs from this repository's data window; our output is not a reproduction of its results.
4. Centers for Disease Control and Prevention. [Use of Agency Materials](https://www.cdc.gov/other/agencymaterials.html). Accessed October 20, 2026. **Role:** reuse, attribution, and non-endorsement guidance; not a claim of a dataset-specific license.
