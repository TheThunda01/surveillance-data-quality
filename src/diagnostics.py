"""Versioned diagnostic identities, kept separate from human-readable messages."""
import csv
import json
from pathlib import Path

CATALOG = json.loads((Path(__file__).resolve().parents[1]/'schemas/preflight-diagnostic-codes-v1.json').read_text())
CODES = {entry['code']: entry for entry in CATALOG['codes']}


def finding(code, message, *, scope=None, field=None, line=None, pathogen=None, week_end=None):
    entry = CODES[code]
    return {'code': code, 'severity': entry['severity'], 'message': str(message),
            'location': {'scope': scope or entry['scope'], 'field': field,
                         'line': line, 'pathogen': pathogen, 'week_end': week_end}}


class DiagnosticError(ValueError):
    def __init__(self, code, message, **location):
        super().__init__(message)
        self.finding = finding(code, message, **location)


def read_json_document(path, scope):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as error:
        raise DiagnosticError('JSON_INVALID', f'{path.name}: invalid JSON: {error.msg}',
                              scope=scope, line=error.lineno) from error
    except UnicodeError as error:
        raise DiagnosticError('TEXT_ENCODING_INVALID', f'{path.name}: expected UTF-8 text',scope=scope) from error


def exception_finding(error):
    if isinstance(error, DiagnosticError):
        return error.finding
    if isinstance(error, UnicodeError):
        return finding('TEXT_ENCODING_INVALID', 'Input is not valid UTF-8 text')
    if isinstance(error, OSError):
        return finding('FILE_IO_ERROR', str(error))
    if isinstance(error, csv.Error):
        return finding('CSV_PARSE_INVALID', str(error))
    return finding('VALIDATION_FAILED', str(error))


def envelope(summary, findings):
    status = 'rejected' if summary is None else ('review' if summary['review_required'] else 'passed')
    return {'diagnostics_version': CATALOG['diagnostics_version'], 'status': status,
            'exit_code': 2 if summary is None else 0, 'summary': summary, 'findings': findings}
