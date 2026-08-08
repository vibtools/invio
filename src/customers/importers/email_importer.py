from __future__ import annotations

import csv
import re
from pathlib import Path

from openpyxl import load_workbook

EMAIL_RE = re.compile(r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)


def _collect(values: list[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        for match in EMAIL_RE.findall(str(value or "")):
            email = match.strip().lower()
            if email not in seen:
                seen.add(email)
                result.append(email)
    return result


def import_emails(path: str | Path) -> tuple[list[str], list[str]]:
    """Extract unique email addresses from CSV/TSV/XLSX/XLSM/TXT files."""

    file_path = Path(path)
    suffix = file_path.suffix.lower()
    values: list[object] = []

    if suffix in {".xlsx", ".xlsm"}:
        workbook = load_workbook(file_path, read_only=True, data_only=True)
        try:
            sheet = workbook.active
            for row in sheet.iter_rows(values_only=True):
                values.extend(row)
        finally:
            workbook.close()
    elif suffix in {".csv", ".tsv"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.reader(handle, delimiter=delimiter):
                values.extend(row)
    else:
        values.append(file_path.read_text(encoding="utf-8-sig", errors="replace"))

    emails = _collect(values)
    warnings: list[str] = []
    if not emails:
        warnings.append("No valid email addresses were found.")
    return emails, warnings
