"""Exercise spreadsheet-safe exports while retaining raw audit evidence."""
from copy import deepcopy
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from csv_export import spreadsheet_safe_rows
from public_audit import write_csv


def write_input(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_output(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


class CsvExportTests(unittest.TestCase):
    def run_cli(self, script, *arguments):
        # Explicit UTF-8 exercises BOM text independently of the OS locale.
        result = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "src" / script), *map(str, arguments)],
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_shared_rows_escape_strings_and_preserve_types_and_source(self):
        formula_values = [prefix + formula for prefix in ["", " ", "\t", "\r\n", "\v", "\f", "\ufeff", " \t\ufeff"]
                          for formula in ["=1+1", "+1+1", "-1+1", "@SUM(1,2)"]]
        values = formula_values + ["ordinary", "café", "", "'=1+1", "value,with\nlines"]
        rows = [{"text": value, "negative_integer": -1, "negative_fraction": -0.5,
                 "missing": None, "zero": 0, "flag": False} for value in values]
        original = deepcopy(rows)
        exported = list(spreadsheet_safe_rows(iter(rows)))
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(exported)
        written = list(csv.DictReader(io.StringIO(output.getvalue(), newline="")))
        for index, (value, row) in enumerate(zip(values, written)):
            with self.subTest(value=value):
                self.assertEqual(row["text"], "'" + value if index < len(formula_values) else value)
                self.assertEqual(row["negative_integer"], "-1")
                self.assertEqual(row["negative_fraction"], "-0.5")
                self.assertEqual(row["missing"], "")
                self.assertEqual(row["zero"], "0")
                self.assertEqual(row["flag"], "False")
                self.assertIs(type(exported[index]["negative_integer"]), int)
                self.assertIs(type(exported[index]["negative_fraction"]), float)
                self.assertIsNone(exported[index]["missing"])
                self.assertIs(exported[index]["flag"], False)
        self.assertEqual(rows, original)

    def test_audit_cli_escapes_sites_and_invalid_weeks_but_keeps_json(self):
        sites = ["ordinary", "=1+1", "+1+1", "-1+1", "@SUM(1,2)", "\ufeff=1+1"]
        invalid_weeks = [prefix + "=1+1" for prefix in ["", " ", "\t", "\r\n", "\v", "\f", "\ufeff"]]
        calendar = [{"site_id": name, "week_start": "2026-01-05"} for name in sites]
        reports = [{"site_id": name, "week_start": "2026-01-05", "positive_tests": "1",
                    "tests_performed": "10", "reported_on": "2026-01-20"} for name in sites]
        reports += [{**reports[0], "week_start": week} for week in invalid_weeks]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calendar_path, reports_path, output = root / "calendar.csv", root / "reports.csv", root / "out"
            write_input(calendar_path, ["site_id", "week_start"], calendar)
            write_input(reports_path, ["site_id", "week_start", "positive_tests", "tests_performed", "reported_on"], reports)
            before = [calendar_path.read_bytes(), reports_path.read_bytes()]
            self.run_cli("audit.py", "--calendar", calendar_path, "--reports", reports_path, "--output", output)
            slots, findings = read_output(output / "slots.csv"), read_output(output / "findings.csv")
            raw = json.loads((output / "audit.json").read_text(encoding="utf-8"))
            expected_sites = {sites[0], *("'" + site for site in sites[1:])}
            self.assertEqual({row["site_id"] for row in slots}, expected_sites)
            self.assertEqual({row["site_id"] for row in findings if row["code"] == "late_report"}, expected_sites)
            self.assertEqual({row["week_start"] for row in findings if row["code"] == "invalid_week_start"}, {"'" + week for week in invalid_weeks})
            self.assertEqual({row["site_id"] for row in raw["slots"]}, set(sites))
            self.assertEqual({row["week_start"] for row in raw["findings"] if row["code"] == "invalid_week_start"}, set(invalid_weeks))
            self.assertTrue(all(row["positive_tests"] == 1 for row in raw["slots"]))
            self.assertEqual([calendar_path.read_bytes(), reports_path.read_bytes()], before)

    def test_audit_empty_findings_keep_header_and_missing_values(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calendar, reports, output = root / "calendar.csv", root / "reports.csv", root / "out"
            write_input(calendar, ["site_id", "week_start"], [{"site_id": "ordinary", "week_start": "2026-01-05"}])
            write_input(reports, ["site_id", "week_start", "positive_tests", "tests_performed", "reported_on"], [])
            self.run_cli("audit.py", "--calendar", calendar, "--reports", reports, "--output", output)
            self.assertEqual((output / "findings.csv").read_text(), "row,site_id,week_start,severity,code\n")
            self.assertEqual(read_output(output / "slots.csv")[0]["positive_tests"], "")
            self.assertIsNone(json.loads((output / "audit.json").read_text())["slots"][0]["positive_tests"])

    def test_vintage_cli_preserves_negative_deltas_errors_and_missingness(self):
        sites = ["ordinary", "=1+1", "+1+1", "-1+1", "@SUM(1,2)", "\ufeff=1+1"]
        expected = [{"site_id": name, "week_end": "2026-10-03"} for name in sites + ["missing", "invalid"]]
        observations = [{"site_id": name, "week_end": "2026-10-03", "issued_on": issued,
                         "positive_tests": positive, "tests_performed": tests}
                        for name in sites
                        for issued, positive, tests in [("2026-10-06", "3", "20"), ("2026-10-15", "2", "19")]]
        observations.append({"site_id": "invalid", "week_end": "2026-10-03", "issued_on": "2026-10-06",
                             "positive_tests": "bad", "tests_performed": "bad"})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected_path, observations_path, output = root / "expected.csv", root / "observations.csv", root / "out"
            write_input(expected_path, ["site_id", "week_end"], expected)
            write_input(observations_path, ["site_id", "week_end", "issued_on", "positive_tests", "tests_performed"], observations)
            before = [expected_path.read_bytes(), observations_path.read_bytes()]
            self.run_cli("vintage_audit.py", "--expected", expected_path, "--observations", observations_path,
                         "--as-of", "2026-10-20", "--output", output)
            rows = {row["site_id"]: row for row in read_output(output / "snapshot.csv")}
            raw = json.loads((output / "snapshot.json").read_text(encoding="utf-8"))
            self.assertEqual(set(rows), {"ordinary", "missing", "invalid", *("'" + site for site in sites[1:])})
            for name in sites:
                exported_name = name if name == "ordinary" else "'" + name
                self.assertEqual(rows[exported_name]["revision_positive_delta"], "-1")
                self.assertEqual(rows[exported_name]["revision_test_delta"], "-1")
            self.assertEqual(rows["missing"]["positive_tests"], "")
            self.assertEqual(rows["invalid"]["errors"], "invalid_positive_tests;invalid_tests_performed")
            self.assertEqual({row["site_id"] for row in raw["slots"]}, set(sites + ["missing", "invalid"]))
            self.assertTrue(all(row["revision_positive_delta"] == -1 for row in raw["slots"] if row["site_id"] in sites))
            self.assertEqual([expected_path.read_bytes(), observations_path.read_bytes()], before)

    def test_public_writer_uses_shared_escape_without_changing_negative_numbers(self):
        rows = [{"pathogen": "=1+1", "test_delta": -1, "relative_change": -0.5, "missing": None, "flag": False},
                {"pathogen": "Adenovirus", "test_delta": 0, "relative_change": 0.0, "missing": None, "flag": True}]
        original = deepcopy(rows)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "comparison.csv"
            write_csv(path, rows)
            output = read_output(path)
        self.assertEqual(output[0], {"pathogen": "'=1+1", "test_delta": "-1", "relative_change": "-0.5", "missing": "", "flag": "False"})
        self.assertEqual(output[1]["pathogen"], "Adenovirus")
        self.assertEqual(rows, original)


if __name__ == "__main__":
    unittest.main()
