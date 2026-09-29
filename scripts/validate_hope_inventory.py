"""HOPE Official Item Inventory validator.

Reads docs/compliance/hope/HOPE_OFFICIAL_ITEM_INVENTORY_1.0.csv and
proves, by executable check rather than manual claim, that the inventory
is internally consistent and matches the approved expected-item set
derived from the CMS HOPE Guidance Manual v1.02 (see
docs/compliance/hope/HOPE_AUTHORITY_REGISTER_1.0.md, Source Record 1).

This script performs STATIC, OFFLINE validation only. It does not and
must not:
  - access patient data
  - access any production or development database
  - make any network call (including to CMS, iQIES, or the VUT)
  - import or execute application runtime code
  - modify the inventory CSV it reads

Usage:
    python scripts/validate_hope_inventory.py
    python scripts/validate_hope_inventory.py --csv <path>

Exit code 0 on PASS, 1 on FAIL. All failures are collected and reported
together (the script does not stop at the first error) so a single run
surfaces the complete list of problems.
"""
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = REPO_ROOT / "docs" / "compliance" / "hope" / "HOPE_OFFICIAL_ITEM_INVENTORY_1.0.csv"

REQUIRED_COLUMNS = [
    "section",
    "top_level_item_id",
    "subitem_id",
    "official_title",
    "official_concept",
    "record_types",
    "timepoints",
    "look_back",
    "permitted_values",
    "caret_skip_value",
    "not_applicable_handling",
    "skip_dependencies",
    "trigger_dependencies",
    "correction_rule",
    "export_rule",
    "technical_edits",
    "source_document",
    "source_version",
    "source_location",
    "effective_date",
    "applicable_errata",
    "inventory_status",
    "traceability_status",
]

# Fields that must never be blank for any row, regardless of trace depth.
REQUIRED_NON_BLANK_FIELDS = [
    "section",
    "top_level_item_id",
    "official_title",
    "source_document",
    "source_version",
    "source_location",
    "effective_date",
    "inventory_status",
    "traceability_status",
]

ALLOWED_SECTIONS = {"A", "F", "I", "J", "M", "N", "Z"}

ALLOWED_INVENTORY_STATUS = {
    "OFFICIAL_ITEM_IDENTIFIED",
    "OFFICIAL_SUBITEM_IDENTIFIED",
}

ALLOWED_TRACEABILITY_STATUS = {
    "PASS",
    "FAIL",
    "PARTIAL",
    "NOT IMPLEMENTED",
    "NOT APPLICABLE",
    "UNVERIFIED",
}

# Fields that a row MUST have populated (non-blank) before it may be
# marked PASS. This is what "PASS is rejected when required trace fields
# remain incomplete" means in executable form.
PASS_REQUIRED_FIELDS = [
    "record_types",
    "timepoints",
    "permitted_values",
    "correction_rule",
    "export_rule",
    "technical_edits",
]

# The approved expected top-level item set, derived from the CMS HOPE
# Guidance Manual v1.02 per docs/compliance/hope/HOPE_AUTHORITY_REGISTER_1.0.md
# Source Record 1, and cross-checked in
# docs/compliance/hope/HOPE_GAP_AND_DEFECT_REGISTER_1.0.md's
# inventory-count-correction entry (Section A=20, F=4, I=1, J=11, M=3,
# N=3, Z=3). This is the "approved expected-item set" the validator
# compares actual CSV rows against - it is not hard-coded totals only.
EXPECTED_TOP_LEVEL_ITEMS = {
    "A": [
        "A0050", "A0100", "A0215", "A0220", "A0250", "A0270", "A0500",
        "A0550", "A0600", "A0700", "A0810", "A0900", "A1005", "A1010",
        "A1110", "A1400", "A1805", "A1905", "A1910", "A2115",
    ],
    "F": ["F2000", "F2100", "F2200", "F3000"],
    "I": ["I0010"],
    "J": [
        "J0050", "J0900", "J0905", "J0910", "J0915", "J2030", "J2040",
        "J2050", "J2051", "J2052", "J2053",
    ],
    "M": ["M1190", "M1195", "M1200"],
    "N": ["N0500", "N0510", "N0520"],
    "Z": ["Z0350", "Z0400", "Z0500"],
}

EXPECTED_J2051_SUBITEMS = [
    "J2051A", "J2051B", "J2051C", "J2051D", "J2051E", "J2051F", "J2051G", "J2051H",
]

ITEM_ID_SECTION_PREFIX = {
    "A": "A",
    "F": "F",
    "I": "I",
    "J": "J",
    "M": "M",
    "N": "N",
    "Z": "Z",
}


@dataclass
class Row:
    index: int  # 1-based data row number (header excluded), for error messages
    data: dict


@dataclass
class ValidationResult:
    errors: list = field(default_factory=list)
    rows: list = field(default_factory=list)

    def add_error(self, row_index, item_id, rule, message):
        location = f"row {row_index}" if row_index is not None else "file-level"
        item = f" ({item_id})" if item_id else ""
        self.errors.append(
            f"{location}{item}: RULE={rule} :: {message}"
        )

    @property
    def passed(self):
        return len(self.errors) == 0


def load_rows(csv_path: Path):
    """Returns (rows, header_errors). Does not raise on missing columns;
    reports them as errors so the caller gets a complete picture."""
    header_errors = []
    rows = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames or []
        missing = [c for c in REQUIRED_COLUMNS if c not in fieldnames]
        if missing:
            header_errors.append(
                f"Missing required column(s): {', '.join(missing)}"
            )
        for i, raw in enumerate(reader, start=1):
            rows.append(Row(index=i, data=raw))
    return rows, header_errors


def _is_blank(value) -> bool:
    return value is None or str(value).strip() == ""


def validate(csv_path: Path) -> ValidationResult:
    result = ValidationResult()

    if not csv_path.exists():
        result.add_error(None, None, "FILE_EXISTS", f"Inventory file not found: {csv_path}")
        return result

    rows, header_errors = load_rows(csv_path)
    for msg in header_errors:
        result.add_error(None, None, "REQUIRED_COLUMNS", msg)
    if header_errors:
        # Column-level errors make per-row validation unreliable; stop here.
        return result

    result.rows = rows

    seen_top_level_ids = {}
    seen_subitem_ids = {}
    top_level_ids_by_section = {}

    for row in rows:
        d = row.data
        item_id = (d.get("top_level_item_id") or "").strip()
        subitem_id = (d.get("subitem_id") or "").strip()
        section = (d.get("section") or "").strip()
        inventory_status = (d.get("inventory_status") or "").strip()
        traceability_status = (d.get("traceability_status") or "").strip()
        display_id = subitem_id or item_id or "<blank id>"

        for col in REQUIRED_NON_BLANK_FIELDS:
            if _is_blank(d.get(col)):
                result.add_error(
                    row.index, display_id, "REQUIRED_NON_BLANK",
                    f"Column '{col}' must not be blank. Fix: populate '{col}' for this row."
                )

        if section and section not in ALLOWED_SECTIONS:
            result.add_error(
                row.index, display_id, "VALID_SECTION",
                f"Section '{section}' is not one of {sorted(ALLOWED_SECTIONS)}. "
                f"Fix: correct the section column or confirm this is truly an official HOPE section."
            )

        if item_id:
            expected_prefix = ITEM_ID_SECTION_PREFIX.get(section)
            if expected_prefix and not item_id.startswith(expected_prefix):
                result.add_error(
                    row.index, display_id, "ITEM_ID_MATCHES_SECTION",
                    f"top_level_item_id '{item_id}' does not start with the declared "
                    f"section prefix '{expected_prefix}'. Fix: correct the section or item ID."
                )

        if item_id and not subitem_id:
            if item_id in seen_top_level_ids:
                result.add_error(
                    row.index, item_id, "UNIQUE_TOP_LEVEL_ID",
                    f"Duplicate top-level item ID '{item_id}' "
                    f"(first seen at row {seen_top_level_ids[item_id]}). "
                    f"Fix: remove the duplicate row or correct the item ID."
                )
            else:
                seen_top_level_ids[item_id] = row.index
                top_level_ids_by_section.setdefault(section, []).append(item_id)

        if subitem_id:
            if subitem_id in seen_subitem_ids:
                result.add_error(
                    row.index, subitem_id, "UNIQUE_SUBITEM_ID",
                    f"Duplicate subitem ID '{subitem_id}' "
                    f"(first seen at row {seen_subitem_ids[subitem_id]}). "
                    f"Fix: remove the duplicate row or correct the subitem ID."
                )
            else:
                seen_subitem_ids[subitem_id] = row.index

            if not item_id:
                result.add_error(
                    row.index, subitem_id, "SUBITEM_HAS_PARENT",
                    "Subitem row has no top_level_item_id (parent). "
                    "Fix: populate the parent top-level item ID for this subitem."
                )
            elif item_id not in seen_top_level_ids:
                result.add_error(
                    row.index, subitem_id, "SUBITEM_PARENT_EXISTS",
                    f"Subitem '{subitem_id}' references parent '{item_id}', but no "
                    f"top-level row for '{item_id}' exists elsewhere in the inventory. "
                    f"Fix: add the missing top-level row or correct the parent reference."
                )
            if not subitem_id.startswith(item_id):
                result.add_error(
                    row.index, subitem_id, "SUBITEM_SAME_SECTION_AS_PARENT",
                    f"Subitem ID '{subitem_id}' does not begin with its declared parent "
                    f"ID '{item_id}'; cannot confirm it belongs to the same item/section. "
                    f"Fix: correct the subitem ID or parent reference."
                )

        eff_date = (d.get("effective_date") or "").strip()
        if eff_date:
            try:
                date.fromisoformat(eff_date)
            except ValueError:
                result.add_error(
                    row.index, display_id, "EFFECTIVE_DATE_PARSEABLE",
                    f"effective_date '{eff_date}' is not an ISO 8601 date (YYYY-MM-DD). "
                    f"Fix: reformat the date."
                )

        if inventory_status and inventory_status not in ALLOWED_INVENTORY_STATUS:
            result.add_error(
                row.index, display_id, "VALID_INVENTORY_STATUS",
                f"inventory_status '{inventory_status}' is not one of "
                f"{sorted(ALLOWED_INVENTORY_STATUS)}. Fix: use an allowed value."
            )

        if traceability_status and traceability_status not in ALLOWED_TRACEABILITY_STATUS:
            result.add_error(
                row.index, display_id, "VALID_TRACEABILITY_STATUS",
                f"traceability_status '{traceability_status}' is not one of "
                f"{sorted(ALLOWED_TRACEABILITY_STATUS)}. Fix: use an allowed value."
            )

        if traceability_status == "PASS":
            incomplete = [c for c in PASS_REQUIRED_FIELDS if _is_blank(d.get(c))]
            if incomplete:
                result.add_error(
                    row.index, display_id, "PASS_REQUIRES_COMPLETE_TRACE",
                    f"traceability_status is PASS but required trace field(s) are blank: "
                    f"{', '.join(incomplete)}. Fix: complete these fields or downgrade the "
                    f"status to PARTIAL/UNVERIFIED."
                )

    all_expected_top_level = {
        item_id for ids in EXPECTED_TOP_LEVEL_ITEMS.values() for item_id in ids
    }
    actual_top_level = set(seen_top_level_ids.keys())

    unknown_top_level = actual_top_level - all_expected_top_level
    for unknown_id in sorted(unknown_top_level):
        result.add_error(
            seen_top_level_ids[unknown_id], unknown_id, "NO_UNKNOWN_TOP_LEVEL_IDS",
            f"Item ID '{unknown_id}' is present in the inventory but is not in the "
            f"approved expected-item set derived from the CMS Guidance Manual v1.02. "
            f"Fix: remove it, or add it to EXPECTED_TOP_LEVEL_ITEMS in this validator "
            f"with a cited controlling source, per the HOPE-DEF-009 retraction lesson."
        )

    missing_top_level = all_expected_top_level - actual_top_level
    for missing_id in sorted(missing_top_level):
        result.add_error(
            None, missing_id, "REQUIRED_IDS_PRESENT",
            f"Expected official item '{missing_id}' is missing from the inventory. "
            f"Fix: add the missing row."
        )

    actual_subitems = set(seen_subitem_ids.keys())
    expected_subitems = set(EXPECTED_J2051_SUBITEMS)
    unknown_subitems = actual_subitems - expected_subitems
    for unknown_id in sorted(unknown_subitems):
        result.add_error(
            seen_subitem_ids[unknown_id], unknown_id, "NO_UNKNOWN_SUBITEM_IDS",
            f"Subitem ID '{unknown_id}' is not in the approved expected J2051 subitem set. "
            f"Fix: remove it or add it to EXPECTED_J2051_SUBITEMS with a cited source."
        )
    missing_subitems = expected_subitems - actual_subitems
    for missing_id in sorted(missing_subitems):
        result.add_error(
            None, missing_id, "REQUIRED_SUBITEM_IDS_PRESENT",
            f"Expected J2051 subitem '{missing_id}' is missing. Fix: add the missing row."
        )

    for section, expected_ids in EXPECTED_TOP_LEVEL_ITEMS.items():
        actual_in_section = top_level_ids_by_section.get(section, [])
        if len(actual_in_section) != len(expected_ids) and not (
            unknown_top_level or missing_top_level
        ):
            result.add_error(
                None, section, "SECTION_COUNT_CONSISTENCY",
                f"Section {section} has {len(actual_in_section)} top-level row(s) in the "
                f"inventory but {len(expected_ids)} expected. Fix: reconcile the rows."
            )

    return result


def generate_report(result: ValidationResult) -> str:
    lines = []
    if result.passed:
        counts_by_section = {}
        for row in result.rows:
            d = row.data
            if (d.get("subitem_id") or "").strip():
                continue
            section = (d.get("section") or "").strip()
            if section:
                counts_by_section[section] = counts_by_section.get(section, 0) + 1
        subitem_count = sum(
            1 for row in result.rows if (row.data.get("subitem_id") or "").strip()
        )
        top_level_count = sum(counts_by_section.values())

        lines.append("HOPE inventory validation: PASS")
        lines.append(f"Top-level items: {top_level_count}")
        lines.append(f"J2051 subitems: {subitem_count}")
        for section in sorted(counts_by_section):
            lines.append(f"Section {section}: {counts_by_section[section]}")
    else:
        lines.append("HOPE inventory validation: FAIL")
        lines.append(f"{len(result.errors)} error(s) found:")
        for err in result.errors:
            lines.append(f"  - {err}")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV,
                         help="Path to the HOPE official item inventory CSV")
    args = parser.parse_args(argv)

    result = validate(args.csv)
    print(generate_report(result))
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
