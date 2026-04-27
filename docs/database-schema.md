# Hospice EMR Database Schema Design

## 1. Design Rules

The database schema follows these rules:

1. All tables use system-generated UUID primary keys
2. Medical Record Number (MRN) is a unique business identifier, not a primary key
3. Finalized clinical documentation is immutable
4. Amendments are stored as separate records
5. No clinical data is hard-deleted
6. All clinical actions are auditable

## 2. Users

Represents any person accessing the system.

Fields:
- id (UUID, primary key)
- email (unique)
- full_name
- role
- license_number (nullable)
- active
- created_at
- updated_at

Notes:
- Role values align with role-permissions.md
- Surveyor accounts are read-only by application logic

## 3. Patients

Represents hospice patients.

Fields:
- id (UUID, primary key)
- mrn (unique)
- full_name
- date_of_birth
- primary_diagnosis
- status (active, discharged, deceased)
- hospice_start_date
- hospice_end_date (nullable)
- created_at
- updated_at

Notes:
- MRN is displayed to users
- Internal ID is never exposed

## 4. Admissions

Represents hospice admission events.

Fields:
- id (UUID)
- patient_id (FK → patients.id)
- admission_date
- certifying_provider_id (FK → users.id)
- level_of_care
- created_at

## 5. Visits

Represents a single patient encounter.

Fields:
- id (UUID)
- patient_id (FK)
- provider_id (FK)
- visit_type
- visit_datetime
- status (draft, finalized)
- created_at
- finalized_at (nullable)

## 6. Clinical Notes

Represents clinical documentation for a visit.

Fields:
- id (UUID)
- visit_id (FK)
- author_id (FK)
- note_type
- content
- status (draft, finalized)
- created_at
- finalized_at

Rules:
- Draft notes may be edited
- Finalized notes may not be modified
``

## 7. Note Amendments

Represents corrections to finalized notes.

Fields:
- id (UUID)
- original_note_id (FK)
- amended_by (FK → users.id)
- amendment_reason
- amendment_content
- created_at

Rules:
- Original note content is preserved
- Amendments are append-only

## 8. Medications
``
## 9. Plans of Care

## 10. Audit Logs

Tracks all access and changes.

Fields:
- id (UUID)
- user_id
- action
- entity_type
- entity_id
- timestamp
- ip_address (nullable)

Rules:
- No updates
- No deletes
- Admin read-only access

