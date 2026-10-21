"""Protect spreadsheet CSV text without changing analytical values or JSON."""


def spreadsheet_safe_value(value: object) -> object:
    """Prefix formula-like strings; preserve numeric values and missingness."""
    if isinstance(value, str) and value.lstrip(" \t\r\n\v\f\ufeff").startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def spreadsheet_safe_rows(rows):
    """Yield fresh export rows so original records remain available unchanged."""
    for row in rows:
        yield {key: spreadsheet_safe_value(value) for key, value in row.items()}
