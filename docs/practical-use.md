# Practical use

## Where this fits

This is a small, inspectable audit before describing a public surveillance extract. The practical output is a record of what was received, which rows can contribute to a count ratio, and what needs review. The CDC example is real aggregate data; the clinic and report-vintage examples are invented. It does not estimate all infections or reconstruct CDC history from one release.

## Input and output contract

`python src/validate_snapshot.py --snapshot data/public` prints JSON to standard output and leaves input files untouched. Contract version 1.0 requires a JSON manifest, a CSV, and captured source metadata. It checks the supported CDC dataset, source-page and endpoint identities, a timezone-aware UTC capture timestamp, file names, exact byte length and SHA-256 digests, metadata identity/columns, and a national combined-type selection with unique supported categories and ordered Saturday endpoints no later than capture. The CSV must have the twelve documented fields. A parsed `posted` release date after the capture date is rejected as inconsistent. Same-day dates are allowed because `posted` has calendar-day precision, not a reliable release time. The row audit then checks scope, counts, duplicates, dates, and percentage consistency.

A malformed contract exits with status 2 and a readable error. A valid contract can still contain absent, suppressed, unavailable, or invalid observation slots: these appear in the JSON counts and set `review_required` to true. That flag covers these row conditions only. False does **not** mean no scientific or provenance review is needed. A checksum detects changed bytes relative to the supplied manifest; it does not authenticate a publisher when both files can be edited together.

`public_audit.py` uses the same loader and writes CSV, JSON, Markdown, and SVG into a chosen output directory. Missing data remain separate from observed zeros. The adapter deliberately supports only its documented schema; a provider change needs inspection and tests before a contract update. See the [field dictionary](public-data-dictionary.md) and [captured provenance](../data/public/manifest.json).

## Worked use case

```sh
python src/validate_snapshot.py
python src/public_audit.py --output /tmp/public-audit
```

The checked-in [preflight output](../examples/snapshot_preflight.json) reports 123 rows, 123 expected slots, and no invalid or unavailable slots. The [analysis](../results_public/report.md) keeps each viral category's denominator separate. Complete rows within this selection do not establish complete participation by laboratories. The source's `posted` field is a release date, not an individual specimen receipt date.

For a later capture, use `fetch_public.py --output snapshots/new_capture`, preserve the earlier directory, run preflight, then compare releases with `compare_snapshots.py`. Capture dates are observations of availability, not proof of the provider's first release time.

## Checks before relying on a result

The operator should verify the source URL and scope, read the capture date, and inspect all row findings. Check whether counts mean tests, people, or events; whether participation or testing changed; and whether the selected period fits the question. Read [the evidence review](literature-review.md) before interpreting timeliness. The 50% denominator-change setting is an adjustable review diagnostic, not a scientific validity cutoff.

## Known limits

There is one genuine CDC capture, so the bundled project cannot measure historical revision rates. There are no laboratory-level reporting denominators or linked patient records. The preflight checks are structural and reproducible, not evidence of national representativeness, laboratory accuracy, clinical performance, or readiness for operational surveillance.

## Next improvements

1. Archive scheduled captures with explicit retention. Acceptance: two independently retrieved, dated releases reproduce a comparison without changing either original.
2. Add contract migration fixtures. Acceptance: a documented provider schema change is rejected by version 1.0 and accepted only by a separately tested migration.
3. Add laboratory participation denominators if publicly documented. Acceptance: coverage states its exact eligible-laboratory definition and never substitutes extract completeness.
4. Add a machine-readable finding taxonomy. Acceptance: each existing failure has a stable code and tests prove that codes preserve missing-versus-zero distinctions.
