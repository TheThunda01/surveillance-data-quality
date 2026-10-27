import csv
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from plot_denominator_context import load_context


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        for name in ("weekly_audit.csv", "trailing_window_sensitivity.csv"):
            shutil.copyfile(ROOT / "results_public" / name, self.path / name)

    def change(self, name, action):
        path = self.path / name
        with path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            fields, rows = reader.fieldnames, list(reader)
        action(rows)
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_saved_counts_reconcile_all_windows(self):
        weeks, windows = load_context(self.path)
        self.assertEqual(sum(map(len, weeks.values())), 123)
        self.assertEqual(sum(map(len, windows.values())), 12)
        self.assertGreater(windows["HMPV"][-1]["delta_pp"], .18)

    def test_duplicate_week_rejected(self):
        self.change("weekly_audit.csv", lambda rows: rows.append(rows[0].copy()))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            load_context(self.path)

    def test_missing_slot_not_bridged(self):
        self.change("weekly_audit.csv", lambda rows: rows.pop(2))
        with self.assertRaisesRegex(ValueError, "explicit missing-week"):
            load_context(self.path)

    def test_mismatched_sensitivity_rejected(self):
        self.change("trailing_window_sensitivity.csv", lambda rows: rows[0].update(tests="1"))
        with self.assertRaisesRegex(ValueError, "tests disagrees"):
            load_context(self.path)

    def test_exclusion_label_must_match_cutoff(self):
        self.change("trailing_window_sensitivity.csv", lambda rows: rows[3].update(exclude_weeks_newer_than_days="365"))
        with self.assertRaisesRegex(ValueError, "common analysis date"):
            load_context(self.path)

    def test_nan_is_not_a_plotted_value(self):
        self.change("trailing_window_sensitivity.csv", lambda rows: rows[0].update(pooled_percent_positive="nan"))
        with self.assertRaisesRegex(ValueError, "pooled_percent_positive disagrees"):
            load_context(self.path)

    def test_unusable_slots_and_zero_tests_remain_distinct(self):
        (self.path / "weekly_audit.csv").write_text(
            "pathogen,week_end,status,tests,detections\n"
            "Example,2026-01-03,usable,10,2\n"
            "Example,2026-01-10,suppressed,,\n"
            "Example,2026-01-17,usable,0,0\n", encoding="utf-8")
        (self.path / "trailing_window_sensitivity.csv").write_text(
            "pathogen,exclude_weeks_newer_than_days,latest_eligible_week_end,eligible_expected_weeks,usable_weeks,tests,detections,pooled_percent_positive,retained_test_denominator_fraction,change_from_all_weeks_pp\n"
            "Example,0,2026-01-17,3,2,10,2,20,1,0\n", encoding="utf-8")
        rows, _ = load_context(self.path)
        self.assertIsNone(rows["Example"][1]["tests"])
        self.assertEqual(rows["Example"][2]["tests"], 0)

    def test_all_zero_denominator_stays_undefined(self):
        (self.path / "weekly_audit.csv").write_text(
            "pathogen,week_end,status,tests,detections\nExample,2026-01-03,usable,0,0\n", encoding="utf-8")
        (self.path / "trailing_window_sensitivity.csv").write_text(
            "pathogen,exclude_weeks_newer_than_days,latest_eligible_week_end,eligible_expected_weeks,usable_weeks,tests,detections,pooled_percent_positive,retained_test_denominator_fraction,change_from_all_weeks_pp\n"
            "Example,0,2026-01-03,1,1,0,0,,,\n", encoding="utf-8")
        _, windows = load_context(self.path)
        self.assertIsNone(windows["Example"][0]["delta_pp"])
        self.assertIsNone(windows["Example"][0]["retained"])


if __name__ == "__main__":
    unittest.main()
