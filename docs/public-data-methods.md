# Public data, report vintages, and what the checks mean

The [practical-use contract](practical-use.md) documents a read-only preflight for the public snapshot. Before parsing observations, the loader checks the manifest's supported source endpoints, UTC capture timestamp, selection, exact byte length/digests, and captured metadata identity/columns. This detects contract mismatches; it does not authenticate edited files or establish complete surveillance. The [bounded evidence review](literature-review.md) records the rationale and inspected sources.

## The question

Can a small, reproducible audit make the observation window, available reports, and test denominators visible before anyone interprets a surveillance curve?

There are two complementary analyses here. The public-data analysis checks one downloaded release of CDC aggregate laboratory results. The report-vintage analysis checks what was available by different dates in an explicitly synthetic version history. The second does not manufacture historical versions of the first.

## Real public-data source

The source is the Centers for Disease Control and Prevention (CDC) dataset **Percent positivity of respiratory viruses by nucleic acid amplification tests (NAATs), as reported on the National Respiratory and Enteric Virus Surveillance System (NREVSS) Dashboard**, Socrata identifier `rgnm-fkqb` ([CDC, n.d.](https://data.cdc.gov/Laboratory-Surveillance/Percent-positivity-of-respiratory-viruses-by-nucle/rgnm-fkqb)). Socrata is the platform serving this public dataset. The pinned file contains national, Combined Type records for Adenovirus, HMPV, and PIV, for the 41 Saturday-ending weeks from January 3 through October 10, 2026. It was retrieved on October 20, 2026. These three series were chosen because this selection supplies explicit counts and a reported percentage; this is a workflow case study, not a representative sample of every NREVSS product.

The raw API response is retained without editing. The manifest records the exact filtered URL, retrieval time, byte length, SHA-256, date window, and category selection. A compact metadata capture records source column names, storage types, and access metadata. It does not contain complete semantic definitions of the dates. The source's `licenseId` is unset; no dataset-specific Creative Commons license is invented. CDC's agency-materials policy describes public-domain reuse with exceptions and requires attribution and a non-endorsement notice ([CDC, n.d.](https://www.cdc.gov/other/agencymaterials.html)). The original records are freely available from the linked source. The MIT license covers this repository's code, not a new license imposed on CDC data.

## Audit rules and denominators

One expected record is one selected series-week. The calendar comes from the declared date window, not from whichever rows happened to be returned. Counts must be nonnegative integers, detections cannot exceed tests, and duplicate series-week keys are quarantined. `*` remains suppressed and `.` remains unavailable; neither is treated as zero. Percentages computed from counts must agree with the source percentage within 0.005 percentage points, allowing two-decimal rounding. The implementation adds a 0.000000000001-point numerical margin to that boundary. A percentage point is an absolute difference between percentages; 10% to 12% is two percentage points. No outlier cutoff removes biologically plausible values.

Coverage is $`\frac{\text{usable series-weeks}}{\text{expected series-weeks}}`$ **within this extract**. It is not the fraction of all laboratories reporting, patients tested, infections detected, or the population represented. A complete-looking national row may aggregate incomplete or selectively submitted laboratory data. CDC describes voluntary laboratory participation, and [Silk et al. (2026)](https://pubmed.ncbi.nlm.nih.gov/41712508/) discuss variation in participation and representativeness. The aggregate file cannot establish unique-patient counts or whether repeated testing occurred. Consequently, positivity is a proportion of reported tests, not population prevalence. The article describes a different surveillance period; its results are not reproduced here.

Pooled positivity is $`100\,\frac{\sum\text{detections}}{\sum\text{tests}}`$ separately for each series. Pooling across the three series could double count tests or people and is not performed. A zero test denominator yields an undefined ratio. Arithmetic agreement checks do not establish clinical accuracy or representativeness.

## Trailing-window sensitivity

The public analysis repeats the summary after excluding observations newer than 0, 7, 14, or 28 days before its analysis date. It reports the number of eligible weeks, the retained test-denominator fraction, and the change in pooled positivity in percentage points. These choices illustrate a reproducible sensitivity analysis; they are not recommended universal delay corrections.

Every window uses the same downloaded release. Excluding recent observation weeks does **not** reconstruct the data available on a past date. The tool refuses an `--as-of` date before this snapshot's capture date to avoid that interpretation. The live CDC metadata checked on 21 October 2026 defines `posted` as the dataset publication date. This supports its use as release metadata; it is not an individual specimen date or laboratory receipt time. The older bundled metadata capture remains unchanged. This single file cannot estimate laboratory reporting-delay distributions.

## Consecutive-week denominator changes

A review diagnostic compares test counts only when consecutive calendar weeks are usable in the same series and the previous count is positive. The signed relative change is $`\frac{\text{current tests}-\text{previous tests}}{\text{previous tests}}`$. Its absolute value is compared strictly with a configurable threshold, default 0.5. This is a transparent demonstration setting, not a validated universal standard. It does not remove records, alter their validity status, estimate incidence, or explain why a denominator changed. Missing or suppressed weeks are not bridged, and zero previous denominators yield an undefined ratio. The output reports both counts so a flagged change can be investigated in context.

## Genuine as-of selection and revision comparison

`vintage_audit.py` accepts a separate table with an explicit `issued_on` for each full replacement report. It selects the newest version issued on or before the requested date and excludes later versions. A revised count is a replacement, not an additional count; downward corrections are allowed. Two records with the same key and issue date are ambiguous and fail validation. An invalid newest version is flagged rather than silently replaced with an older, valid-looking value.

A configurable grace period defines when an expected slot is due. Before that deadline it is `not_due`; after it, absence is `not_yet_available`. These are reporting statuses, not zero observations. The shipped version history is wholly synthetic and does not describe CDC reporting performance.

For real future releases, `compare_snapshots.py` compares two pinned, verified extracts with the same selection and ordered capture times. It flags changed values, status changes, and signed count differences. It cannot identify changes that happened between the captures. We currently ship only one real release and claim no measured historical revision rate.

The distinction between observation time and information availability follows [Mellor et al. (2026)](https://pubmed.ncbi.nlm.nih.gov/42832413/): reporting delays and later additions or corrections can make retrospective analyses appear more useful than they would have been in real time. That paper motivates this design; it does not validate our software or supply a delay model for these records.

## Assumptions, vocabulary, and references

The [assumption register](assumptions.md) explains the expected grid, matching test pools, date interpretations, exclusion rules, and heuristic thresholds. The [glossary](glossary.md) defines the terminology. Full citations and source roles are in [references](references.md); the [reference audit](reference-audit.json) records access limits and verification.
