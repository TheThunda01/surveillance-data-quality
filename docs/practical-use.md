# Practical use

## Where this fits

Use this audit to record what a surveillance extract contains, which rows can contribute to a count ratio, and what needs review. The Centers for Disease Control and Prevention (CDC) example contains real aggregate counts of test results; the clinic and report-vintage examples are invented. The audit does not estimate all infections or reconstruct CDC history from one release.

## Input and output contract

`python src/validate_snapshot.py --snapshot data/public` checks a snapshot without changing its files. It prints JavaScript Object Notation (JSON), a structured text format, to standard output (the terminal output stream). Contract version 1.0 requires a JSON manifest, a comma-separated values (CSV) file, and captured source metadata describing the source.

The preflight checks the supported CDC dataset, source-page and endpoint identities, a capture timestamp with a Coordinated Universal Time (UTC) offset, file names, exact byte length and SHA-256 digests, and metadata identity and columns. It also requires a national combined-type selection with unique supported categories and ordered Saturday endpoints no later than capture. The CSV must have the twelve documented fields.

The adapter treats `posted` as release/update metadata and rejects a parsed date later than capture. Same-day dates are allowed because `posted` has calendar-day precision, not a reliable release time. The row audit then checks scope, counts, duplicates, dates, and percentage consistency.

If a snapshot violates the contract, the command exits with status 2 and a readable error. A snapshot that meets the contract may still contain absent, suppressed, unavailable, or invalid observation slots. The JSON counts report these conditions and set `review_required` to true. False means only that these row conditions were not found; scientific and provenance review may still be needed.

A checksum detects changed bytes relative to the supplied manifest. It cannot authenticate a publisher because someone could edit the files and manifest together.

Add `--diagnostics-json` to emit the [version 1.0 diagnostic envelope](diagnostics.md), including stable finding codes and locations, on success or failure. Rejected input returns exit 2 and a null summary; a completed audit with review findings returns exit 0 and `status: review`. Zero tests remain an informational finding, separate from missing reports. Argument-parsing errors retain argparse's text output.

`public_audit.py` uses the same loader and writes CSV, JSON, Markdown (formatted text), and Scalable Vector Graphics (SVG, a vector image format) into a chosen output directory. Missing data remain separate from observed zeros. The adapter deliberately supports only its documented schema; a provider change needs inspection and tests before a contract update. See the [field dictionary](public-data-dictionary.md) and [captured provenance](../data/public/manifest.json).

## Worked use case

```sh
python src/validate_snapshot.py
python src/validate_snapshot.py --diagnostics-json
python src/public_audit.py --output /tmp/public-audit
```

The checked-in [preflight output](../examples/snapshot_preflight.json) reports 123 rows, 123 expected slots, and no invalid or unavailable slots. The [analysis](../results_public/report.md) keeps each viral category's denominator separate. Complete rows within this selection do not establish complete participation by laboratories. The adapter interprets `posted` as a release/update date. The captured column metadata do not establish individual specimen or testing dates; this assumption is recorded in [assumptions](assumptions.md).

For a later capture, use `fetch_public.py --output snapshots/new_capture`, preserve the earlier directory, run preflight, then compare releases with `compare_snapshots.py`. Capture dates are observations of availability, not proof of the provider's first release time.

## Checks before relying on a result

The operator should verify the source URL and scope, read the capture date, and inspect all row findings. Check whether counts mean tests, people, or events; whether participation or testing changed; and whether the selected period fits the question. Read [the evidence review](literature-review.md) before interpreting timeliness. The 50% denominator-change setting is an adjustable review diagnostic, not a scientific validity cutoff.

## Known limits

Read the [assumption register](assumptions.md), [glossary](glossary.md), and [reference audit](reference-audit.json) alongside a result.

There is one genuine CDC capture, so the bundled project cannot measure historical revision rates. There are no laboratory-level reporting denominators or linked patient records. The preflight checks are structural and reproducible, not evidence of national representativeness, laboratory accuracy, clinical performance, or readiness for operational surveillance.

## Next improvements

1. Archive scheduled captures with explicit retention. Acceptance: two independently retrieved, dated releases reproduce a comparison without changing either original.
2. Add contract migration fixtures. Acceptance: a documented provider schema change is rejected by version 1.0 and accepted only by a separately tested migration.
3. Add laboratory participation denominators if publicly documented. Acceptance: coverage states its exact eligible-laboratory definition and never substitutes extract completeness.
4. Add an example downstream consumer of the diagnostic contract. Acceptance: it handles passed, review, rejected, and unknown additive codes without matching human messages or discarding flagged data automatically.
