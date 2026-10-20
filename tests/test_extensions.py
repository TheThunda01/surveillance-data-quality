from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from public_audit import audit_snapshot, load_snapshot, trailing_sensitivity
from compare_snapshots import compare
from vintage_audit import reconstruct

SELECTION={'level':'National','subtype':'Combined Type','pathogens':['Adenovirus'],'first_week_end':'2026-01-03','last_week_end':'2026-01-03'}
def public_row(**changes):
    row={'mmwrweek_end':'2026-01-03T00:00:00.000','level':'National','state':'','tests':'100','detections':'5','percent_pos':'5.00','subtype':'Combined Type','pathogen':'Adenovirus','posted':'2026-10-16T00:00:00.000','tests_3wma':'.','detections_5wma':'.','percent_pos_3wma':'.'}
    row.update(changes);return row

EXPECTED=[{'site_id':'A','week_end':'2026-10-03'}]
def vintage(issued='2026-10-06',positive='2',tests='20'):
    return {'site_id':'A','week_end':'2026-10-03','issued_on':issued,'positive_tests':positive,'tests_performed':tests}

class PublicDataTests(unittest.TestCase):
    def test_pinned_real_snapshot(self):
        rows,manifest=load_snapshot(ROOT/'data/public')
        result=audit_snapshot(rows,manifest['selection'])
        self.assertEqual(result['input_rows'],123)
        self.assertEqual(result['expected_rows'],123)
        self.assertEqual([(s['detections'],s['tests']) for s in result['summary']],[(21057,799289),(24375,791964),(23015,875604)])
        self.assertTrue(all(s['usable_weeks']==41 for s in result['summary']))

    def test_snapshot_tampering_fails(self):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)
            manifest=json.loads((ROOT/'data/public/manifest.json').read_text())
            manifest['sha256']='wrong'
            path.joinpath('manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,'SHA-256'):load_snapshot(path)

    def test_public_missing_not_zero(self):
        result=audit_snapshot([],SELECTION)
        self.assertEqual(result['slots'][0]['status'],'absent_from_extract')
        self.assertIsNone(result['slots'][0]['tests'])
        self.assertIsNone(result['summary'][0]['pooled_percent_positive'])

    def test_suppression_retained(self):
        result=audit_snapshot([public_row(tests='*',detections='*')],SELECTION)
        self.assertEqual(result['slots'][0]['status'],'suppressed')
        self.assertEqual(result['summary'][0]['usable_weeks'],0)

    def test_unavailable_retained(self):
        result=audit_snapshot([public_row(tests='.')],SELECTION)
        self.assertEqual(result['slots'][0]['status'],'unavailable')

    def test_duplicate_public_key_quarantined(self):
        result=audit_snapshot([public_row(),public_row()],SELECTION)
        self.assertEqual(result['slots'][0]['status'],'invalid')
        self.assertEqual(result['summary'][0]['tests'],0)

    def test_bad_percentage_is_not_silently_recomputed(self):
        result=audit_snapshot([public_row(percent_pos='7.00')],SELECTION)
        self.assertEqual(result['slots'][0]['status'],'invalid')

    def test_rounding_boundary_allowed(self):
        row=public_row(tests='20000',detections='201',percent_pos='1.00')
        self.assertEqual(audit_snapshot([row],SELECTION)['slots'][0]['status'],'usable')

    def test_zero_denominator_is_undefined(self):
        result=audit_snapshot([public_row(tests='0',detections='0',percent_pos='0.00')],SELECTION)
        self.assertIsNone(result['slots'][0]['calculated_percent_positive'])
        self.assertEqual(result['summary'][0]['zero_test_weeks'],1)

    def test_out_of_selection_rejected(self):
        with self.assertRaises(ValueError):audit_snapshot([public_row(level='State')],SELECTION)

    def test_nan_percentage_rejected(self):
        result=audit_snapshot([public_row(percent_pos='NaN')],SELECTION)
        self.assertEqual(result['slots'][0]['status'],'invalid')

    def test_sensitivity_does_not_change_source_counts(self):
        result=audit_snapshot([public_row()],SELECTION)
        before=deepcopy(result)
        rows=trailing_sensitivity(result,date(2026,1,10),[0,14])
        self.assertEqual(rows[0]['tests'],100)
        self.assertEqual(rows[1]['tests'],0)
        self.assertEqual(result,before)

    def test_comparison_detects_downward_correction(self):
        meta={'dataset_id':'rgnm-fkqb','selection':SELECTION,'retrieved_at_utc':'2026-10-20T00:00:00+00:00','sha256':'old'}
        new={**meta,'retrieved_at_utc':'2026-10-21T00:00:00+00:00','sha256':'new'}
        result=compare([public_row()],meta,[public_row(detections='4',percent_pos='4.00')],new)
        self.assertEqual(result['changed_slots'],1)
        self.assertEqual(result['slots'][0]['detection_delta'],-1)

    def test_comparison_rejects_unequal_selection(self):
        meta={'dataset_id':'rgnm-fkqb','selection':SELECTION,'retrieved_at_utc':'2026-10-20T00:00:00+00:00','sha256':'old'}
        with self.assertRaises(ValueError):compare([],meta,[],{**meta,'dataset_id':'other'})

class VintageTests(unittest.TestCase):
    def test_future_revision_is_excluded(self):
        rows=[vintage(),vintage('2026-10-15','3','30')]
        result=reconstruct(rows,EXPECTED,date(2026,10,10))
        self.assertEqual(result['summary']['positive_tests'],2)
        self.assertEqual(result['summary']['future_versions_excluded'],1)

    def test_revision_replaces_not_adds(self):
        result=reconstruct([vintage(),vintage('2026-10-15','3','30')],EXPECTED,date(2026,10,20))
        self.assertEqual(result['summary']['positive_tests'],3)
        self.assertEqual(result['summary']['tests_performed'],30)

    def test_downward_revision_is_legitimate(self):
        result=reconstruct([vintage(positive='3'),vintage('2026-10-15','2','19')],EXPECTED,date(2026,10,20))
        self.assertEqual(result['slots'][0]['revision_positive_delta'],-1)
        self.assertEqual(result['slots'][0]['revision_test_delta'],-1)

    def test_not_due_is_not_missing(self):
        result=reconstruct([],EXPECTED,date(2026,10,5))
        self.assertEqual(result['summary']['expected_due_slots'],0)
        self.assertEqual(result['summary']['unreported_due_slots'],0)
        self.assertIsNone(result['summary']['usable_due_coverage'])

    def test_no_report_is_unreported_after_grace(self):
        result=reconstruct([],EXPECTED,date(2026,10,20))
        self.assertEqual(result['summary']['unreported_due_slots'],1)
        self.assertIsNone(result['slots'][0]['positive_tests'])

    def test_known_zero_preserved(self):
        result=reconstruct([vintage(positive='0')],EXPECTED,date(2026,10,20))
        self.assertEqual(result['slots'][0]['positivity'],0)
        self.assertEqual(result['summary']['usable_due_slots'],1)

    def test_latest_invalid_revision_does_not_restore_old(self):
        result=reconstruct([vintage(),vintage('2026-10-15','30','20')],EXPECTED,date(2026,10,20))
        self.assertEqual(result['slots'][0]['status'],'available_invalid')
        self.assertEqual(result['summary']['tests_performed'],0)

    def test_same_vintage_conflict_fails(self):
        with self.assertRaisesRegex(ValueError,'ambiguous'):reconstruct([vintage(),vintage(positive='3')],EXPECTED,date(2026,10,20))

    def test_issue_before_week_fails(self):
        with self.assertRaisesRegex(ValueError,'precedes'):reconstruct([vintage('2026-10-02')],EXPECTED,date(2026,10,20))

    def test_unsorted_input_has_same_result(self):
        rows=[vintage(),vintage('2026-10-15','3','30')]
        a=reconstruct(rows,EXPECTED,date(2026,10,20));b=reconstruct(rows[::-1],EXPECTED,date(2026,10,20))
        self.assertEqual(a['summary'],b['summary'])
        self.assertEqual(a['slots'][0]['positive_tests'],b['slots'][0]['positive_tests'])

if __name__=='__main__':unittest.main()
