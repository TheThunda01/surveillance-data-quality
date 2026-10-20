# The biology and concepts behind this analysis

## A surveillance number is an observation, not the whole picture

Respiratory surveillance brings together observations about illness, testing, and healthcare use. This project examines one part of that picture: weekly laboratory testing aggregates. Its source is the National Respiratory and Enteric Virus Surveillance System (NREVSS), to which participating laboratories voluntarily report. The information can describe patterns in submitted test results, but it does not enumerate every infection in the country. The distinction matters before calculating a rate or interpreting a line chart. [1, 3]

## What NAAT and PCR mean here

A nucleic acid amplification test, or NAAT, detects genetic material associated with a target organism. Polymerase chain reaction, or PCR, is one type of NAAT. These are different from antigen tests, which detect viral components such as proteins. The dataset identifies its test category as NAAT, so the analysis keeps that category rather than treating all testing technologies as interchangeable. [2]

The repository receives aggregate counts of results, not laboratory measurements for an individual sample. It therefore cannot assess a particular assay's sensitivity, specificity, sample quality, or a person's clinical condition. A “positive” in this analysis means a result counted as positive by the contributing testing system. It is not a measurement of disease severity, nor does this table independently establish which organism caused someone's symptoms.

## Why these three categories were chosen

The worked example includes Adenovirus, human metapneumovirus (HMPV), and parainfluenza viruses (PIV). These are source categories already supplied by NREVSS. The selected national “Combined Type” rows provide test counts, positive detections, and percentages for a manageable common window. Their usefulness here is methodological: the counts let a reader check the percentages and inspect changing denominators. They were not selected because they represent every respiratory infection or because one is expected to predict another.

The categories are also not identical biological units. In the source, PIV combines types 1–4, and HMPV is reported without separating types A and B. This project preserves those definitions and does not infer type-specific behavior. [1]

## The denominator determines the question

Here, weekly positivity is positive detections divided by tests, multiplied by 100. It answers: “What percentage of the reported tests in this category were positive?” It does not answer: “What percentage of people in the population were infected?” The source can include multiple specimens from one patient, while infections in people who were never tested are outside the table. [1]

Consider a purely arithmetic example: 10 positives among 100 tests is 10%; 10 positives among 50 tests is 20%. The numerator did not change. This does not tell us why testing decreased or what happened to infections. It shows why both counts belong beside the percentage. Similarly, percentages across weeks are pooled using summed numerators and denominators, not by giving a small testing week the same weight as a large one. Separate viral categories remain separate because their tested samples need not represent the same people.

## Observation time and information availability differ

An observation week describes when the counted testing occurred. An issue date describes when a version became available for analysis. A later correction can change the value attached to an earlier week. A retrospective dataset may therefore contain information that an analyst could not have known at the time. Mellor and colleagues explain why this distinction matters when evaluating surveillance indicators. [4]

Our pinned CDC file is one captured release. Its `posted` field is not a patient-level reporting-delay measurement. The separate synthetic vintage example demonstrates how actual issue dates can support as-of selection; it does not reconstruct an unavailable CDC history. Missing, not-yet-due, and zero are kept distinct.

## Aggregation and seasonality need care

A national weekly curve combines participating laboratories and locations. Changes in that mix can alter a summary even when local experiences differ. The 2026 MMWR respiratory-surveillance analysis describes both seasonal patterns and limits arising from voluntary participation and representativeness. Its findings concern its own study period; our shorter 2026 extract does not independently establish a recurring seasonal pattern. [3]

An apparent rise or fall is therefore a starting point for checking definitions, coverage, testing practices, and timing. This repository does not estimate incidence, compare disease severity, or identify an outbreak from the curve.

## How the denominator diagnostic helps

The added diagnostic compares test counts in consecutive usable weeks within each category. A configurable flag marks absolute relative changes greater than 50% by default. That number is an illustrative review setting, not a biological boundary or validated universal threshold. Flags do not remove records or change the audit's validity decisions.

A zero previous denominator leaves the ratio undefined. A missing or suppressed week breaks the comparison; the program does not bridge that gap. No flags in a dataset would mean only that this particular check found no changes above the chosen setting. It would not establish stable participation or unbiased surveillance.

## Sources

1. [CDC NREVSS dataset and definitions](https://data.cdc.gov/Laboratory-Surveillance/Percent-positivity-of-respiratory-viruses-by-nucle/rgnm-fkqb).
2. [CDC: Testing and Respiratory Viruses](https://www.cdc.gov/respiratory-viruses/prevention/testing.html).
3. Silk et al. (2026). [Respiratory Virus Activity — United States, July 1, 2024–June 30, 2025](https://doi.org/10.15585/mmwr.mm7506a2).
4. Mellor et al. (2026). [Recommendations for the analysis of leading indicators in epidemic surveillance](https://doi.org/10.1371/journal.pdig.0001759).
