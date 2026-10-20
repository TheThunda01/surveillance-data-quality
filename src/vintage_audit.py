"""Reconstruct aggregate report versions that were available by an explicit date.

Bundled vintages are synthetic. Each revision is a full replacement of a site-week
report; versions are never added together. No value is imputed for an absent row.
"""
from __future__ import annotations
import argparse
import csv
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path

from audit import nonnegative_integer, parse_date, read_csv

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {'site_id', 'week_end', 'issued_on', 'positive_tests', 'tests_performed'}
EXPECTED_FIELDS = {'site_id', 'week_end'}


def reconstruct(observations: list[dict], expected: list[dict], as_of: date, grace_days: int = 7) -> dict:
    """Use the newest version issued on/before as_of, including invalid revisions.

    Counts are validated after selecting a version. Falling back to a previously
    valid version would hide a newly received problem. Date/key ambiguity fails
    the run, because it prevents a defensible ordering of revisions.
    """
    if grace_days < 0:
        raise ValueError('grace_days must be nonnegative')
    calendar = {}
    for row in expected:
        key = (row['site_id'], row['week_end'])
        week = parse_date(row['week_end'])
        if not row['site_id'].strip() or row['site_id'] != row['site_id'].strip():
            raise ValueError('expected site identifier must be nonblank without surrounding spaces')
        if week.weekday() != 5:
            raise ValueError('week_end must be Saturday in this schema')
        if key in calendar:
            raise ValueError(f'duplicate expected key: {key}')
        calendar[key] = week
    if not calendar:
        raise ValueError('expected calendar must not be empty')
    histories = {key: [] for key in calendar}
    seen = set()
    future_versions = 0
    for line, row in enumerate(observations, 2):
        key = (row['site_id'], row['week_end'])
        if key not in calendar:
            raise ValueError(f'line {line}: unknown site-week')
        issued = parse_date(row['issued_on'])
        if issued < calendar[key]:
            raise ValueError(f'line {line}: issue date precedes week end')
        version_key = (*key, issued)
        if version_key in seen:
            raise ValueError(f'line {line}: ambiguous duplicate site-week issue date')
        seen.add(version_key)
        if issued > as_of:
            future_versions += 1
            continue
        histories[key].append((issued, line, row))
    rows = []
    for key in sorted(calendar, key=lambda k: (k[1], k[0])):
        week = calendar[key]
        available = sorted(histories[key], key=lambda v: v[0])
        due = week + timedelta(days=grace_days) <= as_of
        output = {'site_id':key[0], 'week_end':key[1], 'due_on':(week+timedelta(days=grace_days)).isoformat(),
                  'status':'not_due' if not due else 'not_yet_available', 'selected_issue_date':None,
                  'source_line':None, 'available_versions':len(available), 'positive_tests':None,
                  'tests_performed':None, 'positivity':None, 'first_delay_days':None,
                  'selected_delay_days':None, 'revision_positive_delta':None, 'revision_test_delta':None,
                  'errors':[]}
        if available:
            issued, line, selected = available[-1]
            output.update(selected_issue_date=issued.isoformat(), source_line=line,
                          first_delay_days=(available[0][0]-week).days, selected_delay_days=(issued-week).days)
            counts = {}
            for field in ['positive_tests','tests_performed']:
                try:
                    counts[field] = nonnegative_integer(selected[field])
                except ValueError:
                    output['errors'].append(f'invalid_{field}')
            if len(counts)==2 and counts['positive_tests'] > counts['tests_performed']:
                output['errors'].append('positive_tests_exceed_tests')
            if not output['errors']:
                output.update(counts)
                output['positivity'] = counts['positive_tests']/counts['tests_performed'] if counts['tests_performed'] else None
                if due:
                    output['status'] = 'available_usable'
                first = available[0][2]
                try:
                    first_positive = nonnegative_integer(first['positive_tests'])
                    first_tests = nonnegative_integer(first['tests_performed'])
                    if first_positive <= first_tests:
                        output['revision_positive_delta'] = counts['positive_tests']-first_positive
                        output['revision_test_delta'] = counts['tests_performed']-first_tests
                except ValueError:
                    pass
            elif due:
                output['status'] = 'available_invalid'
        rows.append(output)
    due_rows=[r for r in rows if r['status'] != 'not_due']
    usable=[r for r in due_rows if r['status']=='available_usable']
    positives=sum(r['positive_tests'] for r in usable)
    tests=sum(r['tests_performed'] for r in usable)
    summary={'as_of':as_of.isoformat(), 'grace_days':grace_days, 'expected_due_slots':len(due_rows),
             'not_due_slots':len(rows)-len(due_rows), 'available_due_slots':sum(r['selected_issue_date'] is not None for r in due_rows),
             'usable_due_slots':len(usable), 'unreported_due_slots':sum(r['status']=='not_yet_available' for r in due_rows),
             'invalid_due_slots':sum(r['status']=='available_invalid' for r in due_rows),
             'usable_due_coverage':len(usable)/len(due_rows) if due_rows else None,
             'future_versions_excluded':future_versions, 'selected_revised_due_slots':sum(r['available_versions']>1 for r in due_rows),
             'positive_tests':positives, 'tests_performed':tests, 'pooled_positivity':positives/tests if tests else None}
    return {'summary':summary,'slots':rows}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observations',type=Path,default=ROOT/'data/vintage_demo.csv')
    parser.add_argument('--expected',type=Path,default=ROOT/'data/vintage_expected.csv')
    parser.add_argument('--as-of',type=parse_date,default=date(2026,10,20))
    parser.add_argument('--grace-days',type=int,default=7)
    parser.add_argument('--output',type=Path,default=ROOT/'results_vintages')
    args=parser.parse_args()
    try:
        if any(p.resolve().is_relative_to(args.output.resolve()) for p in [args.observations,args.expected]):
            raise ValueError('output must not contain input files')
        observations=read_csv(args.observations,FIELDS)
        expected=read_csv(args.expected,EXPECTED_FIELDS)
        result=reconstruct(observations,expected,args.as_of,args.grace_days)
        result['provenance']={'data_status':'synthetic report-vintage demonstration','input_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [args.observations,args.expected]}}
        args.output.mkdir(parents=True,exist_ok=True)
        (args.output/'snapshot.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        rows=result['slots']
        with (args.output/'snapshot.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows({**r,'errors':';'.join(r['errors'])} for r in rows)
        sensitivity=[]
        for cutoff in [date(2026,10,5),date(2026,10,12),date(2026,10,20)]:
            sensitivity.append(reconstruct(observations,expected,cutoff,args.grace_days)['summary'])
        with (args.output/'as_of_sensitivity.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(sensitivity[0]))
            writer.writeheader();writer.writerows(sensitivity)
        s=result['summary']
        report=['# Synthetic report-vintage analysis','',f"As of {s['as_of']}, with a {s['grace_days']}-day grace period, {s['usable_due_slots']} of {s['expected_due_slots']} due slots have usable reports.",'',
        'This is an invented version-history exercise. It is separate from the real CDC snapshot. A report issued after the cutoff is excluded. A revision replaces an older report; it is not another batch of tests. Negative revision deltas are permitted corrections, not negative test counts.','',
        '| As of | Due slots | Usable | Unreported | Future versions excluded | Positives / tests |','| --- | ---: | ---: | ---: | ---: | --- |']
        report += [f"| {r['as_of']} | {r['expected_due_slots']} | {r['usable_due_slots']} | {r['unreported_due_slots']} | {r['future_versions_excluded']} | {r['positive_tests']} / {r['tests_performed']} |" for r in sensitivity]
        report += ['', 'These denominators differ because different weeks are due and different revisions were available. Comparing these aggregate percentages as disease trends would be misleading.','']
        (args.output/'report.md').write_text('\n'.join(report))
        print(json.dumps(s,indent=2))
    except (ValueError,OSError,csv.Error) as error:
        parser.exit(2,f'vintage audit failed: {error}\n')

if __name__=='__main__':
    main()
