# SNS RNICA Database Mapping 1.0 — Phase 1, Deliverable 2

**STATUS: FROZEN — ACCEPTED COMPLETE (2026-08-21)**
No further edits except factual corrections.

## INVENTORY RULE

This document maps existing fields to their actual current database
implementation. It does not modify `SNS_RNICA_FIELD_INVENTORY_1.0`,
`SNS_RNICA_MASTER_MAP_1.0`, or `SNS_HOPE_CROSSWALK_1.0`. It does not
reorganize sections and does not discuss future architecture.

Database records reality. This document records reality.

Source of truth: `backend/app/models/*.py` (SQLAlchemy models),
`backend/alembic/versions/*.py` (migrations), `backend/app/api/visits.py`
(RNICA save/update endpoints and sync functions).

Field list, order, and section numbering are taken as-is from
`SNS_RNICA_FIELD_INVENTORY_1.0` — Sections 1-28, current RNICA order.

## Output columns

Section | Field | Table | Column | Type | Nullable | Default | FK | Enum | Notes

## Methodology note (read before the tables)

The current RNICA implementation persists nearly all assessment data as a
single JSONB document, not as individual relational columns. Concretely:

- **Primary/authoritative table for all 28 sections:** `rnica_assessments`.
  Every field documented in `SNS_RNICA_FIELD_INVENTORY_1.0` lives inside
  its single `form_data` column (JSONB), at the JSON path already given in
  that document (e.g. `demographics.firstName`,
  `musculoskeletal.adl.bathing`).
- There is **no per-field database column, per-field nullability, per-field
  default, per-field foreign key, or per-field enum/CHECK constraint** for
  the overwhelming majority of fields. The database enforces none of
  this — `form_data` is `NOT NULL` as a whole JSONB blob; everything
  inside it is unconstrained at the database layer. Any "Required",
  "Allowed Values", or "Conditional Logic" behavior recorded in the Field
  Inventory is enforced only in `validateRNICA()` (frontend/application
  layer), not by the database schema.
- A **small, specific set of fields** are also synced out, on RNICA
  save/update, into separate relational tables that are shared with
  Facesheet and other modules. These are documented individually below
  under "Synced-Out Fields," with full table/column/type/nullable/
  default/FK/enum detail, because — unlike the rest — the database *does*
  enforce structure on them.

Given this, the per-section tables below record one row per section
(all fields in that section share the same Table/Column/Type/Nullable/
Default/FK/Enum pattern), followed by a full per-field breakout only for
the fields that have a genuinely different (synced-out) mapping. This
avoids ~450 rows that would otherwise all read
"`rnica_assessments.form_data` / JSONB / nullable / no default / no FK /
no enum" with no additional information — the exceptions are exactly
where the real database mapping detail is.

---

## 1. Primary table: `rnica_assessments`

Source: `backend/app/models/rnica_assessment.py`; created in
`backend/alembic/versions/521d501c6eea_consolidated_baseline.py` (lines
2561-2578); `tenant_id` added in
`backend/alembic/versions/l3m4n5o6p7q8_add_tenant_id_to_rnica_recert.py`.

| Column | Type | Nullable | Default | FK | Enum | Notes |
|---|---|---|---|---|---|---|
| `id` | UUID | No | `uuid.uuid4()` (app-side) | PK | — | |
| `patient_id` | UUID | No | — | `patients.id`, ON DELETE CASCADE | — | indexed |
| `visit_id` | UUID | Yes | — | `visits.id`, ON DELETE SET NULL | — | indexed |
| `tenant_id` | UUID | Yes | — | `tenants.id` | — | indexed; added post-baseline for defense-in-depth scoping |
| `assessment_type` | String(32) | No | `"RNICA"` | — | not DB-enforced | app sets `"RNICA"` on create (`visits.py:774`) |
| `status` | String(32) | No | `"DRAFT"` | — | not DB-enforced | values used in app: DRAFT/etc., not a DB CHECK constraint |
| `locked` | Boolean | No | `False` | — | — | |
| `form_data` | JSONB | No | `dict` (empty object, app-side) | — | — | **holds all Section 1-28 field data**, see below |
| `notes` | Text | Yes | — | — | — | |
| `locked_at` | DateTime(tz) | Yes | — | — | — | |
| `created_at` | DateTime(tz) | No | `datetime.utcnow()` (app-side) | — | — | |
| `updated_at` | DateTime(tz) | No | `datetime.utcnow()` (app-side), updates on write | — | — | |

Relationships: `patient` → `Patient` (backref `rnica_assessments`);
`visit` → `Visit` (backref `rnica_assessments`).

Used by: `backend/app/api/visits.py` — `POST /rnica/save`,
`GET /rnica/{assessment_id}`, `GET /rnica/by-patient/{patient_id}`,
`PUT /rnica/{assessment_id}`, `POST /rnica/{assessment_id}/lock`,
`GET /rnica/{assessment_id}/intelligence`; also read by
`backend/app/api/patients.py` (PPS/KPS/FAST/weight history query) and
`backend/app/services/dashboard_service.py`.

---

## 2. Per-section mapping (Sections 1-28)

Universal row for each section: unless a field is listed in the
"Synced-Out Fields" table (Section 3 below), every field in that section
maps to `rnica_assessments.form_data`, type JSONB, nullable (no DB
constraint), no DB default, no FK, no enum/CHECK constraint.

| Section | Field(s) | Table | Column (JSON path root) | Type | Nullable | Default | FK | Enum |
|---|---|---|---|---|---|---|---|---|
| 1 | Patient Demographics — all fields | `rnica_assessments` | `form_data->'demographics'` | JSONB | Yes | None | None | None |
| 2 | Vitals — all fields (incl. IV Assessment) | `rnica_assessments` | `form_data->'vitals'` | JSONB | Yes | None | None | None |
| 3 | Pain Assessment — all fields | `rnica_assessments` | `form_data->'pain'` | JSONB | Yes | None | None | None |
| 4 | Symptom Impact — all fields | `rnica_assessments` | `form_data->'symptomImpact'` | JSONB | Yes | None | None | None |
| 5 | Diagnoses — all fields | `rnica_assessments` | `form_data->'diagnoses'` | JSONB | Yes | None | None | None |
| 6 | Performance Status — all fields | `rnica_assessments` | `form_data->'performanceStatus'` | JSONB | Yes | None | None | None |
| 7 | Neurological — all fields (incl. Sleep/Rest) | `rnica_assessments` | `form_data->'neurological'` | JSONB | Yes | None | None | None |
| 8 | Cardiovascular — all fields | `rnica_assessments` | `form_data->'cardiovascular'` | JSONB | Yes | None | None | None |
| 9 | Respiratory — all fields (incl. Oxygen Therapy) | `rnica_assessments` | `form_data->'respiratory'` | JSONB | Yes | None | None | None |
| 10 | Infection — all fields | `rnica_assessments` | `form_data->'infection'` | JSONB | Yes | None | None | None |
| 11 | Gastrointestinal — all fields (incl. Feeding Tube, Ostomy) | `rnica_assessments` | `form_data->'gastrointestinal'` | JSONB | Yes | None | None | None |
| 12 | Nutrition — all fields (incl. Dentures) | `rnica_assessments` | `form_data->'nutrition'` | JSONB | Yes | None | None | None |
| 13 | Endocrine — all fields | `rnica_assessments` | `form_data->'endocrine'` | JSONB | Yes | None | None | None |
| 14 | Genitourinary — all fields (incl. Catheter, Reproductive) | `rnica_assessments` | `form_data->'genitourinary'` | JSONB | Yes | None | None | None |
| 15 | Musculoskeletal — all fields (incl. Fall History, Mobility, ADL) | `rnica_assessments` | `form_data->'musculoskeletal'` | JSONB | Yes | None | None | None |
| 16 | Skin / Wounds — all fields (incl. Braden) | `rnica_assessments` | `form_data->'skin'` | JSONB | Yes | None | None | None |
| 17 | Imminent Death — all fields | `rnica_assessments` | `form_data->'imminentDeath'` | JSONB | Yes | None | None | None |
| 18 | SFV — all fields (incl. Symptom Impact at SFV) | `rnica_assessments` | `form_data->'sfv'` | JSONB | Yes | None | None | None |
| 19 | Safety — all fields | `rnica_assessments` | `form_data->'safety'` | JSONB | Yes | None | None | None |
| 20 | Psychosocial — all fields | `rnica_assessments` | `form_data->'psychosocial'` | JSONB | Yes | None | None | None |
| 21 | Spiritual — all fields | `rnica_assessments` | `form_data->'spiritual'` | JSONB | Yes | None | None | None |
| 22 | Bereavement — all fields | `rnica_assessments` | `form_data->'bereavement'` | JSONB | Yes | None | None | None |
| 23 | Personal Care — all fields (incl. Aide Visit Preferences) | `rnica_assessments` | `form_data->'personalCare'` | JSONB | Yes | None | None | None |
| 24 | Teaching Needs — all fields | `rnica_assessments` | `form_data->'teachingNeeds'` | JSONB | Yes | None | None | None |
| 25 | Admissions Order — all fields (incl. HA Assignment, Initial POC/IDG, TO Verification) | `rnica_assessments` | `form_data->'admissionsOrder'` | JSONB | Yes | None | None | None |
| 26 | Hospice Orders Hub — all fields (incl. Med Reconciliation) | `rnica_assessments` | `form_data->'medications'` | JSONB | Yes | None | None | None | note: `formSection` for this nav key is `medications`, not `ordersHub` — see Field Inventory Section 26 |
| 27 | Referrals — all fields | `rnica_assessments` | `form_data->'referrals'` | JSONB | Yes | None | None | None |
| 28 | Finalization — all fields (incl. Response to Interventions, Supervisor Review) | `rnica_assessments` | `form_data->'finalization'` | JSONB | Yes | None | None | None |

---

## 3. Synced-Out Fields (write to relational tables in addition to `form_data`)

Source: `backend/app/api/visits.py`, functions `_sync_facesheet_from_rnica`
(lines 175-220) and `_sync_shared_records_from_rnica` (lines 293-421),
invoked from `save_rnica_assessment` (line 751) and
`update_rnica_assessment` (line 930). These run **in addition to** the
`form_data` JSONB write — the source field remains in `form_data` and is
also propagated to the tables below.

### 3.1 Diagnoses (Section 5)

| Section | Field | Table | Column | Type | Nullable | Default | FK | Enum | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 5 | `diagnoses.primaryDiagnosis.{icd10,description}` | `patient_diagnoses` | `icd10_code`, `diagnosis_description`, `display_name` | String | No (icd10_code, diagnosis_description); No (display_name) | — | `tenant_id`→`tenants.id`, `patient_id`→`patients.id` (CASCADE) | `diagnosis_type` = `PRIMARY` (enum `patient_diagnosis_type_enum`); `source` = `RN_ICA` (enum `patient_diagnosis_source_enum`); `status` enum `patient_diagnosis_status_enum` default `PROPOSED` | via `sync_official_primary_diagnosis()`, `diagnosis_sync_service.py`; unique partial index enforces one active PRIMARY per patient |
| 5 | `diagnoses.secondaryDiagnoses[]` | `patient_diagnoses` | `icd10_code`, `diagnosis_description`, `display_name` | String | No | — | same as above | `diagnosis_type` = `SECONDARY` | via `sync_secondary_and_comorbidity_diagnoses()` |
| 5 | `diagnoses.comorbidities[]` | `patient_diagnoses` | `icd10_code`, `diagnosis_description`, `display_name` | String | No | — | same as above | `diagnosis_type` = `COMORBIDITY` (assumed from function name; exact enum value not individually re-verified beyond `DiagnosisType` import) | via `sync_secondary_and_comorbidity_diagnoses()` |
| 5 | `diagnoses.primaryDiagnosis` / `secondaryDiagnoses[]` (flattened text mirror) | `patient_facesheets` | `primary_diagnosis` (String), `secondary_diagnoses` (Text) | String/Text | Yes | — | — | — | legacy free-text mirror via `_sync_facesheet_from_rnica`; independent of the `patient_diagnoses` sync above |

Migration reference (`patient_diagnoses`):
`backend/alembic/versions/521d501c6eea_consolidated_baseline.py:1376`.

### 3.2 Allergies (Section 10 — Infection)

| Section | Field | Table | Column | Type | Nullable | Default | FK | Enum | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 10 | `infection.allergies[]` | `patient_allergies` | `allergen_text` | String(255) | No | — | `patient_id`→`patients.id` (CASCADE) | `allergen_type` (DRUG/FOOD/ENVIRONMENTAL/OTHER, default `DRUG`); `severity` (MILD/MODERATE/SEVERE/ANAPHYLAXIS, nullable) | via `sync_allergies_from_source()` |
| 10 | `infection.allergies[]` (flattened text mirror) | `patient_facesheets` | `has_allergies` (Boolean), `allergies` (Text) | Boolean/Text | Yes | — | — | — | legacy free-text mirror via `_sync_facesheet_from_rnica` |

Migration reference (`patient_allergies`):
`backend/alembic/versions/6e4e89b3ed4b_add_patient_allergies.py`.

### 3.3 Code Status (Section 1 — Demographics → Advanced Care Planning)

| Section | Field | Table | Column | Type | Nullable | Default | FK | Enum | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `demographics.advancedCarePlanning.codeStatus` | `patient_code_statuses` | `code_status` | String(64) | No | — | `tenant_id`→`tenants.id`, `patient_id`→`patients.id` (CASCADE) | not a DB enum/CHECK — validated in app (`normalize_code_status()`) against FULL_CODE/DNR_DNI/COMFORT_MEASURES_ONLY/OTHER | via `set_current_code_status()`, `source="RN_ICA"`; append-only audit table — every change is a new row, `is_current` flips old row to false |
| 1 | (same field, extraction path note) | — | — | — | — | — | — | — | code reads `form_data.advancedCarePlanning.codeStatus` directly (`_extract_rnica_code_status`, `visits.py:238-241`) — **not** `form_data.demographics.advancedCarePlanning.codeStatus` as nested in the Field Inventory; this is a path-mismatch observation, recorded as-is, not corrected here |

Migration reference (`patient_code_statuses`):
`backend/alembic/versions/d1fdad4c35bf_add_patient_code_statuses.py`;
`tenant_id` added in
`backend/alembic/versions/e2a7b8c9d0f1_add_tenant_id_to_patient_code_statuses.py`.

### 3.4 Contacts / Decision-Makers (Section 1 — Demographics)

| Section | Field | Table | Column | Type | Nullable | Default | FK | Enum | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `demographics.pcg.{name,relationship,phone}` | `patient_contacts` | `name`, `relationship_to_patient`, `phone` | String | Yes | — | `tenant_id`→`tenants.id`, `patient_id`→`patients.id` (CASCADE, unique per patient+role) | `role` = `PRIMARY_CAREGIVER` (app-level constant, not a DB enum — column is `String(64)`) | via `set_patient_contact()`, `source="RN_ICA"`; one row per (patient, role), updated in place (not append-only) |
| 1 | `demographics.advancedCarePlanning.{poaName,poaPhone}` | `patient_contacts` | `name`, `phone` | String | Yes | — | same as above | `role` = `DPOA` | via `set_patient_contact()` |
| 1 | `demographics.advancedCarePlanning.decisionMaker` | `patient_contacts` | `name` | String | Yes | — | same as above | `role` = `DECISION_MAKER` | via `set_patient_contact()` |

Migration reference (`patient_contacts`):
`backend/alembic/versions/a1c2d3e4f5b6_add_patient_contacts.py`.

### 3.5 Level of Care (Section 25 — Admissions Order)

| Section | Field | Table | Column | Type | Nullable | Default | FK | Enum | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 25 | `admissionsOrder.levelOfCare.level` | `patient_facesheets` | `current_level_of_care` | String | Yes | — | — | not a DB enum — mapped via app-side `_RNICA_LOC_TO_FACESHEET_LABEL` dict (`visits.py:276-281`) | direct field assignment (no dedicated sync-service function; done inline in `_sync_shared_records_from_rnica`, `visits.py:397-412`) |

No migration-reference lookup performed for `patient_facesheets` (large,
pre-existing table; not created in a single identifiable RNICA-related
migration).

---

## Status

**Deliverable #2 (`SNS_RNICA_DATABASE_MAPPING_1.0`) complete** for all 28
sections: primary-table schema recorded, universal JSONB mapping rule
recorded per section, and all identified synced-out relational mappings
(Diagnoses, Allergies, Code Status, Contacts/Decision-Makers, Level of
Care) recorded field-by-field with table/column/type/nullable/default/
FK/enum detail.

No changes made to `SNS_RNICA_FIELD_INVENTORY_1.0`,
`SNS_RNICA_MASTER_MAP_1.0`, or `SNS_HOPE_CROSSWALK_1.0`. No code changes
are authorized by this document.

Next, per the stated sequence: Deliverable #3 —
`SNS_RNICA_API_MAPPING_1.0`, pending explicit direction to proceed.
