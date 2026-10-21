# The biology and concepts behind this analysis

## A surveillance number is an observation, not the whole picture

Respiratory surveillance brings together observations about illness, testing, and healthcare use. This project examines one part of that picture: weekly laboratory testing aggregates. Its source is the National Respiratory and Enteric Virus Surveillance System (NREVSS), to which participating laboratories voluntarily report. The information can describe patterns in submitted test results, but it does not enumerate every infection in the country. The distinction matters before calculating a proportion or interpreting a line chart ([CDC, 2025a](https://www.cdc.gov/nrevss/php/dashboard/index.html); [Silk et al., 2026](https://pubmed.ncbi.nlm.nih.gov/41712508/)).

## What NAAT and PCR mean here

A nucleic acid amplification test, or NAAT, detects genetic material associated with a target organism; nucleic acids are molecules such as DNA and RNA that carry genetic information. Polymerase chain reaction, or PCR, is one type of NAAT. These are different from antigen tests, which detect viral components such as proteins. The dataset identifies its test category as NAAT, so the analysis keeps that category rather than treating all testing technologies as interchangeable ([CDC, 2025b](https://www.cdc.gov/respiratory-viruses/prevention/testing.html)).

The repository receives aggregate counts of results, not laboratory measurements for an individual sample. It therefore cannot assess a particular assay's sensitivity (ability to detect a target when present), specificity (ability to give a negative result when the target is absent), sample quality, or a person's clinical condition. An assay is a measurement procedure. A “positive” in this analysis means a result counted as positive by the contributing testing system. It is not a measurement of disease severity, nor does this table independently establish which organism caused someone's symptoms.

## Why these three categories were chosen

The worked example includes Adenovirus, human metapneumovirus (HMPV), and parainfluenza viruses (PIV). These are source categories already supplied by NREVSS. The selected national “Combined Type” rows provide test counts, positive detections, and percentages for a manageable common window. Their usefulness here is methodological: the counts let a reader check the percentages and inspect changing denominators. They were not selected because they represent every respiratory infection or because one is expected to predict another.

The categories are also not identical biological units. CDC describes PIV types 1–4 in NREVSS ([CDC, 2025a](https://www.cdc.gov/nrevss/php/dashboard/index.html)). This extract labels both PIV and HMPV as `Combined Type` and provides no separate type-specific counts. The project preserves those rows and does not infer behavior for a particular type.

## The denominator determines the question

Here, weekly positivity is positive detections divided by tests, multiplied by 100. It answers: “What percentage of the reported tests in this category were positive?” It does not answer: “What percentage of people in the population were infected?” These aggregate records do not identify unique patients, so the project cannot rule out repeated testing or count people. Infections in people who were never tested are outside the table. Population prevalence means the proportion of people with a condition in a defined population and period; it requires a different denominator.

Consider a purely arithmetic example: 10 positives among 100 tests is 10%; 10 positives among 50 tests is 20%. The numerator did not change. This does not tell us why testing decreased or what happened to infections. It shows why both counts belong beside the percentage. Similarly, percentages across weeks are pooled using summed numerators and denominators, not by giving a small testing week the same weight as a large one. Separate viral categories remain separate because their tested samples need not represent the same people.

## Observation time and information availability differ

The observation week is the surveillance reference week assigned by the source. CDC describes collection-week reporting, but this extract does not contain individual collection or testing dates ([CDC, 2025a](https://www.cdc.gov/nrevss/php/dashboard/index.html)). An issue date describes when a version became available for analysis. A later correction can change the value attached to an earlier week. A retrospective dataset may therefore contain information that an analyst could not have known at the time. [Mellor et al. (2026)](https://pubmed.ncbi.nlm.nih.gov/42832413/) explain why this distinction matters when evaluating surveillance indicators.

Our pinned CDC file is one captured release. The adapter treats its `posted` field as release/update metadata, an explicit [assumption](assumptions.md), rather than a patient-level reporting-delay measurement. The separate synthetic vintage example demonstrates how actual issue dates can support as-of selection; it does not reconstruct an unavailable CDC history. Missing, not-yet-due, and zero are kept distinct.

## Aggregation and seasonality need care

A national weekly curve combines participating laboratories and locations. Changes in that mix can alter a summary even when local experiences differ. [Silk et al. (2026)](https://pubmed.ncbi.nlm.nih.gov/41712508/), in the Morbidity and Mortality Weekly Report (MMWR), describe seasonal patterns and limits arising from voluntary participation and representativeness—how well the observed group reflects the population of interest. Its findings concern its own study period; our shorter 2026 extract does not independently establish a recurring seasonal pattern.

An apparent rise or fall is therefore a starting point for checking definitions, coverage, testing practices, and timing. This repository does not estimate incidence (new cases arising in a defined population over time), compare disease severity, or identify an outbreak from the curve.

## How the denominator diagnostic helps

The added diagnostic compares test counts in consecutive usable weeks within each category. A configurable flag marks absolute relative changes greater than 50% by default. That number is an illustrative review setting, not a biological boundary or validated universal threshold. Flags do not remove records or change the audit's validity decisions.

A zero previous denominator leaves the ratio undefined. A missing or suppressed week breaks the comparison; the program does not bridge that gap. No flags in a dataset would mean only that this particular check found no changes above the chosen setting. It would not establish stable participation or unbiased surveillance.

## Sources and vocabulary

The [reference list](references.md) gives complete citations. The [glossary](glossary.md) defines terms such as denominator, suppression, sensitivity analysis, and vintage. The [assumption register](assumptions.md) separates source evidence from choices made by this project.
