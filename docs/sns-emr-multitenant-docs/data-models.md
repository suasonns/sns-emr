# SNS Hospice EMR Data Models
**Multi‑Tenant Enterprise Logical Model**

---

## 1. Overview

This document defines the core logical data entities for the SNS Hospice EMR as a **multi‑tenant enterprise system**. Each tenant represents a legally distinct hospice agency. Clinical records are legal documents; finalized records are immutable; all access and changes are auditable.

Key goals:
- Strict tenant isolation (HIPAA)
- Interface‑scoped RBAC
- Audit‑ready attribution (user + role + interface + time)
- Hospice workflow fidelity (admission → visits → POC → IDG → discharge/death)

---

## 2. Core Concepts (Canonical)

- **Tenant**: a hospice/agency with isolated data and users.
- **Interface**: a named UI surface (Clinical EMR, Billing, Survey Access, Admin Console).
- **Role**: a permission bundle **within one interface**.
- **User**: an individual person belonging to exactly one tenant.
- **Assignment**: a time‑bound mapping of User + Interface + Role.

---

## 3. Core Entities

### 3.1 Tenant
Represents a legally distinct hospice agency.

**Key attributes**
- `id` (UUID)
- `legal_name`
- `display_name`
- `status` (ACTIVE, SUSPENDED)
- `created_at`, `updated_at`

---

### 3.2 Interface
Represents a named product surface.

**Key attributes**
- `id` (UUID)
- `name` (CLINICAL_EMR, BILLING_PORTAL, SURVEY_ACCESS, ADMIN_CONSOLE)
- `created_at`

---

### 3.3 Role
Represents a permission set **scoped to an interface**.

**Key attributes**
- `id` (UUID)
- `interface_id` (FK → Interface)
- `name` (RN, LVN, NP, MD, SW, CHAPLAIN, AIDE, VOLUNTEER, BILLING_ADMIN, QA, SURVEYOR, ADMIN)
- `description`

---

### 3.4 User
Represents an individual person who belongs to exactly one tenant.

**Key attributes**
- `id` (UUID)
- `tenant_id` (FK → Tenant)
- `email` (unique within tenant)
- `full_name`
- `credential_type` (optional; RN/LVN/MD/etc.)
- `license_number` (optional)
- `status` (ACTIVE, INACTIVE)
- `created_at`, `updated_at`

**Rule**: Users are tenant‑scoped; cross‑tenant users are not permitted.

---

### 3.5 User Interface Role Assignment (Keystone)
Represents a time‑bound authorization grant.

**Key attributes**
- `id` (UUID)
- `tenant_id` (FK → Tenant)
- `user_id` (FK → User)
- `interface_id` (FK → Interface)
- `role_id` (FK → Role)
- `assigned_at`
- `revoked_at` (nullable)
- `assigned_by_user_id` (nullable)

**Rules**
- A role is only valid inside its interface.
- Authorization checks are evaluated using `assigned_at`/`revoked_at` against the action timestamp.
- Grants are tenant‑scoped.

---

## 4. Clinical Domain Entities (Tenant‑Scoped)

**All clinical entities include**:
- `tenant_id`
- `created_at`, `created_by_user_id`
- `updated_at`, `updated_by_user_id` (for drafts)

### 4.1 Patient
- `id` (UUID)
- `tenant_id`
- `mrn` (unique within tenant)
- demographics (name, DOB)
- clinical (primary_diagnosis)
- `status` (ACTIVE, DISCHARGED, DECEASED)
- `hospice_start_date`, `hospice_end_date`

### 4.2 Admission
- `id`, `tenant_id`
- `patient_id`
- `admission_date`
- `certifying_provider_user_id`
- `level_of_care`

### 4.3 Visit
- `id`, `tenant_id`
- `patient_id`
- `provider_user_id`
- `visit_type` (RN/LVN/NP/MD/SW/CHAPLAIN/AIDE/VOLUNTEER)
- `visit_datetime`
- `status` (DRAFT, FINALIZED)
- finalization metadata:
  - `finalized_at`
  - `finalized_by_user_id`
  - `finalized_role_id` (snapshot)
  - `finalized_interface_id` (snapshot)

### 4.4 Clinical Note
- `id`, `tenant_id`
- `visit_id`
- `author_user_id`
- `note_type`
- `content`
- `status` (DRAFT, FINALIZED)
- finalization metadata (same snapshot pattern as Visit)

### 4.5 Note Amendment (Append‑Only)
- `id`, `tenant_id`
- `original_note_id`
- `amended_by_user_id`
- `amended_role_id` (snapshot)
- `amended_interface_id` (snapshot)
- `amendment_reason`
- `amendment_content`
- `created_at`

### 4.6 Medication
- `id`, `tenant_id`, `patient_id`
- `name`, `dose`, `route`
- `start_date`, `end_date` (nullable)

### 4.7 Plan of Care (POC)
- `id`, `tenant_id`, `patient_id`
- `effective_date`
- `goals`, `interventions`
- `review_date`
- change attribution snapshots for finalized POC updates

### 4.8 IDG Review (Enterprise‑Ready)
- `id`, `tenant_id`, `patient_id`
- `meeting_date`
- participant evidence (who contributed, roles)
- outcome / changes to POC

---

## 5. Audit & Access Evidence Entities

### 5.1 Audit Log (Immutable)
Captures security and clinical actions.

**Key attributes**
- `id` (UUID)
- `tenant_id`
- `user_id`
- `role_id` (snapshot)
- `interface_id` (snapshot)
- `action` (VIEW, CREATE, UPDATE_DRAFT, FINALIZE, AMEND, EXPORT)
- `entity_type`
- `entity_id`
- `occurred_at`
- `ip_address` (nullable)

**Rules**
- Append‑only; no updates/deletes.
- Retained for life of the record.

---

## 6. Data Integrity Rules (Logical)

- Finalized records are immutable.
- Corrections occur through amendments.
- MRN is unique within tenant, never a primary key.
- Authorization must be evaluated at action time using assignment history.

---

## 7. Out of Scope

- Claims/billing submission logic
- External integrations (pharmacy, labs)
- Mobile apps
