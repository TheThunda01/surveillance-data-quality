# Synthetic surveillance audit

These are invented aggregate records. No result describes an actual population.

| Measure | Result |
| --- | --- |
| expected site weeks | 12 |
| input rows | 12 |
| received site weeks | 11 |
| missing site weeks | 1 |
| invalid site weeks | 4 |
| usable site weeks | 7 |
| usable fraction | 0.5833333333333334 |
| excluded input rows | 5 |
| late usable reports | 1 |
| late after days | 7 |
| median delay days usable | 2 |
| pooled positive tests | 14 |
| pooled tests performed | 360 |
| pooled positivity | 0.03888888888888889 |

Pooled test positivity is **3.89%**, using only usable records. It is not a population prevalence estimate.

Missing slots remain missing. Every duplicated key is quarantined in full; no version is selected automatically. Review findings.csv before changing the source data.

Input fingerprints and row-level reasons are in audit.json.
