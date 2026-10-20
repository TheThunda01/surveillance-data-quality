"""Tests for interpretation-preserving denominator diagnostics."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from public_audit import denominator_changes, audit_snapshot, load_snapshot


def slot(week,tests,status='usable',series='A'):
    return {'pathogen':series,'week_end':week,'tests':tests,'status':status}


class DenominatorChangeTests(unittest.TestCase):
    def test_increase_above_threshold(self):
        rows=denominator_changes([slot('2026-01-03',100),slot('2026-01-10',200)])['rows']
        self.assertEqual(rows[1]['test_count_ratio'],2)
        self.assertEqual(rows[1]['relative_test_count_change'],1)
        self.assertTrue(rows[1]['change_exceeds_threshold'])

    def test_exact_threshold_not_flagged(self):
        rows=denominator_changes([slot('2026-01-03',100),slot('2026-01-10',150)])['rows']
        self.assertFalse(rows[1]['change_exceeds_threshold'])

    def test_decrease_is_signed_and_flagged(self):
        rows=denominator_changes([slot('2026-01-03',100),slot('2026-01-10',40)])['rows']
        self.assertAlmostEqual(rows[1]['relative_test_count_change'],-0.6)
        self.assertTrue(rows[1]['change_exceeds_threshold'])

    def test_zero_previous_denominator_is_undefined(self):
        rows=denominator_changes([slot('2026-01-03',0),slot('2026-01-10',100)])['rows']
        self.assertEqual(rows[1]['diagnostic_status'],'previous_week_zero_tests')
        self.assertIsNone(rows[1]['test_count_ratio'])
        self.assertIsNone(rows[1]['change_exceeds_threshold'])

    def test_zero_current_tests_is_valid_decline(self):
        rows=denominator_changes([slot('2026-01-03',100),slot('2026-01-10',0)])['rows']
        self.assertEqual(rows[1]['test_count_ratio'],0)
        self.assertEqual(rows[1]['relative_test_count_change'],-1)
        self.assertTrue(rows[1]['change_exceeds_threshold'])

    def test_calendar_gap_is_not_bridged(self):
        rows=denominator_changes([slot('2026-01-03',100),slot('2026-01-17',200)])['rows']
        self.assertEqual(rows[1]['diagnostic_status'],'no_previous_calendar_week')
        self.assertIsNone(rows[1]['test_count_ratio'])

    def test_missing_previous_record_is_not_zero(self):
        rows=denominator_changes([slot('2026-01-03',None,'absent_from_extract'),slot('2026-01-10',100)])['rows']
        self.assertEqual(rows[1]['diagnostic_status'],'previous_week_unusable')
        self.assertIsNone(rows[1]['previous_tests'])
        self.assertIsNone(rows[1]['relative_test_count_change'])

    def test_suppression_is_not_interpreted_as_decline(self):
        rows=denominator_changes([slot('2026-01-03',100),slot('2026-01-10',None,'suppressed')])['rows']
        self.assertEqual(rows[1]['diagnostic_status'],'current_week_unusable')
        self.assertIsNone(rows[1]['relative_test_count_change'])

    def test_series_are_compared_separately(self):
        values=[slot('2026-01-03',100,series='A'),slot('2026-01-10',100,series='A'),slot('2026-01-03',10,series='B'),slot('2026-01-10',30,series='B')]
        summary=denominator_changes(values)['summary']
        self.assertEqual([r['flagged_pairs'] for r in summary],[0,1])

    def test_threshold_cannot_be_invalid(self):
        for threshold in [-0.5,float('inf'),float('nan')]:
            with self.subTest(threshold=threshold), self.assertRaises(ValueError):
                denominator_changes([],threshold)

    def test_diagnostic_does_not_mutate_validity_or_counts(self):
        source=[slot('2026-01-03',100),slot('2026-01-10',400)]
        before=deepcopy(source)
        self.assertTrue(denominator_changes(source)['rows'][1]['change_exceeds_threshold'])
        self.assertEqual(source,before)

    def test_public_snapshot_has_120_evaluable_pairs(self):
        rows,manifest=load_snapshot(ROOT/'data/public')
        diagnostics=denominator_changes(audit_snapshot(rows,manifest['selection'])['slots'])
        self.assertEqual(sum(r['evaluable_consecutive_pairs'] for r in diagnostics['summary']),120)
        self.assertEqual(sum(r['flagged_pairs'] for r in diagnostics['summary']),0)

if __name__=='__main__':unittest.main()
