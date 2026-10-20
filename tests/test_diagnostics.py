from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from diagnostics import CATALOG, CODES, DiagnosticError, envelope, exception_finding
from public_audit import audit_snapshot
from snapshot_contract import validate_manifest
from validate_snapshot import preflight


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path=Path(self.directory.name)
        shutil.copytree(ROOT/'data/public',self.path,dirs_exist_ok=True)
        self.manifest=json.loads((self.path/'manifest.json').read_text())
        with (self.path/self.manifest['data_file']).open() as stream:
            self.rows=list(csv.DictReader(stream))
        self.row=self.rows[0]
        self.selection={'level':'National','subtype':'Combined Type','pathogens':[self.row['pathogen']],
                        'first_week_end':self.row['mmwrweek_end'][:10],'last_week_end':self.row['mmwrweek_end'][:10]}

    def write_manifest(self,manifest):
        (self.path/'manifest.json').write_text(json.dumps(manifest))

    def write_data(self,raw):
        (self.path/self.manifest['data_file']).write_bytes(raw)
        self.write_manifest({**self.manifest,'sha256':hashlib.sha256(raw).hexdigest(),'byte_length':len(raw)})

    def write_rows(self,rows):
        stream=io.StringIO(newline='')
        writer=csv.DictWriter(stream,fieldnames=list(self.row))
        writer.writeheader();writer.writerows(rows)
        self.write_data(stream.getvalue().encode())

    def assert_code(self,code,call):
        with self.assertRaises(DiagnosticError) as raised:call()
        item=raised.exception.finding
        self.assertEqual(item['code'],code)
        self.assertEqual(item['severity'],CODES[code]['severity'])
        self.assertEqual(set(item['location']),{'scope','field','line','pathogen','week_end'})
        return item

    def test_catalog_and_schema_agree(self):
        schema=json.loads((ROOT/'schemas/preflight-diagnostics-v1.schema.json').read_text())
        self.assertEqual(set(schema['properties']['findings']['items']['properties']['code']['enum']),set(CODES))
        self.assertEqual(CATALOG['diagnostics_version'],'1.0')
        self.assertEqual(len(CODES),len(CATALOG['codes']))

    def test_manifest_codes_identify_actual_failure(self):
        cases=[('sha256','z'*64,'DIGEST_FORMAT'),('data_file','../x','FILENAME_INVALID'),
               ('metadata_file',self.manifest['data_file'],'FILENAME_COLLISION'),
               ('byte_length',True,'BYTE_LENGTH_INVALID'),('dataset_id','other','DATASET_UNSUPPORTED'),
               ('source_page',None,'SOURCE_URL_INVALID'),('download_url','https://[bad','SOURCE_URL_INVALID'),
               ('retrieved_at_utc','2026-10-20','CAPTURE_TIMESTAMP_INVALID')]
        for field,value,code in cases:
            with self.subTest(field=field):
                item=self.assert_code(code,lambda:validate_manifest({**self.manifest,field:value}))
                self.assertEqual(item['location']['field'],field)
        for field,value,code in [('level','State','SELECTION_SCOPE_INVALID'),('pathogens',[],'SELECTION_SERIES_INVALID'),
                                 ('first_week_end','bad','SELECTION_DATE_INVALID'),
                                 ('last_week_end','2027-01-02','SELECTION_WINDOW_INVALID')]:
            with self.subTest(field=field):
                self.assert_code(code,lambda:validate_manifest({**self.manifest,'selection':{**self.manifest['selection'],field:value}}))
        self.assert_code('MANIFEST_TYPE',lambda:validate_manifest([]))

    def test_digest_and_length_codes_are_not_confused(self):
        self.write_manifest({**self.manifest,'sha256':'0'*64})
        self.assert_code('DATA_DIGEST_MISMATCH',lambda:preflight(self.path))
        self.write_manifest({**self.manifest,'byte_length':1})
        self.assert_code('DATA_LENGTH_MISMATCH',lambda:preflight(self.path))
        self.write_manifest({**self.manifest,'metadata_sha256':'0'*64})
        self.assert_code('METADATA_DIGEST_MISMATCH',lambda:preflight(self.path))

    def test_metadata_shape_and_syntax_have_distinct_codes(self):
        original=json.loads((self.path/self.manifest['metadata_file']).read_text())
        for raw,code in [(b'{','JSON_INVALID'),(json.dumps([]).encode(),'METADATA_IDENTITY_MISMATCH'),
                         (json.dumps({**original,'columns':[]}).encode(),'METADATA_COLUMNS_INVALID')]:
            (self.path/self.manifest['metadata_file']).write_bytes(raw)
            self.write_manifest({**self.manifest,'metadata_sha256':hashlib.sha256(raw).hexdigest()})
            with self.subTest(code=code):self.assert_code(code,lambda:preflight(self.path))

    def test_csv_schema_width_and_syntax_have_distinct_codes(self):
        self.write_data(b'wrong\n1\n')
        self.assert_code('CSV_SCHEMA_INVALID',lambda:preflight(self.path))
        header=','.join(self.row)+'\n'
        self.write_data((header+'1,2\n').encode())
        self.assert_code('CSV_ROW_WIDTH_INVALID',lambda:preflight(self.path))
        self.write_data((header+','.join(list(self.row.values())[:-1])+',"unfinished\n').encode())
        self.assert_code('CSV_PARSE_INVALID',lambda:preflight(self.path))

    def test_capture_and_observation_errors_have_locations(self):
        self.write_manifest({**self.manifest,'retrieved_at_utc':'2026-10-10T00:00:00+00:00'})
        item=self.assert_code('RELEASE_AFTER_CAPTURE',lambda:preflight(self.path))
        self.assertEqual(item['location']['line'],2)
        self.assertEqual(item['location']['field'],'posted')
        self.write_manifest(self.manifest)
        for field,value,code in [('mmwrweek_end','bad','OBSERVATION_DATE_INVALID'),
                                 ('state','NY','OBSERVATION_OUTSIDE_SELECTION')]:
            with self.subTest(field=field):
                self.write_rows([{**self.row,field:value}])
                self.assert_code(code,lambda:preflight(self.path))

    def test_row_findings_preserve_zero_missing_and_exclusion_rules(self):
        cases=[([], 'OBSERVATION_MISSING'),([self.row,self.row],'OBSERVATION_DUPLICATE'),
               ([{**self.row,'posted':'bad'}],'OBSERVATION_RELEASE_INVALID'),
               ([{**self.row,'tests':'*'}],'OBSERVATION_SUPPRESSED'),
               ([{**self.row,'tests':'.'}],'OBSERVATION_UNAVAILABLE'),
               ([{**self.row,'detections':'-1'}],'OBSERVATION_VALUES_INVALID'),
               ([{**self.row,'percent_pos':'99.00'}],'OBSERVATION_PERCENT_MISMATCH'),
               ([{**self.row,'tests':'0','detections':'0','percent_pos':'0.00'}],'OBSERVATION_ZERO_TESTS')]
        for rows,code in cases:
            with self.subTest(code=code):
                findings=[];original=deepcopy(rows)
                result=audit_snapshot(rows,self.selection,findings)
                self.assertEqual(rows,original)
                self.assertEqual([f['code'] for f in findings],[code])
                self.assertEqual(findings[0]['location']['pathogen'],self.row['pathogen'])
                self.assertEqual(findings[0]['severity'],'info' if code.endswith('ZERO_TESTS') else 'review')
                self.assertEqual(result,audit_snapshot(rows,self.selection))

    def test_cli_opt_in_errors_and_legacy_success(self):
        command=[sys.executable,str(ROOT/'src/validate_snapshot.py'),'--snapshot',str(self.path)]
        clean=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(clean.returncode,0)
        self.assertEqual(json.loads(clean.stdout),json.loads((ROOT/'examples/snapshot_preflight.json').read_text()))
        (self.path/'manifest.json').write_text('{')
        legacy=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(legacy.returncode,2)
        self.assertEqual(legacy.stdout,'')
        self.assertTrue(legacy.stderr.startswith('snapshot preflight failed:'))
        machine=subprocess.run(command+['--diagnostics-json'],capture_output=True,text=True)
        self.assertEqual(machine.returncode,2)
        self.assertEqual(machine.stderr,'')
        report=json.loads(machine.stdout)
        self.assertEqual(report['status'],'rejected');self.assertIsNone(report['summary'])
        self.assertEqual(report['findings'][0]['code'],'JSON_INVALID')

    def test_external_exception_categories_are_honest(self):
        self.assertEqual(exception_finding(FileNotFoundError('missing'))['code'],'FILE_IO_ERROR')
        self.assertEqual(exception_finding(UnicodeDecodeError('utf8',b'\xff',0,1,'bad'))['code'],'TEXT_ENCODING_INVALID')
        self.assertEqual(exception_finding(ValueError('unclassified'))['code'],'VALIDATION_FAILED')
        data=self.path/self.manifest['data_file'];data.unlink();data.symlink_to(ROOT/'data/public'/self.manifest['data_file'])
        self.assert_code('SNAPSHOT_SYMLINK',lambda:preflight(self.path))

    def test_success_and_review_envelope_exit_codes(self):
        clean=preflight(self.path);self.assertEqual(envelope(clean,[])['status'],'passed')
        self.write_rows(self.rows[1:]);findings=[]
        summary=preflight(self.path,findings);report=envelope(summary,findings)
        self.assertEqual(report['status'],'review');self.assertEqual(report['exit_code'],0)
        self.assertEqual(findings[0]['code'],'OBSERVATION_MISSING')


if __name__=='__main__':unittest.main()
