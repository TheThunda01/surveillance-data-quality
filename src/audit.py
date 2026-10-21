"""Audit synthetic aggregate laboratory reports without silently repairing records."""
from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from statistics import median

from csv_export import spreadsheet_safe_rows

ROOT = Path(__file__).resolve().parents[1]
REPORT_COLUMNS = {"site_id", "week_start", "positive_tests", "tests_performed", "reported_on"}
CALENDAR_COLUMNS = {"site_id", "week_start"}


def read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or set(reader.fieldnames) != required or len(reader.fieldnames) != len(required):
            raise ValueError(f"{path.name}: columns must be exactly {sorted(required)}")
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"{path.name}: malformed CSV row width")
    return rows


def parse_date(value: str) -> date:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("date must use YYYY-MM-DD")
    return date.fromisoformat(value)


def nonnegative_integer(value: str) -> int:
    if not re.fullmatch(r"0|[1-9][0-9]*", value):
        raise ValueError("value must be a nonnegative integer without padding")
    # SQLite integers are signed 64-bit. Reject overflow before insertion.
    parsed = int(value)
    if parsed > 2**63 - 1:
        raise ValueError("integer exceeds SQLite's supported range")
    return parsed


def audit(reports: list[dict[str, str]], calendar: list[dict[str, str]], late_after_days: int = 7) -> dict:
    if late_after_days < 0:
        raise ValueError("late_after_days must be nonnegative")
    expected = set()
    for row in calendar:
        if not row["site_id"] or row["site_id"] != row["site_id"].strip():
            raise ValueError("calendar site_id must be nonblank and have no surrounding whitespace")
        start = parse_date(row["week_start"])
        if start.weekday() != 0:
            raise ValueError("calendar week_start must be a Monday")
        key = (row["site_id"], row["week_start"])
        if key in expected:
            raise ValueError(f"duplicate calendar key: {key}")
        expected.add(key)
    if not expected:
        raise ValueError("calendar must contain at least one expected report")
    keys: dict[tuple[str, str], list[int]] = {}
    for number, row in enumerate(reports, 2):
        keys.setdefault((row["site_id"], row["week_start"]), []).append(number)
    findings, normalized = [], []
    for number, row in enumerate(reports, 2):
        errors = []
        key = (row["site_id"], row["week_start"])
        if key not in expected:
            errors.append("unexpected_site_week")
        if len(keys[key]) > 1:
            errors.append("duplicate_site_week")
        start = reported = None
        try:
            start = parse_date(row["week_start"])
            if start.weekday() != 0:
                errors.append("week_start_not_monday")
        except (ValueError, OverflowError):
            errors.append("invalid_week_start")
        try:
            reported = parse_date(row["reported_on"])
        except (ValueError, OverflowError):
            errors.append("invalid_reported_on")
        counts = {}
        for field in ("positive_tests", "tests_performed"):
            try:
                counts[field] = nonnegative_integer(row[field])
            except (ValueError, OverflowError):
                errors.append(f"invalid_{field}")
        if len(counts) == 2 and counts["positive_tests"] > counts["tests_performed"]:
            errors.append("positive_tests_exceed_tests")
        delay = None
        if start is not None and reported is not None:
            delay = (reported - (start + timedelta(days=6))).days
            if delay < 0:
                errors.append("reported_before_week_end")
        for code in errors:
            findings.append({"row": number, "site_id": row["site_id"], "week_start": row["week_start"], "severity": "error", "code": code})
        if not errors and delay is not None and delay > late_after_days:
            findings.append({"row": number, "site_id": row["site_id"], "week_start": row["week_start"], "severity": "review", "code": "late_report"})
        normalized.append((number, *key, counts.get("positive_tests"), counts.get("tests_performed"), delay, int(not errors)))
    if any(sum(r[index] for r in normalized if r[6]) > 2**63 - 1 for index in (3, 4)):
        raise ValueError("aggregate counts exceed SQLite integer range")
    with sqlite3.connect(":memory:") as database:
        database.row_factory = sqlite3.Row
        database.executescript((ROOT / "sql/schema.sql").read_text())
        database.executemany("INSERT INTO expected VALUES (?, ?)", sorted(expected))
        database.executemany("INSERT INTO reports VALUES (?, ?, ?, ?, ?, ?, ?)", normalized)
        slots = [dict(row) for row in database.execute((ROOT / "sql/slots.sql").read_text())]
        totals = dict(database.execute((ROOT / "sql/totals.sql").read_text()).fetchone())
    delays = [r[5] for r in normalized if r[6]]
    summary = {
        "data_status": "synthetic demonstration; no real people or sites",
        "expected_site_weeks": len(expected),
        "input_rows": len(reports),
        "received_site_weeks": sum(r["received_rows"] > 0 for r in slots),
        "missing_site_weeks": sum(r["status"] == "missing" for r in slots),
        "invalid_site_weeks": sum(r["status"] == "invalid" for r in slots),
        "usable_site_weeks": sum(r["status"] == "usable" for r in slots),
        "usable_fraction": sum(r["status"] == "usable" for r in slots) / len(expected),
        "excluded_input_rows": sum(not r[6] for r in normalized),
        "late_usable_reports": sum(r[6] and r[5] > late_after_days for r in normalized),
        "late_after_days": late_after_days,
        "median_delay_days_usable": median(delays) if delays else None,
        **totals,
    }
    return {"summary": summary, "slots": slots, "findings": findings}


def save(result: dict, output: Path, source_paths: list[Path]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    result["provenance"] = {
        "inputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
        "method": "row validation, quarantine, then expected-calendar SQL left join",
        "version": "1.0.0",
    }
    (output / "audit.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    for name, columns in [("slots", ["site_id", "week_start", "received_rows", "status", "positive_tests", "tests_performed", "positivity", "delay_days"]), ("findings", ["row", "site_id", "week_start", "severity", "code"])]:
        with (output / f"{name}.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            writer.writerows(spreadsheet_safe_rows(result[name]))
    summary = result["summary"]
    pct = summary["pooled_positivity"]
    value = "undefined (no usable tested samples)" if pct is None else f"{100*pct:.2f}%"
    lines = ["# Synthetic surveillance audit", "", "These are invented aggregate records. No result describes an actual population.", "", "| Measure | Result |", "| --- | --- |"]
    lines.extend(f"| {k.replace('_', ' ')} | {v} |" for k, v in summary.items() if k != "data_status")
    lines += ["", f"Pooled test positivity is **{value}**, using only usable records. It is not a population prevalence estimate.", "", "Missing slots remain missing. Every duplicated key is quarantined in full; no version is selected automatically. Review findings.csv before changing the source data.", "", "Input fingerprints and row-level reasons are in audit.json.", ""]
    (output / "report.md").write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, default=ROOT / "data/reports.csv")
    parser.add_argument("--calendar", type=Path, default=ROOT / "data/calendar.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    parser.add_argument("--late-after-days", type=int, default=7)
    args = parser.parse_args()
    try:
        if any(p.resolve().is_relative_to(args.output.resolve()) for p in (args.reports, args.calendar)):
            raise ValueError("output directory must not contain either input file")
        result = audit(read_csv(args.reports, REPORT_COLUMNS), read_csv(args.calendar, CALENDAR_COLUMNS), args.late_after_days)
        save(result, args.output, [args.reports, args.calendar])
    except (ValueError, OSError, csv.Error, sqlite3.Error) as error:
        parser.exit(2, f"audit failed: {error}\n")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
