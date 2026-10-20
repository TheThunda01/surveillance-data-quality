import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from audit import audit, nonnegative_integer, read_csv, save, REPORT_COLUMNS, CALENDAR_COLUMNS

CALENDAR = [{"site_id": "A", "week_start": "2026-01-05"}]
def row(**changes):
    result = {"site_id":"A", "week_start":"2026-01-05", "positive_tests":"0", "tests_performed":"10", "reported_on":"2026-01-13"}
    result.update(changes)
    return result

class AuditTests(unittest.TestCase):
    def test_zero_is_not_missing(self):
        result = audit([row()], CALENDAR)
        self.assertEqual(result["slots"][0]["status"], "usable")
        self.assertEqual(result["slots"][0]["positivity"], 0)
        self.assertEqual(result["summary"]["missing_site_weeks"], 0)

    def test_absence_is_missing(self):
        result = audit([], CALENDAR)
        self.assertEqual(result["slots"][0]["status"], "missing")
        self.assertIsNone(result["slots"][0]["positive_tests"])
        self.assertIsNone(result["summary"]["pooled_positivity"])

    def test_zero_tests_ratio_is_undefined(self):
        result = audit([row(tests_performed="0")], CALENDAR)
        self.assertIsNone(result["slots"][0]["positivity"])
        self.assertEqual(result["summary"]["usable_site_weeks"], 1)

    def test_all_duplicates_are_quarantined(self):
        result = audit([row(), row(positive_tests="1")], CALENDAR)
        self.assertEqual(result["summary"]["excluded_input_rows"], 2)
        self.assertEqual(result["summary"]["pooled_tests_performed"], 0)
        self.assertEqual(result["slots"][0]["status"], "invalid")

    def test_positive_cannot_exceed_tests(self):
        result = audit([row(positive_tests="11")], CALENDAR)
        self.assertIn("positive_tests_exceed_tests", [r["code"] for r in result["findings"]])
        self.assertEqual(result["summary"]["usable_site_weeks"], 0)

    def test_non_integer_counts_are_not_cast(self):
        for value in ["", "nan", "1.5", "-1", "1e2", " 2", "02"]:
            with self.subTest(value=value):
                result = audit([row(tests_performed=value)], CALENDAR)
                self.assertEqual(result["summary"]["excluded_input_rows"], 1)

    def test_sqlite_overflow_integer_rejected(self):
        with self.assertRaises(ValueError):
            nonnegative_integer(str(2**63))

    def test_aggregate_overflow_rejected(self):
        calendar = CALENDAR + [{"site_id":"B", "week_start":"2026-01-05"}]
        with self.assertRaisesRegex(ValueError, "aggregate counts"):
            audit([row(tests_performed=str(2**63-1)), row(site_id="B", tests_performed="1")], calendar)

    def test_reported_before_week_end_is_invalid(self):
        result = audit([row(reported_on="2026-01-10")], CALENDAR)
        self.assertEqual(result["summary"]["usable_site_weeks"], 0)

    def test_invalid_calendar_dates_fail(self):
        for week in ["2026-02-30", "2026-1-5", "2026-01-06"]:
            with self.subTest(week=week), self.assertRaises(ValueError):
                audit([], [{"site_id":"A", "week_start":week}])

    def test_duplicate_calendar_fails(self):
        with self.assertRaises(ValueError):
            audit([], CALENDAR * 2)

    def test_invalid_report_date_is_flagged(self):
        result = audit([row(reported_on="2026-13-05")], CALENDAR)
        self.assertIn("invalid_reported_on", [r["code"] for r in result["findings"]])

    def test_unknown_slot_does_not_change_denominator(self):
        result = audit([row(site_id="other")], CALENDAR)
        self.assertEqual(result["summary"]["expected_site_weeks"], 1)
        self.assertEqual(result["summary"]["missing_site_weeks"], 1)
        self.assertEqual(result["summary"]["pooled_tests_performed"], 0)

    def test_invalid_report_week_is_flagged(self):
        for week, code in [("2026-01-06", "week_start_not_monday"), ("broken", "invalid_week_start")]:
            result = audit([row(week_start=week)], CALENDAR)
            self.assertIn(code, [r["code"] for r in result["findings"]])

    def test_late_is_review_not_exclusion(self):
        result = audit([row(reported_on="2026-01-19")], CALENDAR)
        self.assertEqual(result["summary"]["usable_site_weeks"], 1)
        self.assertEqual(result["summary"]["late_usable_reports"], 1)
        self.assertEqual(result["summary"]["median_delay_days_usable"], 8)

    def test_pool_counts_not_site_proportions(self):
        calendar = CALENDAR + [{"site_id":"B", "week_start":"2026-01-05"}]
        result = audit([row(positive_tests="1", tests_performed="10"), row(site_id="B", positive_tests="9", tests_performed="90")], calendar)
        self.assertAlmostEqual(result["summary"]["pooled_positivity"], 0.1)
        result = audit([row(positive_tests="1", tests_performed="10"), row(site_id="B", positive_tests="45", tests_performed="90")], calendar)
        self.assertAlmostEqual(result["summary"]["pooled_positivity"], 0.46)

    def test_demo_expected_findings(self):
        result = audit(read_csv(ROOT/"data/reports.csv", REPORT_COLUMNS), read_csv(ROOT/"data/calendar.csv", CALENDAR_COLUMNS))
        expected = json.loads((ROOT/"data/expected_summary.json").read_text())
        for key,value in expected.items():
            self.assertEqual(result["summary"][key], value)

    def test_clean_has_no_errors(self):
        result = audit(read_csv(ROOT/"data/reports_clean.csv", REPORT_COLUMNS), read_csv(ROOT/"data/calendar.csv", CALENDAR_COLUMNS))
        self.assertEqual(result["summary"]["usable_site_weeks"], 12)
        self.assertFalse([r for r in result["findings"] if r["severity"] == "error"])
        # The intentionally slow report remains a review item in the clean fixture.
        self.assertEqual(result["summary"]["late_usable_reports"], 1)

    def test_output_is_deterministic_and_json_has_no_nan(self):
        result = audit([], CALENDAR)
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            source = ROOT / "data/calendar.csv"
            save(result, out, [source])
            original = (out/"audit.json").read_bytes()
            save(result, out, [source])
            self.assertEqual((out/"audit.json").read_bytes(), original)
            self.assertIsNone(json.loads(original)["summary"]["pooled_positivity"])

    def test_bad_schema_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            path.write_text("site_id,site_id\nA,A\n")
            with self.assertRaises(ValueError):
                read_csv(path, CALENDAR_COLUMNS)

if __name__ == "__main__":
    unittest.main()
