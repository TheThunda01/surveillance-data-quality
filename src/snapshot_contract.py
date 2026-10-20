"""The narrow, versioned input contract for this project's CDC adapter."""
from datetime import datetime, timedelta
import re
from urllib.parse import urlsplit

from audit import parse_date

CONTRACT_VERSION = '1.0'
PATHOGENS = {'Adenovirus', 'HMPV', 'PIV'}


def validate_manifest(manifest):
    if not isinstance(manifest, dict):
        raise ValueError('manifest must be a JSON object')
    for key in ('sha256', 'metadata_sha256'):
        value = manifest.get(key)
        if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value):
            raise ValueError(f'{key} must be a lowercase SHA-256 hexadecimal digest')
    for key in ('data_file', 'metadata_file'):
        value = manifest.get(key)
        if not isinstance(value, str) or not value or value in {'.', '..', 'manifest.json'} or '/' in value or '\\' in value:
            raise ValueError(f'{key} must be a plain filename')
    if manifest['data_file'] == manifest['metadata_file']:
        raise ValueError('data and metadata filenames must differ')
    if type(manifest.get('byte_length')) is not int or not 0 < manifest['byte_length'] <= 10_000_000:
        raise ValueError('byte_length must be an integer between 1 and 10000000')
    if manifest.get('dataset_id') != 'rgnm-fkqb':
        raise ValueError('unsupported dataset_id; expected rgnm-fkqb')
    for key, expected in [
            ('source_page', '/Laboratory-Surveillance/Percent-positivity-of-respiratory-viruses-by-nucle/rgnm-fkqb'),
            ('download_url', '/resource/rgnm-fkqb.csv'),
            ('metadata_url', '/api/views/rgnm-fkqb.json')]:
        value = manifest.get(key)
        if not isinstance(value, str):
            raise ValueError(f'{key} must name the supported CDC endpoint')
        url = urlsplit(value)
        if url.scheme != 'https' or url.netloc != 'data.cdc.gov' or url.path != expected or url.fragment:
            raise ValueError(f'{key} must name the supported CDC endpoint')
    value = manifest.get('retrieved_at_utc')
    try:
        captured = datetime.fromisoformat(value) if isinstance(value, str) else None
        if captured is None or captured.tzinfo is None or captured.utcoffset() != timedelta(0):
            raise ValueError()
    except ValueError:
        raise ValueError('retrieved_at_utc must be an ISO timestamp with UTC offset') from None
    selection = manifest.get('selection')
    if not isinstance(selection, dict) or selection.get('level') != 'National' or selection.get('subtype') != 'Combined Type':
        raise ValueError('selection must specify National and Combined Type')
    pathogens = selection.get('pathogens')
    if not isinstance(pathogens, list) or not pathogens or any(not isinstance(p, str) or p not in PATHOGENS for p in pathogens) or len(set(pathogens)) != len(pathogens):
        raise ValueError('selection pathogens must be unique supported categories')
    try:
        first, last = [parse_date(selection[k]) for k in ('first_week_end', 'last_week_end')]
    except (KeyError, TypeError, ValueError):
        raise ValueError('selection dates must be valid ISO dates') from None
    if first.weekday() != 5 or last.weekday() != 5 or first > last or last > captured.date():
        raise ValueError('selection dates must be ordered Saturdays no later than capture')
    return captured
