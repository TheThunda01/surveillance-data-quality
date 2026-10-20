"""Audit a pinned public aggregate CDC NREVSS extract, without reconstructing history."""
from __future__ import annotations
import argparse
from collections import Counter
import csv
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from html import escape
import hashlib
import json
from pathlib import Path

from audit import nonnegative_integer, parse_date, read_csv
from snapshot_contract import validate_manifest
from diagnostics import DiagnosticError, finding, read_json_document

ROOT=Path(__file__).resolve().parents[1]
FIELDS={'mmwrweek_end','level','state','tests','detections','percent_pos','subtype','pathogen','posted','tests_3wma','detections_5wma','percent_pos_3wma'}
MISSING={'':'not_reported','.':'unavailable','*':'suppressed'}


def api_date(value: str) -> date:
    if len(value)!=23 or not value.endswith('T00:00:00.000'):
        raise ValueError('expected Socrata midnight date format')
    return parse_date(value[:10])


def load_snapshot(directory:Path) -> tuple[list[dict],dict]:
    manifest=read_json_document(directory/'manifest.json','manifest')
    captured=validate_manifest(manifest).date()
    name=manifest['data_file']
    if Path(name).name!=name:
        raise DiagnosticError('FILENAME_INVALID','manifest data_file must be a filename',field='data_file')
    path=directory/name
    if path.is_symlink() or (directory/manifest['metadata_file']).is_symlink():
        raise DiagnosticError('SNAPSHOT_SYMLINK','snapshot data and metadata must not be symlinks')
    if path.stat().st_size!=manifest['byte_length']:
        raise DiagnosticError('DATA_LENGTH_MISMATCH','snapshot byte_length does not match manifest',field='byte_length')
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    if actual!=manifest['sha256']:
        raise DiagnosticError('DATA_DIGEST_MISMATCH','snapshot SHA-256 does not match manifest',field='sha256')
    if manifest.get('metadata_file') and manifest.get('metadata_sha256'):
        metadata_name=manifest['metadata_file']
        if Path(metadata_name).name!=metadata_name:
            raise DiagnosticError('FILENAME_INVALID','metadata_file must be a filename',field='metadata_file')
        if hashlib.sha256((directory/metadata_name).read_bytes()).hexdigest()!=manifest['metadata_sha256']:
            raise DiagnosticError('METADATA_DIGEST_MISMATCH','metadata SHA-256 does not match manifest',field='metadata_sha256')
        metadata=read_json_document(directory/metadata_name,'metadata')
        if not isinstance(metadata,dict) or metadata.get('id')!=manifest['dataset_id']:
            raise DiagnosticError('METADATA_IDENTITY_MISMATCH','metadata dataset identity does not match manifest',field='id')
        columns=metadata.get('columns')
        if not isinstance(columns,list) or any(not isinstance(c,dict) for c in columns):
            raise DiagnosticError('METADATA_COLUMNS_INVALID','metadata columns must be a list of objects',field='columns')
        names=[c.get('fieldName') for c in columns]
        if any(not isinstance(n,str) for n in names) or set(names)!=FIELDS or len(names)!=len(FIELDS):
            raise DiagnosticError('METADATA_COLUMNS_INVALID','metadata column schema does not match the supported adapter',field='columns')
    rows=read_snapshot_csv(path)
    for line,row in enumerate(rows,2):
        try:
            posted=api_date(row['posted'])
        except ValueError:
            # Malformed release dates remain row-level findings in the audit.
            continue
        if posted>captured:
            raise DiagnosticError('RELEASE_AFTER_CAPTURE',f'line {line}: posted release date follows snapshot capture date',field='posted',line=line)
    return rows,manifest


def read_snapshot_csv(path):
    with path.open(newline='',encoding='utf-8') as stream:
        reader=csv.DictReader(stream,strict=True)
        try:
            if reader.fieldnames is None or set(reader.fieldnames)!=FIELDS or len(reader.fieldnames)!=len(FIELDS):
                raise DiagnosticError('CSV_SCHEMA_INVALID',f'{path.name}: columns must be exactly {sorted(FIELDS)}',line=1)
            rows=[]
            for row in reader:
                if None in row or any(value is None for value in row.values()):
                    raise DiagnosticError('CSV_ROW_WIDTH_INVALID',f'{path.name}: malformed CSV row width',line=reader.line_num)
                rows.append(row)
        except csv.Error as error:
            raise DiagnosticError('CSV_PARSE_INVALID',f'{path.name}: malformed CSV: {error}',line=reader.line_num) from error
    return rows


def audit_snapshot(rows:list[dict], selection:dict, diagnostic_findings=None) -> dict:
    first,last=map(parse_date,[selection['first_week_end'],selection['last_week_end']])
    if first.weekday()!=5 or last.weekday()!=5 or first>last:
        raise ValueError('selection endpoints must be ordered Saturdays')
    pathogens=selection['pathogens']
    if len(set(pathogens))!=len(pathogens) or not pathogens:
        raise ValueError('selection pathogens must be unique and nonempty')
    weeks=[first+timedelta(days=7*i) for i in range((last-first).days//7+1)]
    lookup={}
    for line,row in enumerate(rows,2):
        try:
            week=api_date(row['mmwrweek_end'])
        except ValueError as error:
            raise DiagnosticError('OBSERVATION_DATE_INVALID',f'line {line}: {error}',field='mmwrweek_end',line=line) from error
        if row['level']!=selection['level'] or row['subtype']!=selection['subtype'] or row['state']:
            raise DiagnosticError('OBSERVATION_OUTSIDE_SELECTION',f'line {line}: row is outside national combined-type selection',line=line)
        if row['pathogen'] not in pathogens or week not in weeks:
            raise DiagnosticError('OBSERVATION_OUTSIDE_SELECTION',f'line {line}: row outside declared snapshot window',line=line)
        lookup.setdefault((row['pathogen'],week),[]).append((line,row))
    slots=[]
    def record(slot,code):
        if diagnostic_findings is not None:
            diagnostic_findings.append(finding(code,slot['finding'] or 'No row exists for expected series-week',
                                               line=slot['source_line'],pathogen=slot['pathogen'],week_end=slot['week_end']))
    for pathogen in pathogens:
        for week in weeks:
            submitted=lookup.get((pathogen,week),[])
            slot={'pathogen':pathogen,'week_end':week.isoformat(),'status':'absent_from_extract',
                  'source_line':None,'tests':None,'detections':None,'reported_percent_positive':None,
                  'calculated_percent_positive':None,'percent_difference_pp':None,'posted_date':None,'finding':''}
            code='OBSERVATION_MISSING'
            if len(submitted)>1:
                slot.update(status='invalid',finding='duplicate pathogen-week; all copies quarantined')
                code='OBSERVATION_DUPLICATE'
            elif submitted:
                line,row=submitted[0]; slot['source_line']=line
                try:
                    slot['posted_date']=api_date(row['posted']).isoformat()
                    if parse_date(slot['posted_date'])<week:
                        raise ValueError('release date precedes observation week')
                except ValueError as error:
                    slot.update(status='invalid',finding=str(error));slots.append(slot);record(slot,'OBSERVATION_RELEASE_INVALID');continue
                tokens={row[k] for k in ['tests','detections','percent_pos']}
                unavailable=tokens.intersection(MISSING)
                if unavailable:
                    reason='suppressed' if '*' in unavailable else 'unavailable'
                    slot.update(status=reason,finding='source marks at least one required value '+reason)
                    code='OBSERVATION_SUPPRESSED' if reason=='suppressed' else 'OBSERVATION_UNAVAILABLE'
                else:
                    try:
                        tests=nonnegative_integer(row['tests']); positive=nonnegative_integer(row['detections'])
                        reported=Decimal(row['percent_pos'])
                        if not reported.is_finite() or reported<0 or reported>100:
                            raise ValueError('percentage outside 0 to 100')
                        if positive>tests:
                            raise ValueError('detections exceed tests')
                        calculated=Decimal(100)*positive/tests if tests else None
                        delta=abs(reported-calculated) if calculated is not None else None
                        slot.update(tests=tests,detections=positive,reported_percent_positive=float(reported),
                                    calculated_percent_positive=float(calculated) if calculated is not None else None,
                                    percent_difference_pp=float(delta) if delta is not None else None,status='usable')
                        code=None
                        if delta is not None and delta>Decimal('0.005000000001'):
                            slot.update(status='invalid',finding='provided percentage differs from count ratio beyond two-decimal rounding')
                            code='OBSERVATION_PERCENT_MISMATCH'
                        if tests==0:
                            slot['finding']='zero-test denominator; calculated positivity undefined'
                            code='OBSERVATION_ZERO_TESTS'
                    except (ValueError,InvalidOperation,OverflowError) as error:
                        slot.update(status='invalid',finding=str(error))
                        code='OBSERVATION_VALUES_INVALID'
            slots.append(slot)
            if code is not None:record(slot,code)
    summary=[]
    for pathogen in pathogens:
        selected=[r for r in slots if r['pathogen']==pathogen]
        usable=[r for r in selected if r['status']=='usable']
        tests=sum(r['tests'] for r in usable); positives=sum(r['detections'] for r in usable)
        statuses=Counter(r['status'] for r in selected)
        summary.append({'pathogen':pathogen,'expected_weeks':len(weeks),'rows_present':len(selected)-statuses['absent_from_extract'],
                        'usable_weeks':len(usable),'usable_week_coverage':len(usable)/len(weeks),
                        'absent_weeks':statuses['absent_from_extract'],'suppressed_weeks':statuses['suppressed'],
                        'unavailable_weeks':statuses['unavailable'],'invalid_weeks':statuses['invalid'],
                        'zero_test_weeks':sum(r['tests']==0 for r in usable),
                        'detections':positives,'tests':tests,'pooled_percent_positive':100*positives/tests if tests else None,
                        'max_rounding_difference_pp':max((r['percent_difference_pp'] for r in usable if r['percent_difference_pp'] is not None),default=None)})
    return {'summary':summary,'slots':slots,'input_rows':len(rows),'expected_rows':len(weeks)*len(pathogens)}


def trailing_sensitivity(result:dict, as_of:date, lags=(0,7,14,28)) -> list[dict]:
    """Retrospective window sensitivity; NOT a reconstruction of earlier vintages."""
    if any(lag<0 for lag in lags):
        raise ValueError('lag windows must be nonnegative')
    output=[]
    for base in result['summary']:
        full_tests=base['tests']
        for lag in lags:
            cutoff=as_of-timedelta(days=lag)
            selected=[r for r in result['slots'] if r['pathogen']==base['pathogen'] and parse_date(r['week_end'])<=cutoff]
            usable=[r for r in selected if r['status']=='usable']
            tests=sum(r['tests'] for r in usable); positives=sum(r['detections'] for r in usable)
            output.append({'pathogen':base['pathogen'],'exclude_weeks_newer_than_days':lag,'latest_eligible_week_end':cutoff.isoformat(),
                           'eligible_expected_weeks':len(selected),'usable_weeks':len(usable),
                           'detections':positives,'tests':tests,'retained_test_denominator_fraction':tests/full_tests if full_tests else None,
                           'pooled_percent_positive':100*positives/tests if tests else None,
                           'change_from_all_weeks_pp':100*positives/tests-base['pooled_percent_positive'] if tests and base['pooled_percent_positive'] is not None else None})
    return output



def denominator_changes(slots:list[dict], threshold:float=0.5) -> dict:
    """Flag large relative count changes between consecutive usable weeks.

    This is a diagnostic for review, not an exclusion rule, significance test,
    or estimate of incidence. No comparison bridges an absent/unusable week.
    """
    cutoff=Decimal(str(threshold))
    if not cutoff.is_finite() or cutoff<0:
        raise ValueError('denominator-change threshold must be finite and nonnegative')
    lookup={(r['pathogen'],parse_date(r['week_end'])):r for r in slots}
    if len(lookup)!=len(slots):
        raise ValueError('denominator diagnostic requires unique series-week slots')
    rows=[]
    for current in sorted(slots,key=lambda r:(r['pathogen'],r['week_end'])):
        week=parse_date(current['week_end'])
        previous_week=week-timedelta(days=7)
        previous=lookup.get((current['pathogen'],previous_week))
        item={'pathogen':current['pathogen'],'week_end':current['week_end'],
              'previous_week_end':previous_week.isoformat(),
              'previous_tests':previous['tests'] if previous and previous['status']=='usable' else None,
              'current_tests':current['tests'] if current['status']=='usable' else None,
              'test_count_ratio':None,'relative_test_count_change':None,
              'change_exceeds_threshold':None,'diagnostic_status':None}
        if current['status']!='usable':
            item['diagnostic_status']='current_week_unusable'
        elif previous is None:
            item['diagnostic_status']='no_previous_calendar_week'
        elif previous['status']!='usable':
            item['diagnostic_status']='previous_week_unusable'
        elif previous['tests']==0:
            item['diagnostic_status']='previous_week_zero_tests'
        else:
            change=Decimal(current['tests']-previous['tests'])/Decimal(previous['tests'])
            item.update(test_count_ratio=float(Decimal(current['tests'])/Decimal(previous['tests'])),
                        relative_test_count_change=float(change),
                        change_exceeds_threshold=abs(change)>cutoff,diagnostic_status='evaluated')
        rows.append(item)
    summaries=[]
    for pathogen in dict.fromkeys(r['pathogen'] for r in rows):
        selected=[r for r in rows if r['pathogen']==pathogen]
        evaluated=[r for r in selected if r['diagnostic_status']=='evaluated']
        summaries.append({'pathogen':pathogen,'evaluable_consecutive_pairs':len(evaluated),
                          'flagged_pairs':sum(r['change_exceeds_threshold'] for r in evaluated),
                          'largest_absolute_change_fraction':max((abs(r['relative_test_count_change']) for r in evaluated),default=None)})
    return {'threshold_fraction':float(cutoff),'flag_rule':'absolute relative change strictly greater than threshold',
            'purpose':'review diagnostic only; does not alter validity or exclude data','summary':summaries,'rows':rows}


def write_csv(path:Path,rows:list[dict]):
    if not rows:
        raise ValueError('cannot write an empty table without a schema')
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def chart(slots:list[dict],path:Path):
    pathogens=list(dict.fromkeys(r['pathogen'] for r in slots))
    weeks=sorted({r['week_end'] for r in slots})
    ymax=max((r['calculated_percent_positive'] or 0 for r in slots if r['status']=='usable'),default=1)*1.15 or 1
    colors=['#0072B2','#D55E00','#009E73']
    chunks=['<svg xmlns="http://www.w3.org/2000/svg" width="920" height="550" viewBox="0 0 920 550" role="img" aria-labelledby="title desc">',
            '<title id="title">National NREVSS weekly test positivity in the pinned 2026 extract</title>',
            '<desc id="desc">Three unsmoothed series, each with its own test denominator. These are test results from voluntary laboratory reporting, not population prevalence.</desc>',
            '<rect width="920" height="550" fill="white"/>','<g font-family="sans-serif" fill="#17212b">',
            '<text x="75" y="30" font-size="20">National weekly test positivity · pinned CDC extract</text>',
            '<text x="75" y="54" font-size="13">Unsmoothed count ratios; each series has a separate denominator.</text>']
    for j in range(6):
        y=410-j*64;value=ymax*j/5
        chunks += [f'<line x1="75" y1="{y}" x2="865" y2="{y}" stroke="#dbe0e5"/>',f'<text x="65" y="{y+4}" text-anchor="end" font-size="12">{value:.1f}%</text>']
    for i in [0,10,20,30,40]:
        if i<len(weeks):
            x=75+790*i/max(1,len(weeks)-1)
            chunks.append(f'<text x="{x:.1f}" y="433" text-anchor="middle" font-size="12">{weeks[i]}</text>')
    for index,pathogen in enumerate(pathogens):
        parts=[]
        for i,week in enumerate(weeks):
            r=next(r for r in slots if r['pathogen']==pathogen and r['week_end']==week)
            if r['status']!='usable' or r['calculated_percent_positive'] is None:
                if parts: chunks.append(f'<polyline points="{" ".join(parts)}" fill="none" stroke="{colors[index%3]}" stroke-width="2.3"/>');parts=[]
                continue
            x=75+790*i/max(1,len(weeks)-1);y=410-320*r['calculated_percent_positive']/ymax
            parts.append(f'{x:.1f},{y:.1f}')
        if parts:chunks.append(f'<polyline points="{" ".join(parts)}" fill="none" stroke="{colors[index%3]}" stroke-width="2.3"/>')
        x=80+index*230
        chunks += [f'<line x1="{x}" y1="469" x2="{x+28}" y2="469" stroke="{colors[index%3]}" stroke-width="3"/>',f'<text x="{x+36}" y="474" font-size="14">{escape(pathogen)}</text>']
    chunks += ['<text x="75" y="510" font-size="12">Source: CDC NREVSS; Jan 3–Oct 10, 2026. Retrieved Oct 20, 2026.</text>',
               '<text x="75" y="529" font-size="12">Coverage here means rows in this extract, not all laboratories, patients, or infections. No CDC endorsement.</text>','</g></svg>']
    path.write_text('\n'.join(chunks)+'\n')


def display_number(value, digits=3, signed=False):
    if value is None:
        return 'undefined'
    return format(value, f'{"+" if signed else ""}.{digits}f')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',type=Path,default=ROOT/'data/public')
    parser.add_argument('--output',type=Path,default=ROOT/'results_public')
    parser.add_argument('--as-of',type=parse_date,default=None)
    parser.add_argument('--denominator-change-threshold',type=float,default=0.5,help='flag absolute consecutive-week test-count changes above this fraction; diagnostic only')
    args=parser.parse_args()
    try:
        if args.snapshot.resolve().is_relative_to(args.output.resolve()):
            raise ValueError('output must not contain the snapshot input directory')
        rows,manifest=load_snapshot(args.snapshot)
        captured=datetime.fromisoformat(manifest['retrieved_at_utc']).date()
        as_of=args.as_of or captured
        if as_of<captured:
            raise ValueError('single snapshot cannot reconstruct availability before its retrieval date')
        result=audit_snapshot(rows,manifest['selection'])
        result['provenance']={'source_page':manifest['source_page'],'sha256':manifest['sha256'],'retrieved_at_utc':manifest['retrieved_at_utc'],
                              'analysis_as_of':as_of.isoformat(),'historical_vintages_available':False}
        sensitivity=trailing_sensitivity(result,as_of)
        result['trailing_window_sensitivity']=sensitivity
        diagnostics=denominator_changes(result['slots'],args.denominator_change_threshold)
        result['denominator_change_diagnostics']=diagnostics
        args.output.mkdir(parents=True,exist_ok=True)
        (args.output/'audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        write_csv(args.output/'weekly_audit.csv',result['slots']);write_csv(args.output/'summary.csv',result['summary']);write_csv(args.output/'trailing_window_sensitivity.csv',sensitivity)
        chart(result['slots'],args.output/'weekly_positivity.svg')
        write_csv(args.output/'denominator_changes.csv',diagnostics['rows'])
        write_csv(args.output/'denominator_diagnostic_summary.csv',diagnostics['summary'])
        report=['# Real public-data audit: CDC NREVSS','',
        f"Pinned extract: **{manifest['selection']['first_week_end']}–{manifest['selection']['last_week_end']}**, retrieved **{captured}**. Source: CDC. This project is not endorsed by CDC or the U.S. government. The source data are freely available from the linked CDC dataset.",'',
        'This audit describes data in one extracted release. It does not measure the fraction of all laboratories reporting or the completeness of infections in the population.','',
        '| Series | Usable / expected weeks | Positive tests / tests | Pooled positivity |', '| --- | --- | --- | --- |']
        report += [f"| {r['pathogen']} | {r['usable_weeks']} / {r['expected_weeks']} | {r['detections']:,} / {r['tests']:,} | {display_number(r['pooled_percent_positive'])}% |" for r in result['summary']]
        report += ['', '![Weekly unsmoothed test positivity](weekly_positivity.svg)','',
        'All three numerator/denominator pairs remain separate. Do not add them as unique people or compare pooled ratios as if they came from identical tested populations.','',
        '## What changes when recent weeks are held out?','',
        'The trailing-window analysis excludes weeks newer than 0, 7, 14, or 28 days before the analysis date. It reuses the same retrieved release. It is a sensitivity analysis of the observation window, **not** a recovery of values that were reported on an earlier date.','',
        '| Series | Days held out | Usable weeks | Retained test denominator | Positivity change (percentage points) |', '| --- | ---: | ---: | ---: | ---: |']
        report += [f"| {r['pathogen']} | {r['exclude_weeks_newer_than_days']} | {r['usable_weeks']} | {display_number(100*r['retained_test_denominator_fraction'] if r['retained_test_denominator_fraction'] is not None else None, 2)}% | {display_number(r['change_from_all_weeks_pp'], 4, True)} |" for r in sensitivity]
        report += ['', '## Did the weekly test denominator change sharply?', '',
        f"The review flag uses an absolute week-to-week test-count change **greater than {100*diagnostics['threshold_fraction']:.1f}%**. It compares consecutive usable calendar weeks only; a missing week or zero previous denominator leaves the ratio undefined. This setting is a demonstration choice, not a validated universal cutoff. Flagged records remain in every analysis.", '',
        '| Series | Evaluable consecutive pairs | Flagged for review | Largest absolute change |', '| --- | ---: | ---: | ---: |']
        report += [f"| {r['pathogen']} | {r['evaluable_consecutive_pairs']} | {r['flagged_pairs']} | {display_number(100*r['largest_absolute_change_fraction'] if r['largest_absolute_change_fraction'] is not None else None,2)}% |" for r in diagnostics['summary']]
        report += ['', '[Inspect the week-level counts and ratios](denominator_changes.csv). A change can reflect testing, participation, calendar effects, or other factors; this file does not identify its cause and is not an incidence or outbreak indicator.', '']
        report += ['', 'No adjustment for underreporting, causal effect, or outbreak forecast is fitted. The `posted` field is treated as release metadata, never as an individual laboratory submission date. See the methods for why complete-looking rows can still be provisional.','',f"[Original dataset]({manifest['source_page']}) · [Snapshot provenance](../data/public/manifest.json) · [Methods](../docs/public-data-methods.md)",'']
        (args.output/'report.md').write_text('\n'.join(report))
        print(json.dumps({'input_rows':result['input_rows'],'expected_rows':result['expected_rows'],'summary':result['summary']},indent=2))
    except (ValueError,KeyError,OSError,csv.Error) as error:
        parser.exit(2,f'public audit failed: {error}\n')

if __name__=='__main__':main()
