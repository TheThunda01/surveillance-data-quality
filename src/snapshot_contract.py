"""The narrow, versioned input contract for this project's CDC adapter."""
from datetime import datetime, timedelta
import re
from urllib.parse import urlsplit

from audit import parse_date
from diagnostics import DiagnosticError

CONTRACT_VERSION = '1.0'
PATHOGENS = {'Adenovirus', 'HMPV', 'PIV'}


def validate_manifest(manifest):
    if not isinstance(manifest, dict):
        raise DiagnosticError('MANIFEST_TYPE','manifest must be a JSON object')
    for key in ('sha256', 'metadata_sha256'):
        value = manifest.get(key)
        if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value):
            raise DiagnosticError('DIGEST_FORMAT',f'{key} must be a lowercase SHA-256 hexadecimal digest',field=key)
    for key in ('data_file', 'metadata_file'):
        value = manifest.get(key)
        if not isinstance(value, str) or not value or value in {'.', '..', 'manifest.json'} or '/' in value or '\\' in value:
            raise DiagnosticError('FILENAME_INVALID',f'{key} must be a plain filename',field=key)
    if manifest['data_file'] == manifest['metadata_file']:
        raise DiagnosticError('FILENAME_COLLISION','data and metadata filenames must differ',field='metadata_file')
    if type(manifest.get('byte_length')) is not int or not 0 < manifest['byte_length'] <= 10_000_000:
        raise DiagnosticError('BYTE_LENGTH_INVALID','byte_length must be an integer between 1 and 10000000',field='byte_length')
    if manifest.get('dataset_id') != 'rgnm-fkqb':
        raise DiagnosticError('DATASET_UNSUPPORTED','unsupported dataset_id; expected rgnm-fkqb',field='dataset_id')
    for key, expected in [
            ('source_page', '/Laboratory-Surveillance/Percent-positivity-of-respiratory-viruses-by-nucle/rgnm-fkqb'),
            ('download_url', '/resource/rgnm-fkqb.csv'),
            ('metadata_url', '/api/views/rgnm-fkqb.json')]:
        value = manifest.get(key)
        if not isinstance(value, str):
            raise DiagnosticError('SOURCE_URL_INVALID',f'{key} must name the supported CDC endpoint',field=key)
        try:
            url = urlsplit(value)
        except ValueError:
            raise DiagnosticError('SOURCE_URL_INVALID',f'{key} must name the supported CDC endpoint',field=key) from None
        if url.scheme != 'https' or url.netloc != 'data.cdc.gov' or url.path != expected or url.fragment:
            raise DiagnosticError('SOURCE_URL_INVALID',f'{key} must name the supported CDC endpoint',field=key)
    value = manifest.get('retrieved_at_utc')
    try:
        captured = datetime.fromisoformat(value) if isinstance(value, str) else None
        if captured is None or captured.tzinfo is None or captured.utcoffset() != timedelta(0):
            raise ValueError()
    except ValueError:
        raise DiagnosticError('CAPTURE_TIMESTAMP_INVALID','retrieved_at_utc must be an ISO timestamp with UTC offset',field='retrieved_at_utc') from None
    selection = manifest.get('selection')
    if not isinstance(selection, dict) or selection.get('level') != 'National' or selection.get('subtype') != 'Combined Type':
        raise DiagnosticError('SELECTION_SCOPE_INVALID','selection must specify National and Combined Type',field='selection')
    pathogens = selection.get('pathogens')
    if not isinstance(pathogens, list) or not pathogens or any(not isinstance(p, str) or p not in PATHOGENS for p in pathogens) or len(set(pathogens)) != len(pathogens):
        raise DiagnosticError('SELECTION_SERIES_INVALID','selection pathogens must be unique supported categories',field='selection.pathogens')
    try:
        first, last = [parse_date(selection[k]) for k in ('first_week_end', 'last_week_end')]
    except (KeyError, TypeError, ValueError):
        raise DiagnosticError('SELECTION_DATE_INVALID','selection dates must be valid ISO dates',field='selection') from None
    if first.weekday() != 5 or last.weekday() != 5 or first > last or last > captured.date():
        raise DiagnosticError('SELECTION_WINDOW_INVALID','selection dates must be ordered Saturdays no later than capture',field='selection')
    return captured
