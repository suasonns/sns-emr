"""Automated tests for scripts/validate_hope_authority_sources.py.

Covers the owner-required 14 negative fixtures plus a synthetic
"Canonical Authority Package" positive fixture (all 12 required sources
genuinely populated), and the real committed CSV as a documented-gap
case (expected FAIL, because ITEM_SET_HUV and VUT_REFERENCE_MATERIAL are
honestly NOT_LOCATED).

Run with:
    python -m unittest scripts.tests.test_validate_hope_authority_sources -v
"""
from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate_hope_authority_sources as v  # noqa: E402

REAL_SOURCES_CSV = REPO_ROOT / "docs" / "compliance" / "hope" / "HOPE_AUTHORITY_SOURCES_1.0.csv"
REAL_INVENTORY_CSV = REPO_ROOT / "docs" / "compliance" / "hope" / "HOPE_OFFICIAL_ITEM_INVENTORY_1.0.csv"

FIELDS = v.REQUIRED_COLUMNS


def _row(source_id, title, classification, version="v1.00", **overrides):
    base = {f: "NONE_KNOWN" for f in FIELDS}
    base.update({
        "source_id": source_id,
        "official_title": title,
        "source_classification": classification,
        "publisher": "CMS",
        "version": version,
        "publication_date": "2025-01-01",
        "effective_date": "2025-10-01",
        "verification_date": "2026-09-29",
        "official_url": f"https://www.cms.gov/files/document/{source_id.lower()}.pdf",
        "local_storage_path": f"session-state/x/files/{source_id.lower()}.pdf",
        "sha256": "a" * 64,
        "applicable_sections": "A",
        "applicable_item_ids": "N/A",
        "mandatory_or_explanatory": "MANDATORY",
        "supersedes": "NONE_KNOWN",
        "superseded_by": "NONE_KNOWN",
        "known_conflicts": "NONE_KNOWN",
        "resolution": "N/A",
    })
    base.update(overrides)
    return base


def _canonical_rows():
    """One fully-populated row per REQUIRED_SOURCE_IDS entry."""
    titles = {
        "GUIDANCE_MANUAL_V1_02": ("HOPE Guidance Manual", "GUIDANCE_MANUAL", "v1.02"),
        "DATA_SPECS_V1_00_1": ("HOPE Data Submission Specifications", "TECHNICAL_SPECIFICATION", "v1.00.1"),
        "ERRATA_V1_00_2": ("HOPE Data Specs Errata", "ERRATA", "v1.00.2"),
        "ERRATA_V1_00_3": ("HOPE Data Specs Errata", "ERRATA", "v1.00.3"),
        "ITEM_SET_ADMISSION_V1_01": ("HOPE Admission Item Set", "ITEM_SET", "v1.01"),
        "ITEM_SET_HUV": ("HOPE HUV Item Set", "ITEM_SET", "v1.01"),
        "ITEM_SET_DISCHARGE_V1_01": ("HOPE Discharge Item Set", "ITEM_SET", "v1.01"),
        "ITEM_SET_ALL_ITEMS_V1_01": ("HOPE All Items", "ITEM_SET", "v1.01"),
        "HQRP_MEASURE_SPEC_V1_03": ("HQRP Quality Measure Specifications", "QUALITY_MEASURE_SPECIFICATION", "v1.03"),
        "HOPE_FAQ": ("HOPE Implementation FAQs", "FAQ_OR_TRAINING", "v1.0"),
        "VUT_INSTRUCTIONS_V2_2": ("Assessment Submitter User Manual", "VALIDATION_GUIDANCE", "v2.2"),
        "VUT_REFERENCE_MATERIAL": ("HOPE VUT Error Message Reference Guide", "VALIDATION_GUIDANCE", "v1.0"),
    }
    return [
        _row(sid, title, classification, version=version)
        for sid, (title, classification, version) in titles.items()
    ]


def _write_csv(rows) -> Path:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8")
    writer = csv.DictWriter(tmp, fieldnames=FIELDS)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    tmp.close()
    return Path(tmp.name)


class TestPositiveCase(unittest.TestCase):
    def test_canonical_authority_package_passes(self):
        csv_path = _write_csv(_canonical_rows())
        try:
            result = v.validate(csv_path, REAL_INVENTORY_CSV)
            # Ignore inventory cross-reference noise for this synthetic
            # fixture (title text is intentionally simplified); assert on
            # source-package-level rules only, which is what "Canonical
            # Authority Package" is required to prove.
            source_level_errors = [
                e for e in result.errors if "INVENTORY_REFERENCES_KNOWN_SOURCE" not in e
            ]
            self.assertEqual(source_level_errors, [], msg="\n".join(source_level_errors))
        finally:
            csv_path.unlink()

    def test_real_committed_sources_documents_known_gaps_only(self):
        result = v.validate(REAL_SOURCES_CSV, REAL_INVENTORY_CSV)
        self.assertFalse(result.passed)
        joined = "\n".join(result.errors)
        self.assertIn("ITEM_SET_HUV", joined)
        self.assertIn("VUT_REFERENCE_MATERIAL", joined)
        # No other required source should be reported missing/invalid.
        for req_id in v.REQUIRED_SOURCE_IDS:
            if req_id in ("ITEM_SET_HUV", "VUT_REFERENCE_MATERIAL"):
                continue
            self.assertNotIn(
                f"({req_id})", joined,
                msg=f"Unexpected error referencing {req_id}:\n{joined}"
            )


class TestNegativeCases(unittest.TestCase):
    def _assert_fails_with_rule(self, rows, rule, inventory_path=REAL_INVENTORY_CSV):
        csv_path = _write_csv(rows)
        try:
            result = v.validate(csv_path, inventory_path)
            self.assertFalse(result.passed)
            joined = "\n".join(result.errors)
            self.assertIn(rule, joined, msg=f"Expected rule {rule} in errors:\n{joined}")
        finally:
            csv_path.unlink()

    def _missing_one(self, source_id):
        return [r for r in _canonical_rows() if r["source_id"] != source_id]

    def test_missing_guidance_manual_fails(self):
        self._assert_fails_with_rule(self._missing_one("GUIDANCE_MANUAL_V1_02"), "REQUIRED_SOURCE_PRESENT")

    def test_missing_data_specifications_fails(self):
        self._assert_fails_with_rule(self._missing_one("DATA_SPECS_V1_00_1"), "REQUIRED_SOURCE_PRESENT")

    def test_missing_errata_v1_00_2_fails(self):
        self._assert_fails_with_rule(self._missing_one("ERRATA_V1_00_2"), "REQUIRED_SOURCE_PRESENT")

    def test_missing_errata_v1_00_3_fails(self):
        self._assert_fails_with_rule(self._missing_one("ERRATA_V1_00_3"), "REQUIRED_SOURCE_PRESENT")

    def test_missing_admission_item_set_fails(self):
        self._assert_fails_with_rule(self._missing_one("ITEM_SET_ADMISSION_V1_01"), "REQUIRED_SOURCE_PRESENT")

    def test_missing_huv_item_set_fails(self):
        self._assert_fails_with_rule(self._missing_one("ITEM_SET_HUV"), "REQUIRED_SOURCE_PRESENT")

    def test_missing_discharge_item_set_fails(self):
        self._assert_fails_with_rule(self._missing_one("ITEM_SET_DISCHARGE_V1_01"), "REQUIRED_SOURCE_PRESENT")

    def test_missing_hqrp_measure_specification_fails(self):
        self._assert_fails_with_rule(self._missing_one("HQRP_MEASURE_SPEC_V1_03"), "REQUIRED_SOURCE_PRESENT")

    def test_missing_faq_fails(self):
        self._assert_fails_with_rule(self._missing_one("HOPE_FAQ"), "REQUIRED_SOURCE_PRESENT")

    def test_missing_vut_instructions_fails(self):
        self._assert_fails_with_rule(self._missing_one("VUT_INSTRUCTIONS_V2_2"), "REQUIRED_SOURCE_PRESENT")

    def test_missing_sha_fails(self):
        rows = _canonical_rows()
        rows[0] = dict(rows[0])
        rows[0]["sha256"] = ""
        self._assert_fails_with_rule(rows, "REQUIRED_NON_BLANK")

    def test_missing_effective_date_fails(self):
        rows = _canonical_rows()
        rows[0] = dict(rows[0])
        rows[0]["effective_date"] = ""
        self._assert_fails_with_rule(rows, "REQUIRED_NON_BLANK")

    def test_missing_version_fails(self):
        rows = _canonical_rows()
        rows[0] = dict(rows[0])
        rows[0]["version"] = ""
        self._assert_fails_with_rule(rows, "REQUIRED_NON_BLANK")

    def test_invalid_classification_fails(self):
        rows = _canonical_rows()
        rows[0] = dict(rows[0])
        rows[0]["source_classification"] = "MADE_UP_CLASSIFICATION"
        self._assert_fails_with_rule(rows, "VALID_CLASSIFICATION")

    def test_duplicate_source_id_fails(self):
        rows = _canonical_rows()
        dup = dict(rows[0])
        rows.append(dup)
        self._assert_fails_with_rule(rows, "DUPLICATE_SOURCE_ID")

    def test_duplicate_source_version_record_fails(self):
        rows = _canonical_rows()
        dup = dict(rows[0])
        dup["source_id"] = dup["source_id"] + "_DUP"
        rows.append(dup)
        self._assert_fails_with_rule(rows, "DUPLICATE_SOURCE_VERSION_RECORD")

    def test_source_references_unknown_item_fails(self):
        rows = _canonical_rows()
        rows[0] = dict(rows[0])
        rows[0]["applicable_item_ids"] = "Z9999_NOT_A_REAL_ITEM"
        self._assert_fails_with_rule(rows, "SOURCE_REFERENCES_KNOWN_ITEM")

    def test_inventory_references_unknown_source_fails(self):
        # Build a minimal inventory citing a source that has no matching row.
        inv_fields = [
            "section", "top_level_item_id", "subitem_id", "official_title",
            "official_concept", "record_types", "timepoints", "look_back",
            "permitted_values", "caret_skip_value", "not_applicable_handling",
            "skip_dependencies", "trigger_dependencies", "correction_rule",
            "export_rule", "technical_edits", "source_document", "source_version",
            "source_location", "effective_date", "applicable_errata",
            "inventory_status", "traceability_status",
        ]
        inv_row = {f: "" for f in inv_fields}
        inv_row.update({
            "section": "A", "top_level_item_id": "A0050", "official_title": "Type of Record",
            "source_document": "A Completely Fabricated Source Nobody Registered",
            "source_version": "v9.99", "effective_date": "2025-10-01",
            "inventory_status": "OFFICIAL_ITEM_IDENTIFIED", "traceability_status": "UNVERIFIED",
        })
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8")
        writer = csv.DictWriter(tmp, fieldnames=inv_fields)
        writer.writeheader()
        writer.writerow(inv_row)
        tmp.close()
        inv_path = Path(tmp.name)
        try:
            self._assert_fails_with_rule(
                _canonical_rows(), "INVENTORY_REFERENCES_KNOWN_SOURCE", inventory_path=inv_path
            )
        finally:
            inv_path.unlink()

    def test_missing_required_column_fails(self):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8")
        writer = csv.writer(tmp)
        writer.writerow(["source_id", "official_title"])
        writer.writerow(["GUIDANCE_MANUAL_V1_02", "HOPE Guidance Manual"])
        tmp.close()
        csv_path = Path(tmp.name)
        try:
            result = v.validate(csv_path, REAL_INVENTORY_CSV)
            self.assertFalse(result.passed)
            self.assertIn("REQUIRED_COLUMNS", "\n".join(result.errors))
        finally:
            csv_path.unlink()

    def test_missing_file_fails(self):
        result = v.validate(Path("does_not_exist_authority_sources.csv"), REAL_INVENTORY_CSV)
        self.assertFalse(result.passed)
        self.assertIn("FILE_EXISTS", "\n".join(result.errors))


if __name__ == "__main__":
    unittest.main()
