import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from snapshot_contract import validate_manifest
from validate_snapshot import preflight


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT/'data/public/manifest.json').read_text())

    def test_pinned_preflight_is_read_only(self):
        directory = ROOT/'data/public'
        before = {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()}
        result = preflight(directory)
        self.assertEqual(result['rows'], 123)
        self.assertEqual(result['expected_slots'], 123)
        self.assertFalse(result['review_required'])
        self.assertEqual(before, {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()})

    def test_bad_manifest_types_and_scope(self):
        changes = [('dataset_id', 'wrong'), ('sha256', 'z'*64), ('metadata_sha256', None),
                   ('data_file', '../external.csv'), ('metadata_file', 'nested\\file'),
                   ('byte_length', True), ('byte_length', 0),
                   ('download_url', 'https://example.org/resource/rgnm-fkqb.csv'),
                   ('retrieved_at_utc', '2026-10-20T12:00:00'),
                   ('retrieved_at_utc', '2026-10-20T12:00:00+01:00')]
        for key, value in changes:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_manifest({**self.manifest, key: value})
        with self.assertRaises(ValueError):
            validate_manifest([])

    def test_selection_constraints(self):
        for key, value in [('pathogens', 'Adenovirus'), ('pathogens', ['PIV','PIV']),
                           ('pathogens', ['other']), ('pathogens', []), ('level','State'),
                           ('first_week_end','2026-01-04'), ('last_week_end','2027-01-02'),
                           ('last_week_end','bad')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_manifest({**self.manifest, 'selection': {**self.manifest['selection'], key:value}})

    def test_source_page_is_required_and_identifies_supported_dataset(self):
        missing={key:value for key,value in self.manifest.items() if key!='source_page'}
        for manifest in [missing,{**self.manifest,'source_page':'https://example.org/data'}]:
            with self.subTest(manifest=manifest),self.assertRaisesRegex(ValueError,'source_page'):
                validate_manifest(manifest)

    def test_release_after_capture_rejected_and_same_calendar_day_allowed(self):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)
            shutil.copytree(ROOT/'data/public',path,dirs_exist_ok=True)
            manifest={**self.manifest,'retrieved_at_utc':'2026-10-10T00:00:00+00:00'}
            (path/'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,'posted release date follows snapshot capture date'):
                preflight(path)
            manifest['retrieved_at_utc']='2026-10-16T00:00:00+00:00'
            (path/'manifest.json').write_text(json.dumps(manifest))
            self.assertFalse(preflight(path)['review_required'])

    def test_metadata_identity_checked_even_when_hash_matches(self):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)
            shutil.copytree(ROOT/'data/public', path, dirs_exist_ok=True)
            metadata=json.loads((path/self.manifest['metadata_file']).read_text())
            metadata['id']='different'
            raw=(json.dumps(metadata)+'\n').encode()
            (path/self.manifest['metadata_file']).write_bytes(raw)
            manifest={**self.manifest,'metadata_sha256':hashlib.sha256(raw).hexdigest()}
            (path/'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,'identity'):preflight(path)

    def test_declared_length_and_metadata_schema_checked(self):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)
            shutil.copytree(ROOT/'data/public',path,dirs_exist_ok=True)
            manifest={**self.manifest,'byte_length':1}
            (path/'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,'byte_length'):preflight(path)
            metadata=json.loads((path/self.manifest['metadata_file']).read_text())
            metadata['columns']=[]
            raw=json.dumps(metadata).encode()
            (path/self.manifest['metadata_file']).write_bytes(raw)
            manifest={**self.manifest,'metadata_sha256':hashlib.sha256(raw).hexdigest()}
            (path/'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,'schema'):preflight(path)

    def test_valid_contract_with_missing_observation_requires_review(self):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)
            shutil.copytree(ROOT/'data/public',path,dirs_exist_ok=True)
            data=path/self.manifest['data_file']
            lines=data.read_bytes().splitlines(keepends=True)
            raw=b''.join([lines[0]]+lines[2:])
            data.write_bytes(raw)
            manifest={**self.manifest,'sha256':hashlib.sha256(raw).hexdigest(),'byte_length':len(raw)}
            (path/'manifest.json').write_text(json.dumps(manifest))
            result=preflight(path)
            self.assertTrue(result['contract_valid'])
            self.assertTrue(result['review_required'])
            self.assertEqual(result['unavailable_slots'],1)
            self.assertEqual(result['rows'],122)
            self.assertEqual(result['expected_slots'],123)


if __name__ == '__main__':unittest.main()
