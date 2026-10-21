# Methods, assumptions, and sources

## What is being counted

Each expected key is one fictional clinic and one Monday-starting week. `positive_tests` counts positive test results within the same pool described by `tests_performed`. These are test counts, not unique patients, incident cases, or population denominators. Repeated testing and selection into testing are not modeled.

The expected calendar is authoritative for this run. Coverage is reported two ways: $`\frac{\text{submitted slots}}{\text{expected slots}}`$ and $`\frac{\text{usable slots}}{\text{expected slots}}`$. A missing slot has no submitted row; an invalid slot has submitted data that cannot pass this schema. Neither is converted into zero.

The script rejects invalid calendar definitions because a faulty expectation table would corrupt the audit denominator. Within the submitted report table, invalid rows are retained as findings and excluded from aggregates. Duplicate resolution requires a documented human decision outside this tool.

## How the references apply

[German et al. (2001)](https://pubmed.ncbi.nlm.nih.gov/18634202/) define data quality in terms of recorded completeness and validity, and discuss timeliness as speed between steps. That supports separating our checks, but it does not validate this software or establish a universal acceptable reporting delay. This example measures only week-end-to-submission delay, not the interval from symptom onset, testing, or clinical diagnosis.

The World Health Organization (WHO)'s [COVID-19 dashboard methods (n.d.)](https://data.who.int/dashboards/covid19/circulation) calculate positivity from reported positive and processed samples and caution that changes in testing and reporting can affect interpretation. Our pooled ratio follows that numerator/denominator logic on invented records. The example does not use WHO data, implement its full surveillance definitions, or assume that test positivity is population prevalence.

## Reproducibility and limitations

`src/generate_demo.py` is the complete fixture recipe. It creates three fictional sites and four weeks, then plants one absent report, one duplicate key, and three invalid values or date relationships. The audit records SHA-256 fingerprints of its two inputs. Output ordering is deterministic and files contain no execution timestamp.

The seven-day threshold is a configurable demonstration choice. It flags review, not exclusion. All dates are calendar dates without time zones; this example does not model within-day reporting. There is no imputation, delay adjustment, causal analysis, or uncertainty model. The tool catches explicit inconsistencies, not all real data errors. Choosing exclusions can alter a summary; therefore the audit exposes both excluded rows and denominator coverage.

## Assumptions, vocabulary, and references

See the [assumption register](assumptions.md) for the calendar and delay choices, the [glossary](glossary.md) for definitions, and [references](references.md) for complete citations. These sources motivate the checks; they do not independently validate this implementation.
