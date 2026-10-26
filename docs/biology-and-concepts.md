# The biology and concepts behind this analysis

## A surveillance number is an observation, not the whole picture

Respiratory surveillance brings together observations about illness, testing, and healthcare use. This project examines one part of that picture: weekly laboratory testing aggregates. Its source is the National Respiratory and Enteric Virus Surveillance System (NREVSS), to which participating laboratories voluntarily report. The information can describe patterns in submitted test results, but it does not enumerate every infection in the country. The distinction matters before calculating a proportion or interpreting a line chart ([CDC, 2025a](https://www.cdc.gov/nrevss/php/dashboard/index.html); [Silk et al., 2026](https://pubmed.ncbi.nlm.nih.gov/41712508/)).

## What NAAT and PCR mean here

A nucleic acid amplification test, or NAAT, detects genetic material associated with a target organism; nucleic acids are molecules such as DNA and RNA that carry genetic information. Polymerase chain reaction, or PCR, is one type of NAAT. These are different from antigen tests, which detect viral components such as proteins. The dataset identifies its test category as NAAT, so the analysis keeps that category rather than treating all testing technologies as interchangeable ([CDC, 2025b](https://www.cdc.gov/respiratory-viruses/prevention/testing.html)).

These aggregate counts cannot assess individual samples or patients. They contain no individual laboratory measurements, so the analysis cannot assess an assay's sensitivity (detecting a target when present), specificity (giving a negative result when the target is absent), sample quality, or a person's clinical condition. An assay is a measurement procedure.

A “positive” here is a result counted as positive by the contributing testing system. It does not measure disease severity or independently establish which organism caused someone's symptoms.

## Why these three categories were chosen

The example uses three NREVSS categories—Adenovirus, human metapneumovirus (HMPV), and parainfluenza viruses (PIV)—because their counts allow readers to check percentages and compare denominators. The selected national “Combined Type” rows provide test counts, positive detections, and percentages for a manageable common window. The selection does not imply that these categories represent every respiratory infection or predict one another.

The categories are also not identical biological units. CDC describes PIV types 1–4 in NREVSS ([CDC, 2025a](https://www.cdc.gov/nrevss/php/dashboard/index.html)). This extract labels both PIV and HMPV as `Combined Type` and provides no separate type-specific counts. The project preserves those rows and does not infer behavior for a particular type.

## The denominator determines the question

Weekly positivity describes reported tests, not the proportion of infected people. It is positive detections divided by tests, multiplied by 100. The aggregate records do not identify unique patients, so the project cannot count people or rule out repeated testing. Infections in people who were never tested are outside the table. Population prevalence—the proportion of people with a condition in a defined population and period—requires a different denominator.

For example, 10 positives among 100 tests is 10%; 10 positives among 50 tests is 20%. The numerator did not change. This arithmetic shows why both counts belong beside the percentage, but it does not explain why testing decreased or what happened to infections.

The analysis pools weeks by summing numerators and denominators, so a week with fewer tests contributes less than one with more tests. It keeps viral categories separate because their tested samples need not represent the same people.

## Observation time and information availability differ

The observation week is the surveillance reference week assigned by the source. CDC describes collection-week reporting, but this extract does not contain individual collection or testing dates ([CDC, 2025a](https://www.cdc.gov/nrevss/php/dashboard/index.html)). An issue date describes when a version became available for analysis. A later correction can change the value attached to an earlier week. A retrospective dataset may therefore contain information that an analyst could not have known at the time. [Mellor et al. (2026)](https://pubmed.ncbi.nlm.nih.gov/42832413/) explain why this distinction matters when evaluating surveillance indicators.

Our pinned CDC file is one captured release. The adapter treats its `posted` field as release/update metadata, an explicit [assumption](assumptions.md), rather than a patient-level reporting-delay measurement. The separate synthetic vintage example demonstrates how actual issue dates can support as-of selection; it does not reconstruct an unavailable CDC history. Missing, not-yet-due, and zero are kept distinct.

## Aggregation and seasonality need care

A national weekly curve combines participating laboratories and locations. Changes in that mix can alter a summary even when local experiences differ. [Silk et al. (2026)](https://pubmed.ncbi.nlm.nih.gov/41712508/), in the Morbidity and Mortality Weekly Report (MMWR), describe seasonal patterns and limits arising from voluntary participation and representativeness—how well the observed group reflects the population of interest. Its findings concern its own study period; our shorter 2026 extract does not independently establish a recurring seasonal pattern.

An apparent rise or fall is therefore a starting point for checking definitions, coverage, testing practices, and timing. This repository does not estimate incidence (new cases arising in a defined population over time), compare disease severity, or identify an outbreak from the curve.

## How the denominator diagnostic helps

The denominator diagnostic flags changes in test counts for review. It compares consecutive usable weeks within each category and, by default, flags absolute relative changes greater than 50%. This configurable setting is illustrative, not a biological boundary or validated universal threshold. Flags do not remove records or change the audit's validity decisions.

A zero previous denominator leaves the ratio undefined. A missing or suppressed week breaks the comparison; the program does not bridge that gap. No flags in a dataset would mean only that this particular check found no changes above the chosen setting. It would not establish stable participation or unbiased surveillance.

## Sources and vocabulary

The [reference list](references.md) gives complete citations. The [glossary](glossary.md) defines terms such as denominator, suppression, sensitivity analysis, and vintage. The [assumption register](assumptions.md) separates source evidence from choices made by this project.
