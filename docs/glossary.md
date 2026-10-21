# Glossary

This page explains the scientific and computing terms used in the project. Field names retain the spelling required by the source or program. The [data dictionaries](public-data-dictionary.md) give their exact rules; the [assumption register](assumptions.md) explains the choices behind them.

## Biology, surveillance, and statistics

| Term | Meaning in this project |
| --- | --- |
| Aggregate | A count or summary that combines individual observations. It does not retain a patient-level record. |
| Assay | A procedure used to measure or detect something in a sample. |
| Bias | A systematic difference between what is measured or estimated and the quantity of interest. Passing an arithmetic check does not rule it out. |
| CDC | Centers for Disease Control and Prevention, the US public health agency publishing the real example data. |
| Clinical validity | Whether a measurement or interpretation is suitable for its intended clinical purpose. This project does not evaluate that. |
| Completeness or coverage | How much of a specified set is observed. Here, extract coverage means usable expected series-week slots divided by all expected slots; it does not measure coverage of people or laboratories. |
| Causal analysis | An analysis intended to estimate what would change because of an intervention or exposure. This project does not identify causes. |
| Denominator | The quantity by which another quantity is divided. For positivity it is the number of tests; for extract coverage it is the number of expected slots. |
| Detection or positive test | A result counted as positive by the contributing system. It does not itself measure symptoms, severity, or a unique infected person. |
| Diagnostic | Here, a software check that highlights a data condition. It is not a medical diagnosis or a validated outbreak alarm. |
| HHS | US Department of Health and Human Services. |
| HMPV | Human metapneumovirus, one of the source's viral categories. |
| Imputation | Filling a missing value using an assumption or model. This project does not impute missing counts. |
| Incidence | New cases arising in a defined population during a specified period. The test counts in this project are not incidence estimates. |
| NAAT | Nucleic acid amplification test: a test that amplifies genetic material to help detect a target. Nucleic acids include DNA (deoxyribonucleic acid) and RNA (ribonucleic acid). |
| NREVSS | National Respiratory and Enteric Virus Surveillance System, the voluntary laboratory reporting system used for the real example. Enteric refers to the intestinal tract. |
| Numerator | The quantity above the division line, such as positive tests in a positivity calculation. |
| PCR | Polymerase chain reaction, one type of NAAT. An antigen test instead detects components such as proteins. |
| Proportion | A part divided by its whole, between zero and one. Multiplying by 100 expresses it as a percentage. |
| Percentage point | An absolute difference between percentages: 10% to 12% is two percentage points, but a 20% relative increase. |
| PIV | Parainfluenza viruses. The selected records use the source label `Combined Type`. |
| Pooled positivity | Sum of positive tests divided by sum of tests for one category, multiplied by 100 for a percentage. It weights weeks by their test counts rather than averaging their percentages equally. |
| Population prevalence | The proportion of people with a condition in a defined population and period. A proportion of reported tests is a different quantity. |
| Representativeness | How well the observed group reflects the population about which a conclusion is intended. |
| Retrospective | Looking back using information available at a later time. Later revisions can affect what an earlier period looks like. |
| Sensitivity and specificity | For an assay, sensitivity is its ability to detect the target when present; specificity is its ability to give a negative result when the target is absent. Neither is estimated here. |
| Sensitivity analysis | Repeating a calculation after changing a stated choice to see how much the result changes. This is unrelated to an assay's sensitivity. |
| Series | One repeatedly measured category, here a viral category with weekly counts. A series-week is one category in one week. |
| Suppressed | Withheld from display by the source, marked `*` in this adapter. It is not an observed zero. |
| Surveillance | Ongoing collection, analysis, and interpretation of observations for monitoring health. |
| Time series | Observations indexed in time order, such as a category’s weekly test counts. |
| Threshold | A chosen boundary for flagging a result. The default 50% denominator-change and seven-day delay settings are illustrative choices. |
| Unavailable | A value the source does not supply, represented by `.` or a blank required field here. |

## Dates and reporting history

| Term | Meaning in this project |
| --- | --- |
| As-of date or cutoff | The date limiting which information can be used. In the synthetic history, only versions issued on or before it are eligible. |
| Backfill | Data added later to a previously reported period. A revision can also reduce or correct an earlier value. |
| Grace period | A chosen number of days after the reporting week before a report is considered due. It is not an empirically estimated reporting delay here. |
| Issue date | The date a version is recorded as becoming available. Synthetic `issued_on` explicitly represents this event. |
| MMWR week | A surveillance calendar week used in Morbidity and Mortality Weekly Report data. This adapter accepts Saturday-ending source dates. The synthetic SQL example instead uses Monday starts and Sunday ends. |
| Observation or reference week | The week to which an aggregate is assigned. It is distinct from the date the file was retrieved. |
| Posted date | The source's `posted` field, interpreted by the adapter as release/update-date metadata. The captured metadata do not establish its complete meaning or a patient-level timeline. |
| Release or snapshot | A saved state of the dataset. A capture date shows when this project retrieved it, not necessarily when it first became publicly available. |
| Reporting delay | Time between two defined events. The synthetic basic audit uses week end to submission date; the vintage audit uses week end to issue date. No patient-level delay is inferred. |
| Revision | A replacement or correction to a previously reported value. A full replacement must not be added to the old value as another batch. |
| Trailing-window exclusion | Leaving out weeks newer than a specified age while retaining the same saved release. This does not recover an earlier release. |
| UTC | Coordinated Universal Time, the common time reference used for capture timestamps. |
| Vintage | A particular version of observations available at a time. The bundled report histories are invented examples, not past CDC releases. |

## Computing and review

| Term | Meaning in this project |
| --- | --- |
| API and endpoint | An application programming interface is a way for programs to request data. An endpoint is a particular address serving a request. |
| Archive | A collection of saved earlier states or changes. The Delphi archive is an external design example; it is not bundled here. |
| Checksum or digest | A value computed from file contents. SHA-256 (Secure Hash Algorithm, 256-bit) gives the fingerprints used here. Agreement detects change relative to the supplied manifest, not publisher authenticity. |
| CLI | Command-line interface: running a program by typing a command and options in a terminal. |
| Contract | The supported input or output fields and rules that programs agree to follow. |
| CSV | Comma-separated values, a text format for tables. A quoted record can span multiple physical lines. |
| Deterministic | Producing the same result from the same inputs and settings. |
| Envelope | A structured wrapper containing status, summary, and diagnostic findings. |
| Exit code | A number returned when a command ends. Here 0 means the command completed, not scientific approval; 2 indicates rejected input or an invocation error. |
| Fixture | A small input example used to demonstrate or test a defined behavior. |
| I/O | Input/output: reading information and writing results. |
| JSON | JavaScript Object Notation, a structured text format for objects, lists, numbers, and other values. JSON `null` represents an absent or undefined value in these outputs. |
| Integer | A whole number. Count fields here must be nonnegative integers. |
| JSON Schema | A machine-readable description of allowed JSON structure and values. The checked-in schema describes diagnostic version 1.0. |
| Key | Fields used together to identify a record, such as viral category and week. Duplicate keys require review. |
| Left join | A database operation that preserves every record in the first table, even when the second table has no match. This exposes missing expected reports. |
| Manifest | A file recording source addresses, selection rules, capture time, file names, and checksums for a saved extract. |
| Metadata | Information about data, such as field names, storage types, or source identity. A field name alone may not fully define its scientific meaning. |
| MIT license | A software reuse license. It covers this repository's code; it does not assign a new license to CDC data. |
| Pinned | Saved at a fixed version so later upstream changes do not silently alter an analysis. A commit identifier pins a version of repository files. |
| Preflight | Checks performed before the main analysis. Passing them does not establish scientific validity. |
| Provenance | The documented origin and transformation history of data or results. |
| Quarantine | Keep a problematic record for inspection but exclude it from numerical summaries. |
| Regression test | A check that an established behavior still works after a change. It does not establish external scientific validity. |
| RFC and HTTP | A Request for Comments is an internet specification. Hypertext Transfer Protocol carries web requests and responses. RFC 9457 is a design reference, not a standard implemented by this CLI. |
| Schema | The expected field names, types, and structural rules of a dataset. |
| SQL and SQLite | Structured Query Language is used to query tables; SQLite is the database engine used by the synthetic audit. |
| Standard library | Modules supplied with Python, so no separately installed analysis package is required. |
| SVG | Scalable Vector Graphics, the image format used for the chart. |
| Synthetic | Invented data with known conditions for demonstration or testing; not observations of real people or sites. |
| Validation | Checking stated rules or fitness for a defined purpose. This repository's input validation and tests are narrower than independent scientific or operational validation. |
