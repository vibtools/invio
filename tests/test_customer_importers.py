from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from src.customers.importers import import_customers, import_emails


class CustomerImporterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_structured_csv_imports_explicit_customer_data(self):
        path = self.root / "customers.csv"
        path.write_text("email,name,country\nAlice@Example.com,Alice,us\nbob@example.com,,BD\n", encoding="utf-8")
        result = import_customers(path)
        self.assertTrue(result.structured)
        self.assertEqual([(r.email, r.name, r.country) for r in result.records], [
            ("alice@example.com", "Alice", "US"),
            ("bob@example.com", "", "BD"),
        ])
        self.assertEqual(result.issues, [])

    def test_structured_rows_report_missing_invalid_email_country_and_conflicts(self):
        path = self.root / "customers.tsv"
        path.write_text(
            "email\tname\tcountry\n"
            "\tMissing\tUS\n"
            "not-an-email\tBad\tUS\n"
            "ok@example.com\tOk\tUSA\n"
            "same@example.com\tFirst\tUS\n"
            "same@example.com\tSecond\tGB\n",
            encoding="utf-8",
        )
        result = import_customers(path)
        self.assertEqual([r.email for r in result.records], ["same@example.com"])
        text = "\n".join(issue.display() for issue in result.issues)
        self.assertIn("Row 2: email is missing", text)
        self.assertIn("Row 3: email format is invalid", text)
        self.assertIn("Row 4: country must be a two-letter code", text)
        self.assertIn("Row 6: duplicate customer data conflicts", text)

    def test_same_file_duplicate_first_row_wins(self):
        path = self.root / "customers.csv"
        path.write_text(
            "email,name,country\n"
            "same@example.com,First,US\n"
            "SAME@example.com,First,US\n",
            encoding="utf-8",
        )
        result = import_customers(path)
        self.assertEqual(len(result.records), 1)
        self.assertEqual(result.duplicates_skipped, 1)
        self.assertEqual(result.records[0].name, "First")

    def test_legacy_csv_without_email_header_preserves_email_extraction(self):
        path = self.root / "legacy.csv"
        path.write_text("Contact\nSend to A@example.com today\nB@example.com\n", encoding="utf-8")
        result = import_customers(path)
        self.assertFalse(result.structured)
        self.assertEqual([r.email for r in result.records], ["a@example.com", "b@example.com"])
        emails, warnings = import_emails(path)
        self.assertEqual(emails, ["a@example.com", "b@example.com"])
        self.assertEqual(warnings, [])

    def test_txt_remains_legacy_email_only_and_never_guesses_metadata(self):
        path = self.root / "legacy.txt"
        path.write_text("A@example.com\nB@example.com\n", encoding="utf-8")
        result = import_customers(path)
        self.assertEqual([(r.email, r.name, r.country) for r in result.records], [
            ("a@example.com", "", ""),
            ("b@example.com", "", ""),
        ])

    def test_structured_xlsx_supported(self):
        path = self.root / "customers.xlsx"
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["email", "name", "country"])
        sheet.append(["a@example.com", "Alice", "gb"])
        workbook.save(path)
        workbook.close()
        result = import_customers(path)
        self.assertEqual([(r.email, r.name, r.country) for r in result.records], [("a@example.com", "Alice", "GB")])


    def test_structured_xlsm_supported(self):
        path = self.root / "customers.xlsm"
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["email", "name", "country"] )
        sheet.append(["macro@example.com", "Macro", "ca"])
        workbook.save(path)
        workbook.close()
        result = import_customers(path)
        self.assertEqual([(r.email, r.name, r.country) for r in result.records], [("macro@example.com", "Macro", "CA")])

    def test_structured_country_requires_ascii_two_letter_code(self):
        path = self.root / "customers.csv"
        path.write_text("email,name,country\na@example.com,Alice,éé\n", encoding="utf-8")
        result = import_customers(path)
        self.assertEqual(result.records, [])
        self.assertEqual(len(result.issues), 1)
        self.assertIn("Row 2: country must be a two-letter code", result.issues[0].display())

    def test_import_records_retain_source_rows_for_existing_list_conflicts(self):
        path = self.root / "customers.csv"
        path.write_text("email,name,country\na@example.com,Alicia,GB\n", encoding="utf-8")
        result = import_customers(path)
        self.assertEqual(result.record_rows, [2])

    def test_malformed_workbook_is_reported_as_value_error(self):
        path = self.root / "broken.xlsx"
        path.write_bytes(b"not-an-xlsx")
        with self.assertRaisesRegex(ValueError, "Customer file could not be read"):
            import_customers(path)

if __name__ == "__main__":
    unittest.main()
