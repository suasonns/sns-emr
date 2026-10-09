"""Automated tests for scripts/validate_hope_inventory.py.

Covers the owner-required negative cases plus the real committed
inventory as the positive case. Run with:

    python -m pytest scripts/tests/test_validate_hope_inventory.py -v

or, without pytest installed, simply:

    python scripts/tests/test_validate_hope_inventory.py
"""
from __future__ import annotations

import csv
import io
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate_hope_inventory as v  # noqa: E402

REAL_CSV = REPO_ROOT / "docs" / "compliance" / "hope" / "HOPE_OFFICIAL_ITEM_INVENTORY_1.0.csv"

BASE_FIELDS = [
    "section", "top_level_item_id", "subitem_id", "official_title",
    "official_concept", "record_types", "timepoints", "look_back",
    "permitted_values", "caret_skip_value", "not_applicable_handling",
    "skip_dependencies", "trigger_dependencies", "correction_rule",
    "export_rule", "technical_edits", "source_document", "source_version",
    "source_location", "effective_date", "applicable_errata",
    "inventory_status", "traceability_status",
]


def _row(**overrides):
    base = {f: "" for f in BASE_FIELDS}
    base.update({
        "source_document": "HOPE Guidance Manual",
        "source_version": "v1.02",
        "source_location": "https://www.cms.gov/files/document/hope-guidance-manual-v1-02.pdf",
        "effective_date": "2025-10-01",
        "inventory_status": "OFFICIAL_ITEM_IDENTIFIED",
        "traceability_status": "UNVERIFIED",
    })
    base.update(overrides)
    return base


def _write_csv(rows) -> Path:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8")
    writer = csv.DictWriter(tmp, fieldnames=BASE_FIELDS)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    tmp.close()
    return Path(tmp.name)


def _full_valid_inventory():
    """Builds a minimal but complete valid inventory covering every
    expected item, so single-defect test cases can be isolated by
    mutating exactly one row."""
    rows = []
    for section, ids in v.EXPECTED_TOP_LEVEL_ITEMS.items():
        for item_id in ids:
            rows.append(_row(section=section, top_level_item_id=item_id,
                              official_title=f"Title for {item_id}"))
    for subitem_id in v.EXPECTED_J2051_SUBITEMS:
        rows.append(_row(section="J", top_level_item_id="J2051", subitem_id=subitem_id,
                          official_title=f"Title for {subitem_id}"))
    return rows


class TestPositiveCase(unittest.TestCase):
    def test_real_committed_inventory_passes(self):
        result = v.validate(REAL_CSV)
        self.assertTrue(result.passed, msg="\n".join(result.errors))
        report = v.generate_report(result)
        self.assertIn("HOPE inventory validation: PASS", report)
        self.assertIn("Section A: 20", report)
        self.assertIn("Section F: 4", report)
        self.assertIn("Section I: 1", report)
        self.assertIn("Section J: 11", report)
        self.assertIn("Section M: 3", report)
        self.assertIn("Section N: 3", report)
        self.assertIn("Section Z: 3", report)
        self.assertIn("J2051 subitems: 8", report)
        self.assertIn("Top-level items: 45", report)

    def test_synthetic_full_valid_inventory_passes(self):
        csv_path = _write_csv(_full_valid_inventory())
        try:
            result = v.validate(csv_path)
            self.assertTrue(result.passed, msg="\n".join(result.errors))
        finally:
            csv_path.unlink()


class TestNegativeCases(unittest.TestCase):
    def _assert_fails_with_rule(self, rows, rule):
        csv_path = _write_csv(rows)
        try:
            result = v.validate(csv_path)
            self.assertFalse(result.passed)
            joined = "\n".join(result.errors)
            self.assertIn(rule, joined, msg=f"Expected rule {rule} in errors:\n{joined}")
        finally:
            csv_path.unlink()

    def test_duplicate_j0050_rejected(self):
        rows = _full_valid_inventory()
        rows.append(_row(section="J", top_level_item_id="J0050",
                          official_title="Duplicate Death is Imminent"))
        self._assert_fails_with_rule(rows, "UNIQUE_TOP_LEVEL_ID")

    def test_unknown_i0600_rejected(self):
        rows = _full_valid_inventory()
        rows.append(_row(section="I", top_level_item_id="I0600",
                          official_title="Retracted HOPE-DEF-009 item"))
        self._assert_fails_with_rule(rows, "NO_UNKNOWN_TOP_LEVEL_IDS")

    def test_m1190_in_wrong_section_rejected(self):
        rows = [r for r in _full_valid_inventory()
                if not (r["section"] == "M" and r["top_level_item_id"] == "M1190")]
        rows.append(_row(section="N", top_level_item_id="M1190",
                          official_title="Skin Conditions filed under wrong section"))
        # Wrong-section placement is caught by the item-ID/section prefix
        # mismatch rule, and because M1190 is now missing from Section M
        # by the required-IDs-present rule.
        csv_path = _write_csv(rows)
        try:
            result = v.validate(csv_path)
            self.assertFalse(result.passed)
            joined = "\n".join(result.errors)
            self.assertTrue(
                "ITEM_ID_MATCHES_SECTION" in joined or "REQUIRED_IDS_PRESENT" in joined,
                msg=f"Expected a wrong-section detection rule in errors:\n{joined}",
            )
        finally:
            csv_path.unlink()

    def test_j2051c_without_parent_j2051_rejected(self):
        rows = [r for r in _full_valid_inventory()
                if not (r["section"] == "J" and r["top_level_item_id"] == "J2051"
                        and not r["subitem_id"])]
        # J2051C (and other J2051 subitems) remain, but their parent J2051
        # top-level row is gone.
        self._assert_fails_with_rule(rows, "SUBITEM_PARENT_EXISTS")

    def test_section_a_count_of_19_rejected(self):
        rows = [r for r in _full_valid_inventory()
                if not (r["section"] == "A" and r["top_level_item_id"] == "A1905")]
        # Removing A1905 reproduces the original real-world miscount (19 instead of 20).
        self._assert_fails_with_rule(rows, "REQUIRED_IDS_PRESENT")

    def test_section_f_count_of_1_rejected(self):
        rows = [r for r in _full_valid_inventory()
                if not (r["section"] == "F" and r["top_level_item_id"] in
                        ("F2000", "F2200", "F3000"))]
        # Reproduces the original real-world miscount (1 instead of 4).
        self._assert_fails_with_rule(rows, "REQUIRED_IDS_PRESENT")

    def test_missing_source_version_rejected(self):
        rows = _full_valid_inventory()
        rows[0] = dict(rows[0])
        rows[0]["source_version"] = ""
        self._assert_fails_with_rule(rows, "REQUIRED_NON_BLANK")

    def test_pass_with_incomplete_trace_rejected(self):
        rows = _full_valid_inventory()
        rows[0] = dict(rows[0])
        rows[0]["traceability_status"] = "PASS"
        # record_types, timepoints, permitted_values, correction_rule,
        # export_rule, technical_edits are all left blank.
        self._assert_fails_with_rule(rows, "PASS_REQUIRES_COMPLETE_TRACE")

    def test_missing_required_column_rejected(self):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8")
        writer = csv.writer(tmp)
        writer.writerow(["section", "top_level_item_id"])  # far too few columns
        writer.writerow(["A", "A0050"])
        tmp.close()
        csv_path = Path(tmp.name)
        try:
            result = v.validate(csv_path)
            self.assertFalse(result.passed)
            self.assertIn("REQUIRED_COLUMNS", "\n".join(result.errors))
        finally:
            csv_path.unlink()

    def test_missing_file_rejected(self):
        result = v.validate(Path("does_not_exist_hope_inventory.csv"))
        self.assertFalse(result.passed)
        self.assertIn("FILE_EXISTS", "\n".join(result.errors))


if __name__ == "__main__":
    unittest.main()
