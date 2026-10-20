"""Read-only snapshot preflight. Passing does not establish epidemiological validity."""
import argparse
import csv
import json
from pathlib import Path

from public_audit import ROOT, audit_snapshot, load_snapshot
from snapshot_contract import CONTRACT_VERSION


def preflight(directory):
    rows, manifest = load_snapshot(directory)
    result = audit_snapshot(rows, manifest['selection'])
    invalid = sum(r['invalid_weeks'] for r in result['summary'])
    unavailable = sum(r['absent_weeks'] + r['suppressed_weeks'] + r['unavailable_weeks'] for r in result['summary'])
    return {'contract_version': CONTRACT_VERSION, 'contract_valid': True,
            'review_required': bool(invalid or unavailable), 'dataset_id': manifest['dataset_id'],
            'data_sha256': manifest['sha256'], 'metadata_sha256': manifest['metadata_sha256'],
            'retrieved_at_utc': manifest['retrieved_at_utc'], 'rows': len(rows),
            'expected_slots': result['expected_rows'], 'invalid_slots': invalid,
            'unavailable_slots': unavailable,
            'interpretation': 'Checks file integrity, supported schema and row consistency only; does not establish complete laboratory reporting or authentic source provenance.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, default=ROOT/'data/public')
    args = parser.parse_args()
    try:
        print(json.dumps(preflight(args.snapshot), indent=2, allow_nan=False))
    except (ValueError, KeyError, OSError, csv.Error) as error:
        parser.exit(2, f'snapshot preflight failed: {error}\n')


if __name__ == '__main__':
    main()
