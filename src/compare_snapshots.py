"""Compare two verified public releases, preserving the identities of both."""
import argparse
from datetime import datetime
import json
from pathlib import Path
from public_audit import audit_snapshot, load_snapshot, write_csv


def compare(old_rows,old_manifest,new_rows,new_manifest):
    if old_manifest['dataset_id']!=new_manifest['dataset_id'] or old_manifest['selection']!=new_manifest['selection']:
        raise ValueError('both releases must describe the same dataset and selection')
    if datetime.fromisoformat(new_manifest['retrieved_at_utc'])<datetime.fromisoformat(old_manifest['retrieved_at_utc']):
        raise ValueError('new release was retrieved earlier than old release')
    old=audit_snapshot(old_rows,old_manifest['selection']);new=audit_snapshot(new_rows,new_manifest['selection'])
    key=lambda r:(r['pathogen'],r['week_end'])
    old_lookup={key(r):r for r in old['slots']}
    comparisons=[]
    for row in new['slots']:
        before=old_lookup[key(row)]
        fields=['status','tests','detections','reported_percent_positive']
        changed=[f for f in fields if before[f]!=row[f]]
        numeric=before['status']=='usable' and row['status']=='usable'
        comparisons.append({'pathogen':row['pathogen'],'week_end':row['week_end'],'changed_fields':';'.join(changed),
                            'old_status':before['status'],'new_status':row['status'],
                            'old_tests':before['tests'],'new_tests':row['tests'],
                            'test_delta':row['tests']-before['tests'] if numeric else None,
                            'detection_delta':row['detections']-before['detections'] if numeric else None})
    return {'old_sha256':old_manifest['sha256'],'new_sha256':new_manifest['sha256'],
            'old_retrieved_at_utc':old_manifest['retrieved_at_utc'],'new_retrieved_at_utc':new_manifest['retrieved_at_utc'],
            'changed_slots':sum(bool(r['changed_fields']) for r in comparisons),'slots':comparisons}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old',type=Path,required=True);parser.add_argument('--new',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        if any(p.resolve().is_relative_to(args.output.resolve()) for p in [args.old,args.new]):
            raise ValueError('output must not contain either source directory')
        result=compare(*load_snapshot(args.old),*load_snapshot(args.new))
        args.output.mkdir(parents=True,exist_ok=True)
        (args.output/'comparison.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n', encoding='utf-8', newline='\n')
        write_csv(args.output/'comparison.csv',result['slots'])
        print(json.dumps({k:v for k,v in result.items() if k!='slots'},indent=2))
    except (ValueError,OSError,KeyError) as error:
        parser.exit(2,f'comparison failed: {error}\n')

if __name__=='__main__':main()
