"""HOPE Authority Source Package validator.

Reads docs/compliance/hope/HOPE_AUTHORITY_SOURCES_1.0.csv (the
machine-readable companion to HOPE_AUTHORITY_REGISTER_1.0.md) and proves,
by executable check, whether the required CMS/QTSO authority-source
package is complete, internally consistent, and cross-referenced against
the Official Item Inventory.

Static, offline validation only. No network access, no database access,
no patient data, no application runtime import. Does not modify the
files it reads.

Usage:
    python scripts/validate_hope_authority_sources.py
    python scripts/validate_hope_authority_sources.py --sources <path> --inventory <path>

Exit code 0 on PASS, 1 on FAIL.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCES_CSV = REPO_ROOT / "docs" / "compliance" / "hope" / "HOPE_AUTHORITY_SOURCES_1.0.csv"
DEFAULT_INVENTORY_CSV = REPO_ROOT / "docs" / "compliance" / "hope" / "HOPE_OFFICIAL_ITEM_INVENTORY_1.0.csv"

REQUIRED_COLUMNS = [
    "source_id",
    "official_title",
    "source_classification",
    "publisher",
    "version",
    "publication_date",
    "effective_date",
    "verification_date",
    "official_url",
    "local_storage_path",
    "sha256",
    "applicable_sections",
    "applicable_item_ids",
    "mandatory_or_explanatory",
    "supersedes",
    "superseded_by",
    "known_conflicts",
    "resolution",
]

# Every field below must be non-blank text (a sentinel like NOT_LOCATED,
# UNVERIFIED, N/A, or NONE_KNOWN counts as a populated, honest value; an
# empty string does not).
REQUIRED_NON_BLANK_FIELDS = REQUIRED_COLUMNS[:]  # every column is required to be present, non-blank

ALLOWED_CLASSIFICATIONS = {
    "GUIDANCE_MANUAL",
    "ITEM_SET",
    "TECHNICAL_SPECIFICATION",
    "ERRATA",
    "QUALITY_MEASURE_SPECIFICATION",
    "FAQ_OR_TRAINING",
    "VALIDATION_GUIDANCE",
    "SNS_POLICY",
}

ALLOWED_MANDATORY_VALUES = {"MANDATORY", "EXPLANATORY"}

# Sentinel values meaning "this required source has not actually been
# located/populated yet" - used to detect MISSING sources even though the
# row exists as a placeholder (so the CSV can honestly record an open gap
# without silently disappearing from the report).
NOT_LOCATED_SENTINELS = {"NOT_LOCATED", "NOT_RETAINED", "NOT_COMPUTED"}

# The owner's required source inventory (12 distinct source_ids across
# categories A-G). Every one of these must have a row in the CSV; a row
# that exists but is entirely sentinel-valued (NOT_LOCATED) is reported as
# MISSING, not silently treated as satisfied.
REQUIRED_SOURCE_IDS = [
    "GUIDANCE_MANUAL_V1_02",
    "DATA_SPECS_V1_00_1",
    "ERRATA_V1_00_2",
    "ERRATA_V1_00_3",
    "ITEM_SET_ADMISSION_V1_01",
    "ITEM_SET_HUV",
    "ITEM_SET_DISCHARGE_V1_01",
    "ITEM_SET_ALL_ITEMS_V1_01",
    "HQRP_MEASURE_SPEC_V1_03",
    "HOPE_FAQ",
    "VUT_INSTRUCTIONS_V2_2",
    "VUT_REFERENCE_MATERIAL",
]

# Tokens used in applicable_item_ids that are sentinels/wildcards, not
# actual item IDs, and must not be checked against the inventory.
ITEM_ID_SENTINELS = {
    "N/A", "GENERAL", "UNVERIFIED", "UNKNOWN", "UNVERIFIED_NOT_CROSS_CHECKED",
    "ALL_45_TOP_LEVEL_PLUS_8_J2051_SUBITEMS", "ALL_SUBMITTED_ITEMS",
}


@dataclass
class SourceRow:
    index: int
    data: dict


@dataclass
class ValidationResult:
    errors: list = field(default_factory=list)
    rows: list = field(default_factory=list)

    def add_error(self, row_index, source_id, rule, message):
        location = f"row {row_index}" if row_index is not None else "file-level"
        ident = f" ({source_id})" if source_id else ""
        self.errors.append(f"{location}{ident}: RULE={rule} :: {message}")

    @property
    def passed(self):
        return len(self.errors) == 0


def _title_words(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _title_matches(doc: str, title: str) -> bool:
    """A cited inventory source_document is considered to match an
    authority source's official_title when every significant word in the
    (shorter) document citation also appears in the title's word set -
    tolerating punctuation/parenthetical differences like
    'HOPE Guidance Manual' vs 'Hospice Outcomes and Patient Evaluation
    (HOPE) Guidance Manual'."""
    doc_words = _title_words(doc)
    title_words = _title_words(title)
    if not doc_words or not title_words:
        return False
    return doc_words.issubset(title_words) or title_words.issubset(doc_words)


def _is_blank(value) -> bool:
    return value is None or str(value).strip() == ""


def load_sources(csv_path: Path):
    header_errors = []
    rows = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames or []
        missing = [c for c in REQUIRED_COLUMNS if c not in fieldnames]
        if missing:
            header_errors.append(f"Missing required column(s): {', '.join(missing)}")
        for i, raw in enumerate(reader, start=1):
            rows.append(SourceRow(index=i, data=raw))
    return rows, header_errors


def load_inventory_item_ids(inventory_path: Path):
    """Returns the set of every known top-level and subitem ID in the
    Official Item Inventory, for source-to-item cross-reference checks."""
    ids = set()
    if not inventory_path.exists():
        return ids
    with inventory_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            top = (row.get("top_level_item_id") or "").strip()
            sub = (row.get("subitem_id") or "").strip()
            if top:
                ids.add(top)
            if sub:
                ids.add(sub)
    return ids


def load_inventory_source_citations(inventory_path: Path):
    """Returns the distinct (source_document, source_version) pairs cited
    across the inventory, for inventory-to-source cross-reference checks."""
    citations = set()
    if not inventory_path.exists():
        return citations
    with inventory_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            doc = (row.get("source_document") or "").strip()
            ver = (row.get("source_version") or "").strip()
            if doc or ver:
                citations.add((doc, ver))
    return citations


def validate(sources_path: Path, inventory_path: Path) -> ValidationResult:
    result = ValidationResult()

    if not sources_path.exists():
        result.add_error(None, None, "FILE_EXISTS", f"Authority sources file not found: {sources_path}")
        return result

    rows, header_errors = load_sources(sources_path)
    for msg in header_errors:
        result.add_error(None, None, "REQUIRED_COLUMNS", msg)
    if header_errors:
        return result

    result.rows = rows

    seen_source_ids = {}
    seen_title_version = {}
    present_source_ids = set()
    missing_source_ids = []

    for row in rows:
        d = row.data
        source_id = (d.get("source_id") or "").strip()
        title = (d.get("official_title") or "").strip()
        classification = (d.get("source_classification") or "").strip()
        version = (d.get("version") or "").strip()
        official_url = (d.get("official_url") or "").strip()
        local_path = (d.get("local_storage_path") or "").strip()
        sha256 = (d.get("sha256") or "").strip()
        effective_date = (d.get("effective_date") or "").strip()
        verification_date = (d.get("verification_date") or "").strip()
        mandatory = (d.get("mandatory_or_explanatory") or "").strip()

        for col in REQUIRED_NON_BLANK_FIELDS:
            if _is_blank(d.get(col)):
                result.add_error(
                    row.index, source_id or "<blank id>", "REQUIRED_NON_BLANK",
                    f"Column '{col}' must not be blank (use an explicit sentinel like "
                    f"NOT_LOCATED/UNVERIFIED/N/A/NONE_KNOWN if genuinely unknown). "
                    f"Fix: populate '{col}'."
                )

        if source_id:
            if source_id in seen_source_ids:
                result.add_error(
                    row.index, source_id, "DUPLICATE_SOURCE_ID",
                    f"Duplicate source_id '{source_id}' (first seen at row {seen_source_ids[source_id]}). "
                    f"Fix: remove or rename the duplicate."
                )
            else:
                seen_source_ids[source_id] = row.index
                present_source_ids.add(source_id)

        if title and version and version not in NOT_LOCATED_SENTINELS and version != "UNVERSIONED":
            key = (title.lower(), version.lower())
            if key in seen_title_version:
                result.add_error(
                    row.index, source_id, "DUPLICATE_SOURCE_VERSION_RECORD",
                    f"Duplicate (official_title, version) pair {key} "
                    f"(first seen at row {seen_title_version[key]}). "
                    f"Fix: merge or distinguish the two rows."
                )
            else:
                seen_title_version[key] = row.index

        if classification and classification not in ALLOWED_CLASSIFICATIONS:
            result.add_error(
                row.index, source_id, "VALID_CLASSIFICATION",
                f"source_classification '{classification}' is not one of "
                f"{sorted(ALLOWED_CLASSIFICATIONS)}. Fix: use an allowed value."
            )

        if mandatory and mandatory not in ALLOWED_MANDATORY_VALUES:
            result.add_error(
                row.index, source_id, "VALID_MANDATORY_FLAG",
                f"mandatory_or_explanatory '{mandatory}' is not one of "
                f"{sorted(ALLOWED_MANDATORY_VALUES)}. Fix: use an allowed value."
            )

        # A source counts as MISSING only when the source itself has not
        # been located (no real version or URL). Binary-not-retained
        # (local_path/sha256 = NOT_RETAINED/NOT_COMPUTED) is a separately
        # disclosed tool limitation, not evidence the source is absent -
        # it must not be conflated with a genuinely missing source.
        is_missing = version in NOT_LOCATED_SENTINELS or official_url in NOT_LOCATED_SENTINELS
        if is_missing and source_id:
            missing_source_ids.append(source_id)
        else:
            if effective_date and effective_date not in ("N/A",):
                try:
                    date.fromisoformat(effective_date)
                except ValueError:
                    result.add_error(
                        row.index, source_id, "EFFECTIVE_DATE_PARSEABLE",
                        f"effective_date '{effective_date}' is not ISO 8601 (YYYY-MM-DD) or 'N/A'. "
                        f"Fix: reformat the date."
                    )
            if verification_date:
                try:
                    date.fromisoformat(verification_date)
                except ValueError:
                    result.add_error(
                        row.index, source_id, "VERIFICATION_DATE_PARSEABLE",
                        f"verification_date '{verification_date}' is not ISO 8601 (YYYY-MM-DD). "
                        f"Fix: reformat the date."
                    )

    for req_id in REQUIRED_SOURCE_IDS:
        if req_id not in present_source_ids:
            result.add_error(
                None, req_id, "REQUIRED_SOURCE_PRESENT",
                f"Required authority source '{req_id}' has no row at all in the CSV. "
                f"Fix: add a row, even if only to honestly record it as NOT_LOCATED."
            )
        elif req_id in missing_source_ids:
            result.add_error(
                None, req_id, "REQUIRED_SOURCE_POPULATED",
                f"Required authority source '{req_id}' exists as a row but is not yet "
                f"actually located/populated (version, URL, or storage+hash are sentinel "
                f"values). This source is MISSING for compliance purposes. "
                f"Fix: locate and populate the source, or keep as an explicitly approved gap."
            )

    inventory_item_ids = load_inventory_item_ids(inventory_path)
    for row in rows:
        d = row.data
        source_id = (d.get("source_id") or "").strip()
        applicable_ids_raw = (d.get("applicable_item_ids") or "").strip()
        if not applicable_ids_raw or applicable_ids_raw in ITEM_ID_SENTINELS:
            continue
        for token in applicable_ids_raw.split(";"):
            token = token.strip()
            if not token or token in ITEM_ID_SENTINELS:
                continue
            if inventory_item_ids and token not in inventory_item_ids:
                result.add_error(
                    row.index, source_id, "SOURCE_REFERENCES_KNOWN_ITEM",
                    f"applicable_item_ids references '{token}', which is not a known "
                    f"top-level or subitem ID in the Official Item Inventory. "
                    f"Fix: correct the item ID or add it to the inventory with a cited source."
                )

    inventory_citations = load_inventory_source_citations(inventory_path)
    known_title_versions = {
        (row.data.get("official_title", "").strip().lower(), row.data.get("version", "").strip().lower())
        for row in rows
    }
    for doc, ver in inventory_citations:
        matched = any(
            _title_matches(doc, title)
            for title, version in known_title_versions
            if ver.lower() == version
        )
        if not matched:
            result.add_error(
                None, None, "INVENTORY_REFERENCES_KNOWN_SOURCE",
                f"Inventory cites source_document='{doc}', source_version='{ver}', which does "
                f"not match any row in the Authority Sources CSV by title/version. "
                f"Fix: add the missing authority source row or correct the inventory citation."
            )

    return result


def generate_report(result: ValidationResult) -> str:
    lines = []
    if result.passed:
        lines.append("HOPE authority source package validation: PASS")
        lines.append(f"Total required sources: {len(REQUIRED_SOURCE_IDS)}")
        lines.append(f"Total source rows: {len(result.rows)}")
    else:
        lines.append("HOPE authority source package validation: FAIL")
        lines.append(f"{len(result.errors)} error(s) found:")
        for err in result.errors:
            lines.append(f"  - {err}")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES_CSV)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY_CSV)
    args = parser.parse_args(argv)

    result = validate(args.sources, args.inventory)
    print(generate_report(result))
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
