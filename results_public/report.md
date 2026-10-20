# Real public-data audit: CDC NREVSS

Pinned extract: **2026-01-03–2026-10-10**, retrieved **2026-10-20**. Source: CDC. This project is not endorsed by CDC or the U.S. government. The source data are freely available from the linked CDC dataset.

This audit describes data in one extracted release. It does not measure the fraction of all laboratories reporting or the completeness of infections in the population.

| Series | Usable / expected weeks | Positive tests / tests | Pooled positivity |
| --- | --- | --- | --- |
| Adenovirus | 41 / 41 | 21,057 / 799,289 | 2.634% |
| HMPV | 41 / 41 | 24,375 / 791,964 | 3.078% |
| PIV | 41 / 41 | 23,015 / 875,604 | 2.628% |

![Weekly unsmoothed test positivity](weekly_positivity.svg)

All three numerator/denominator pairs remain separate. Do not add them as unique people or compare pooled ratios as if they came from identical tested populations.

## What changes when recent weeks are held out?

The trailing-window analysis excludes weeks newer than 0, 7, 14, or 28 days before the analysis date. It reuses the same retrieved release. It is a sensitivity analysis of the observation window, **not** a recovery of values that were reported on an earlier date.

| Series | Days held out | Usable weeks | Retained test denominator | Positivity change (percentage points) |
| --- | ---: | ---: | ---: | ---: |
| Adenovirus | 0 | 41 | 100.00% | +0.0000 |
| Adenovirus | 7 | 41 | 100.00% | +0.0000 |
| Adenovirus | 14 | 40 | 98.09% | -0.0094 |
| Adenovirus | 28 | 38 | 93.10% | -0.0098 |
| HMPV | 0 | 41 | 100.00% | +0.0000 |
| HMPV | 7 | 41 | 100.00% | +0.0000 |
| HMPV | 14 | 40 | 97.87% | +0.0543 |
| HMPV | 28 | 38 | 92.88% | +0.1870 |
| PIV | 0 | 41 | 100.00% | +0.0000 |
| PIV | 7 | 41 | 100.00% | +0.0000 |
| PIV | 14 | 40 | 98.04% | +0.0000 |
| PIV | 28 | 38 | 93.14% | +0.0175 |

## Did the weekly test denominator change sharply?

The review flag uses an absolute week-to-week test-count change **greater than 50.0%**. It compares consecutive usable calendar weeks only; a missing week or zero previous denominator leaves the ratio undefined. This setting is a demonstration choice, not a validated universal cutoff. Flagged records remain in every analysis.

| Series | Evaluable consecutive pairs | Flagged for review | Largest absolute change |
| --- | ---: | ---: | ---: |
| Adenovirus | 40 | 0 | 25.45% |
| HMPV | 40 | 0 | 16.57% |
| PIV | 40 | 0 | 34.05% |

[Inspect the week-level counts and ratios](denominator_changes.csv). A change can reflect testing, participation, calendar effects, or other factors; this file does not identify its cause and is not an incidence or outbreak indicator.


No adjustment for underreporting, causal effect, or outbreak forecast is fitted. The `posted` field is treated as release metadata, never as an individual laboratory submission date. See the methods for why complete-looking rows can still be provisional.

[Original dataset](https://data.cdc.gov/Laboratory-Surveillance/Percent-positivity-of-respiratory-viruses-by-nucle/rgnm-fkqb) · [Snapshot provenance](../data/public/manifest.json) · [Methods](../docs/public-data-methods.md)
