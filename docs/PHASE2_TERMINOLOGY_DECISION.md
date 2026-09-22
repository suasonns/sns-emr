# PHASE2_TERMINOLOGY_DECISION.md

**Document Status:** ACTIVE

**Status:** Ratified. Repository-evidence-based. No inference, no
extrapolation.

## Term

`ACP`

## Approved Meaning

**Advance Care Planning** — a RNICA clinical concept covering a
patient's code status and end-of-life treatment preferences.

## Source

`docs/tenant-platform/RNICA_ACP_SIX_FIELD_RECONCILIATION_DECISION.md` —
defines the approved 6-field ACP target:

1. CPR Preference Discussion Status
2. Code Status
3. Life-Sustaining Treatment Discussion Status
4. Life-Sustaining Treatment Preference
5. Hospitalization Preference Discussion Status
6. Hospitalization Preference

## Repository Occurrence Count

- **33 / 33 files** containing the token `ACP` use it to mean Advance Care
  Planning. Zero exceptions.
- **~210 total occurrences** reviewed across:
  - 7 backend files: `app/services/contact_sync_service.py`,
    `app/services/code_status_sync_service.py`, `app/api/patient_contacts.py`,
    `app/api/patient_code_status.py`,
    `alembic/versions/a1c2d3e4f5b6_add_patient_contacts.py`,
    `app/models/patient_contact.py`, `app/models/patient_code_status.py`
  - 26 documentation files, including
    `RNICA_ACP_SIX_FIELD_RECONCILIATION_DECISION.md`,
    `RNICA_PHASED_IMPLEMENTATION_PLAN.md` ("Increment 9 — ACP & Goals of
    Care"), `RNICA_LOCK_READINESS_MATRIX.md`, `RNICA_DATA_MAPPING_MATRIX.md`,
    `RNICA_CURRENT_TO_TARGET_GAP_REPORT.md`,
    `RNICA_IMPLEMENTATION_AUTHORITY.md`,
    `RNICA_IMPLEMENTATION_PLANNING_HANDOFF.md`,
    `RNICA_GITHUB_HANDOFF_PLAN.md`, `PATIENT_CHART_AUTHORITY_MAP.md`,
    `RNICA_COMPLETION_LEDGER.md`, `SNS_HOPE_HARVEST_RECONCILIATION_1.0.md`,
    `SNS_IMPLEMENTATION_GAP_REPORT_1.0.md`,
    `SNS_MIGRATION_COMPLEXITY_RATINGS_1.0.md`,
    `SNS_RNICA_API_MAPPING_1.0.md`, `SNS_RNICA_BUILD_SEQUENCING_2.0.md`,
    `SNS_RNICA_GAP_VALIDATION_2.0.md`,
    `SNS_RNICA_HOPE_CROSSWALK_VERIFICATION_2.0.md`,
    `SNS_RNICA_NARRATIVE_SOURCE_INVENTORY_1.0.md`,
    `SNS_RNICA_SECTION_1_IMPLEMENTATION_CONTRACT.md`,
    `SNS_RNICA_SECTION_INVENTORY_1.0.md`,
    `SNS_RNICA_VALIDATION_INVENTORY_1.0.md`, plus 6 further RNICA
    tenant-platform documents.

## Prohibited Meaning

**Access Control Policy.**

- Repository occurrence count: **0**.
- This meaning was introduced by the assistant during Phase 2 planning
  without repository grounding. It is not a defined term, workstream, or
  abstraction anywhere in this codebase and must not be created as one.

## Evidence Summary

Every occurrence of `ACP` in this repository — in code comments, model
docstrings, sync-service module docstrings, and all 26 RNICA/HOPE planning
documents — refers to the clinical concept of Advance Care Planning (Code
Status, Life-Sustaining Treatment Preference, Hospitalization Preference,
and their paired discussion-status fields, per CMS HOPE items
F2000/F2100/F2200). No occurrence, in any file, uses `ACP` to mean an
access-control or permission-enforcement abstraction.

## Rule Going Forward

`ACP` = Advance Care Planning, always, in this repository.

Authority model work, RBAC enforcement, and permission/audit enforcement
must be referred to by their actual repository-defined terms only:

- **Authority enforcement** (`ROLE_AUTHORITY_RANK`, `role_authority_rank()`
  — `backend/app/core/roles.py`)
- **RBAC enforcement** (`role_can()`, `PLATFORM_PERMISSION_MATRIX` —
  `backend/app/core/roles.py`)
- **Permission enforcement** (route-level `role_can()` / dependency checks)
- **Audit enforcement** (`log_event()` — `backend/app/services/audit_logger.py`;
  `AuditLog` — `backend/app/models/audit_log.py`)

These four terms must never be labeled or referred to as "ACP" in this
repository, in planning documents, or in implementation work.

## General Rule for Future Ambiguous Terms

When a term is ambiguous:

1. Search the repository for every occurrence.
2. Collect and document the evidence (file, location, exact phrase,
   surrounding context).
3. Identify the repository's actual meaning from that evidence.
4. Do not infer. Do not extrapolate. Do not introduce new terminology not
   already present in the repository.

Repository evidence always wins over an externally-assumed definition.
