# SNS Hospice EMR Database Schema Design
**Multi‑Tenant Enterprise (PostgreSQL + Alembic)**

---

## 1. Design Rules (Non‑Negotiable)

1. **All tables use UUID primary keys.**
2. **Every PHI/clinical table includes `tenant_id` (FK → tenants.id).**
3. **No hard deletes for clinical data.** Use soft-delete only when explicitly allowed for non‑clinical reference data.
4. **Finalized documentation is immutable.** Changes require append‑only amendments.
5. **Audit logs are append‑only** (no update/delete).
6. **Forward‑only migrations** (Alembic). Never rewrite migration history.
7. **Roles are interface‑scoped**; permissions are granted by time‑bound assignments.

---

## 2. Core Multi‑Tenant Tables

### 2.1 tenants
- `id` UUID PK
- `legal_name` TEXT
- `display_name` TEXT
- `status` TEXT (ACTIVE/SUSPENDED)
- `created_at` TIMESTAMPTZ
- `updated_at` TIMESTAMPTZ

### 2.2 interfaces
- `id` UUID PK
- `name` TEXT UNIQUE (CLINICAL_EMR, BILLING_PORTAL, SURVEY_ACCESS, ADMIN_CONSOLE)
- `created_at` TIMESTAMPTZ

### 2.3 roles
- `id` UUID PK
- `interface_id` UUID FK → interfaces.id
- `name` TEXT
- `description` TEXT
- UNIQUE(`interface_id`, `name`)

### 2.4 users
- `id` UUID PK
- `tenant_id` UUID FK → tenants.id
- `email` TEXT
- `full_name` TEXT
- `credential_type` TEXT NULL
- `license_number` TEXT NULL
- `status` TEXT (ACTIVE/INACTIVE)
- `created_at` TIMESTAMPTZ
- `updated_at` TIMESTAMPTZ
- UNIQUE(`tenant_id`, `email`)

### 2.5 user_interface_roles (time‑bound grants)
- `id` UUID PK
- `tenant_id` UUID FK → tenants.id
- `user_id` UUID FK → users.id
- `interface_id` UUID FK → interfaces.id
- `role_id` UUID FK → roles.id
- `assigned_at` TIMESTAMPTZ
- `revoked_at` TIMESTAMPTZ NULL
- `assigned_by_user_id` UUID NULL FK → users.id

**Indexes**
- (`tenant_id`, `user_id`)
- (`tenant_id`, `interface_id`, `role_id`)
- (`user_id`, `interface_id`, `assigned_at`)

---

## 3. Clinical Tables (Tenant‑Scoped)

### 3.1 patients
- `id` UUID PK
- `tenant_id` UUID FK
- `mrn` TEXT
- `full_name` TEXT
- `date_of_birth` DATE
- `primary_diagnosis` TEXT
- `status` TEXT (ACTIVE/DISCHARGED/DECEASED)
- `hospice_start_date` DATE
- `hospice_end_date` DATE NULL
- audit fields: `created_at`, `created_by_user_id`, `updated_at`, `updated_by_user_id`
- UNIQUE(`tenant_id`, `mrn`)

### 3.2 admissions
- `id` UUID PK
- `tenant_id` UUID FK
- `patient_id` UUID FK → patients.id
- `admission_date` DATE
- `certifying_provider_user_id` UUID FK → users.id
- `level_of_care` TEXT
- `created_at` TIMESTAMPTZ
- `created_by_user_id` UUID FK → users.id

### 3.3 visits
- `id` UUID PK
- `tenant_id` UUID FK
- `patient_id` UUID FK
- `provider_user_id` UUID FK → users.id
- `visit_type` TEXT (normalized uppercase at API layer)
- `visit_datetime` TIMESTAMPTZ
- `status` TEXT (DRAFT/FINALIZED)
- `created_at` TIMESTAMPTZ
- `created_by_user_id` UUID
- finalization snapshots:
  - `finalized_at` TIMESTAMPTZ NULL
  - `finalized_by_user_id` UUID NULL
  - `finalized_role_id` UUID NULL
  - `finalized_interface_id` UUID NULL

### 3.4 clinical_notes
- `id` UUID PK
- `tenant_id` UUID FK
- `visit_id` UUID FK → visits.id
- `author_user_id` UUID FK → users.id
- `note_type` TEXT
- `content` TEXT
- `status` TEXT (DRAFT/FINALIZED)
- `created_at` TIMESTAMPTZ
- `created_by_user_id` UUID
- `updated_at` TIMESTAMPTZ NULL
- `updated_by_user_id` UUID NULL
- finalization snapshots:
  - `finalized_at` TIMESTAMPTZ NULL
  - `finalized_by_user_id` UUID NULL
  - `finalized_role_id` UUID NULL
  - `finalized_interface_id` UUID NULL

### 3.5 note_amendments (append‑only)
- `id` UUID PK
- `tenant_id` UUID FK
- `original_note_id` UUID FK → clinical_notes.id
- `amended_by_user_id` UUID FK → users.id
- `amended_role_id` UUID
- `amended_interface_id` UUID
- `amendment_reason` TEXT
- `amendment_content` TEXT
- `created_at` TIMESTAMPTZ

### 3.6 medications
- `id` UUID PK
- `tenant_id` UUID FK
- `patient_id` UUID FK
- `name` TEXT
- `dose` TEXT
- `route` TEXT
- `start_date` DATE
- `end_date` DATE NULL
- `created_at` TIMESTAMPTZ

### 3.7 plans_of_care
- `id` UUID PK
- `tenant_id` UUID FK
- `patient_id` UUID FK
- `effective_date` DATE
- `goals` TEXT
- `interventions` TEXT
- `review_date` DATE
- finalization snapshots for approved POC versions (recommended)

### 3.8 idg_reviews (recommended)
- `id` UUID PK
- `tenant_id` UUID FK
- `patient_id` UUID FK
- `meeting_date` DATE
- `summary` TEXT
- `created_at` TIMESTAMPTZ

---

## 4. Audit Logs (Immutable)

### 4.1 audit_logs
- `id` UUID PK
- `tenant_id` UUID FK
- `user_id` UUID FK
- `role_id` UUID (snapshot)
- `interface_id` UUID (snapshot)
- `action` TEXT
- `entity_type` TEXT
- `entity_id` UUID
- `occurred_at` TIMESTAMPTZ
- `ip_address` TEXT NULL

**Rules**
- No UPDATE
- No DELETE
- Admin read access only

---

## 5. Tenant Enforcement Options

### Option A (Application‑Scoped)
All queries include `tenant_id` in filters. Recommended for MVP/early enterprise.

### Option B (Database Row‑Level Security)
Enable PostgreSQL RLS policies keyed by tenant context for defense‑in‑depth.

---

## 6. Verification Queries (DB Sanity Checks)

Use these to verify tenant isolation:

- Confirm tenant_id exists on PHI tables.
- Confirm MRN uniqueness per tenant.
- Confirm audit logs capture role/interface snapshots.

---

## 7. Notes

- Normalize `visit_type` to uppercase in API layer.
- Use forward‑only Alembic migrations.
- Never rely on UI for authorization; enforce server‑side.
