"""Fetch a new version of the fixed public CDC extract into a NEW directory.

No API keys are used. The checked-in snapshot is never overwritten. This optional
network step is not required to reproduce the bundled analysis.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
from io import StringIO
import json
from pathlib import Path
import urllib.parse
import urllib.request

from public_audit import FIELDS, audit_snapshot

SELECTION={'level':'National','subtype':'Combined Type','pathogens':['Adenovirus','HMPV','PIV'],
           'first_week_end':'2026-01-03','last_week_end':'2026-10-10'}
BASE='https://data.cdc.gov/resource/rgnm-fkqb.csv'
PARAMS={'$where':"level = 'National' AND subtype = 'Combined Type' AND pathogen in ('Adenovirus','HMPV','PIV') AND mmwrweek_end >= '2026-01-03T00:00:00.000' AND mmwrweek_end <= '2026-10-10T00:00:00.000'",'$order':'mmwrweek_end ASC, pathogen ASC','$limit':'5000'}
URL=BASE+'?'+urllib.parse.urlencode(PARAMS)
METADATA_URL='https://data.cdc.gov/api/views/rgnm-fkqb.json'
SOURCE='https://data.cdc.gov/Laboratory-Surveillance/Percent-positivity-of-respiratory-viruses-by-nucle/rgnm-fkqb'


def fetch_bytes(url):
    request=urllib.request.Request(url,headers={'User-Agent':'surveillance-data-quality-educational/2.0'})
    with urllib.request.urlopen(request,timeout=60) as response:
        content=response.read(10_000_001)
    if len(content)>10_000_000:
        raise ValueError('unexpectedly large response')
    return content


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True,help='new directory, which must not already exist')
    args=parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError('output exists; use a new directory to preserve earlier vintages')
        raw=fetch_bytes(URL)
        reader=csv.DictReader(StringIO(raw.decode('utf-8')))
        if reader.fieldnames is None or set(reader.fieldnames)!=FIELDS or len(reader.fieldnames)!=len(FIELDS):
            raise ValueError('CDC response schema changed; inspect before adapting the loader')
        rows=list(reader)
        if not rows or len(rows)>=5000:
            raise ValueError('empty or potentially truncated API response')
        if any(None in row or any(v is None for v in row.values()) for row in rows):
            raise ValueError('malformed CSV row width')
        audit_snapshot(rows,SELECTION)
        metadata=json.loads(fetch_bytes(METADATA_URL))
        kept={k:metadata.get(k) for k in ['id','name','attribution','attributionLink','licenseId','rowsUpdatedAt']}
        kept['columns']=[{k:c.get(k) for k in ['fieldName','name','dataTypeName']} for c in metadata.get('columns',[]) if not c.get('fieldName','').startswith(':')]
        core=metadata.get('metadata',{}).get('custom_fields',{}).get('Common Core',{})
        kept['public_access']=core.get('Public Access Level')
        kept['update_frequency']=core.get('Update Frequency')
        metadata_bytes=(json.dumps(kept,indent=2)+'\n').encode()
        manifest={'source':'CDC National Respiratory and Enteric Virus Surveillance System (NREVSS)','dataset_id':'rgnm-fkqb',
                  'source_page':SOURCE,'download_url':URL,'metadata_url':METADATA_URL,'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),
                  'data_file':'nrevss_national_2026.csv','sha256':hashlib.sha256(raw).hexdigest(),'byte_length':len(raw),
                  'license_id':metadata.get('licenseId'),'metadata_file':'source_metadata.json','metadata_sha256':hashlib.sha256(metadata_bytes).hexdigest(),
                  'selection':SELECTION,'reuse_policy_url':'https://www.cdc.gov/other/agencymaterials.html',
                  'license_note':'Dataset metadata has no licenseId unless supplied above. See CDC agency-materials policy and retain attribution; no CDC endorsement.',
                  'disclaimer':'One retrieved release. posted is release metadata, not an individual reporting delay.'}
        args.output.mkdir(parents=True,exist_ok=False)
        (args.output/manifest['data_file']).write_bytes(raw)
        (args.output/'source_metadata.json').write_bytes(metadata_bytes)
        (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print(json.dumps({'directory':str(args.output),'rows':len(rows),'sha256':manifest['sha256']},indent=2))
    except (ValueError,OSError,KeyError,csv.Error) as error:
        parser.exit(2,f'fetch failed: {error}\n')

if __name__=='__main__':main()
