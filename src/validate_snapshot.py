"""Read-only snapshot preflight. Passing does not establish epidemiological validity."""
import argparse
import csv
import json
from pathlib import Path

from public_audit import ROOT, audit_snapshot, load_snapshot
from snapshot_contract import CONTRACT_VERSION
from diagnostics import envelope, exception_finding


def preflight(directory, diagnostic_findings=None):
    rows, manifest = load_snapshot(directory)
    result = audit_snapshot(rows, manifest['selection'],diagnostic_findings)
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
    parser.add_argument('--diagnostics-json', action='store_true',help='emit versioned findings on stdout for success or failure')
    args = parser.parse_args()
    try:
        findings=[]
        summary=preflight(args.snapshot,findings if args.diagnostics_json else None)
        print(json.dumps(envelope(summary,findings) if args.diagnostics_json else summary, indent=2, allow_nan=False))
    except (ValueError, KeyError, OSError, csv.Error) as error:
        if args.diagnostics_json:
            print(json.dumps(envelope(None,[exception_finding(error)]),indent=2,allow_nan=False))
            parser.exit(2)
        parser.exit(2, f'snapshot preflight failed: {error}\n')


if __name__ == '__main__':
    main()
