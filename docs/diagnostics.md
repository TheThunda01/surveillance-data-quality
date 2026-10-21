# Machine-readable preflight diagnostics

The optional `--diagnostics-json` switch emits the same versioned JavaScript Object Notation (JSON) envelope—a structured wrapper around the findings whether the snapshot passes, needs row review, or is rejected. Without it, the existing summary and human-readable error behavior remain available.

This envelope covers preflight execution after command-line parsing. Invalid command-line arguments still produce argparse's text error and exit status 2.

```sh
python src/validate_snapshot.py --diagnostics-json
# Deliberately invalid manifest fixture: prints a rejection and exits 2.
python src/validate_snapshot.py --snapshot examples/invalid_manifest --diagnostics-json
```

See the [passing capture](../examples/diagnostics_passed.json), [rejected fixture](../examples/diagnostics_rejected.json), [JSON Schema](../schemas/preflight-diagnostics-v1.schema.json), and [code catalog](../schemas/preflight-diagnostic-codes-v1.json). The rejected fixture is a synthetic parser test, not a CDC release.

## Envelope and exit contract

| Field | Meaning |
| --- | --- |
| `diagnostics_version` | `1.0`; version of this envelope and code taxonomy |
| `status` | `passed`, `review`, or `rejected` |
| `exit_code` | 0 for a completed audit, including row findings; 2 for rejected input |
| `summary` | Existing preflight summary when the audit completes, otherwise null |
| `findings` | Zero or more typed findings, each with code, severity, message, and location |

Each location always contains `scope`, `field`, `line`, `pathogen`, and `week_end`. Unknown or inapplicable details are null. `line` is a one-based source row/line locator: CSV structural errors use the parser's physical line, while row findings use the header-plus-record index. They coincide for the single-line records in the bundled snapshot; multiline quoted CSV records can differ. No patient data or full input values are included.

In this version, invalid manifests or structural/source failures stop at the first detected error. Their severity is `error`, the status is `rejected`, and no partial aggregate is emitted. Once the input contract is accepted, all expected series-week slots are assessed. Missing, suppressed, unavailable, duplicate, invalid-release, count, and percentage findings have severity `review`. These observations retain the existing exclusion and denominator rules. A reported zero-test denominator has severity `info`: its positivity is undefined, but zero is not a missing report.

`passed` means the implemented contract and row checks completed without review findings. It does not mean authentic source provenance, complete laboratory participation, or valid population inference. Likewise, a review flag is not an estimate of bias or a mandate to discard every flagged value.

## Stable codes, changing prose

Consumers should branch on `diagnostics_version` and `code`, not English messages. Typed exceptions assign codes where a check actually fails; code selection does not parse error strings. File input/output (I/O), text decoding, comma-separated values (CSV) parsing, and JSON syntax have separate categories. `VALIDATION_FAILED` is an explicit generic fallback for a validation exception without a specific type; it makes no claim about its cause.

The [catalog](../schemas/preflight-diagnostic-codes-v1.json) is the machine-readable list of current meanings and severities. Codes retain their meanings within major version 1. Consumers should tolerate added fields or unfamiliar additive codes when accepting a later minor version, while applying their own handling policy. The checked-in schema describes exactly version 1.0.

This is a command-line interface (CLI) format designed for this project, not an implementation of a Hypertext Transfer Protocol (HTTP) standard. [Nottingham et al. (2023), RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) provides a useful design precedent for separating a machine problem identifier from human-readable details. No RFC code or third-party validation library is copied or required.

## Verification on 2026-10-20

All **74 tests** passed, including actual-input regressions for distinct typed errors and missing-versus-zero findings. The three original analyses reproduced their checked-in outputs byte for byte. The original preflight example also remains unchanged, and the new passed/rejected diagnostic examples reproduce their JSON. Source data, licenses, baseline results, and the round-1 search log were preserved. These are local checks; they do not establish epidemiological validity or a hosted CI result.

For terminology and complete source details, see the [glossary](glossary.md) and [references](references.md). The [dated review](review-2026-10-20.md) records the checks repeated during the editorial review.
