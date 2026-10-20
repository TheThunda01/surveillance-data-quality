# Methods, assumptions, and sources

## What is being counted

Each expected key is one fictional clinic and one Monday-starting week. `positive_tests` counts positive test results within the same pool described by `tests_performed`. These are test counts, not unique patients, incident cases, or population denominators. Repeated testing and selection into testing are not modeled.

The expected calendar is authoritative for this run. Coverage is reported two ways: submitted slots / expected slots and usable slots / expected slots. A missing slot has no submitted row; an invalid slot has submitted data that cannot pass this schema. Neither is converted into zero.

The script rejects invalid calendar definitions because a faulty expectation table would corrupt the audit denominator. Within the submitted report table, invalid rows are retained as findings and excluded from aggregates. Duplicate resolution requires a documented human decision outside this tool.

## How the references apply

CDC's 2001 surveillance evaluation guidance defines data quality in terms of recorded completeness and validity, and discusses timeliness as speed between steps. That supports separating our checks, but it does not validate this software or establish a universal acceptable reporting delay. This example measures only week-end-to-submission delay, not the interval from symptom onset, testing, or clinical diagnosis. [1]

WHO's dashboard methods calculate positivity from reported positive and processed samples and caution that changes in testing and reporting can affect interpretation. Our pooled ratio follows that numerator/denominator logic on invented records. The example does not use WHO data, implement its full surveillance definitions, or assume that test positivity is population prevalence. [2]

## Reproducibility and limitations

`src/generate_demo.py` is the complete fixture recipe. It creates three fictional sites and four weeks, then plants one absent report, one duplicate key, and three invalid values/date relationships. The audit records SHA-256 fingerprints of its two inputs. Output ordering is deterministic and files contain no execution timestamp.

The seven-day threshold is a configurable demonstration choice. It flags review, not exclusion. All dates are calendar dates without time zones; this example does not model within-day reporting. There is no imputation, delay adjustment, causal analysis, or uncertainty model. The tool catches explicit inconsistencies, not all real data errors. Choosing exclusions can alter a summary; therefore the audit exposes both excluded rows and denominator coverage.

## References

1. German RR, Lee LM, Horan JM, Milstein RL, Pertowski CA, Waller MN. Updated Guidelines for Evaluating Public Health Surveillance Systems: Recommendations from the Guidelines Working Group. *MMWR Recommendations and Reports*. 2001;50(RR-13):1–35. [Official CDC report](https://www.cdc.gov/mmwr/preview/mmwrhtml/rr5013a1.htm). Supports the conceptual separation of completeness, validity, and timeliness; it is not a certification standard for this implementation.
2. World Health Organization. WHO COVID-19 dashboard: circulation and data interpretation notes. [Official methods and interpretation page](https://data.who.int/dashboards/covid19/circulation). Accessed October 20, 2026. Supports the test-positivity denominator definition and cautions about reporting and testing practices; this project makes no claim about COVID-19 trends.
