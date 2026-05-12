# SNS Hospice EMR Role & Permission Matrix
**Multi‑Tenant Enterprise | Interface‑Scoped RBAC**

---

## 1. Overview

This document defines **role‑based permissions** for the SNS Hospice EMR as a **multi‑tenant enterprise system**.

Key properties:
- Roles are **scoped to an Interface** (context)
- All access is **tenant‑scoped**
- “Minimum necessary” access is enforced
- Finalization is a legal signature event and is fully audited

**Permission verbs**
- View: read-only
- Create: create new record
- Edit (Draft): modify draft record
- Finalize: sign/lock record
- Amend: append correction to finalized record
- Admin: configure system

---

## 2. Interfaces

- **Clinical EMR**: clinical documentation and patient management
- **Billing Portal**: (post‑MVP) claims and revenue cycle
- **Survey Access**: read‑only reviewer portal
- **Admin Console**: tenant configuration and access management

---

## 3. Clinical EMR Interface Roles

### 3.1 Registered Nurse (RN) — Clinical EMR
- View assigned patients: Yes
- Create admissions: Yes
- Create visit notes: Yes
- Edit draft notes: Yes
- Finalize visit notes: Yes
- Amend finalized notes: Yes
- Manage medications: Yes
- Update Plan of Care (POC): Yes (within policy)
- View audit logs: No

### 3.2 Licensed Vocational Nurse (LVN) — Clinical EMR
- View assigned patients: Yes
- Create admissions: No
- Create visit notes: Yes
- Edit draft notes: Yes
- Finalize visit notes: Yes (if tenant policy allows)
- Amend finalized notes: Yes (with reason)
- Manage medications: View-only
- Update POC: No (unless explicitly granted)

### 3.3 Nurse Practitioner (NP) — Clinical EMR
- View assigned patients: Yes
- Perform face-to-face documentation: Yes
- Create/Finalize NP notes: Yes
- Eligibility evaluation support: Yes
- Orders (if implemented): Yes (provider scope)
- Amend finalized notes: Yes

### 3.4 Physician / Medical Director (MD) — Clinical EMR
- View patient records: Yes
- Certify eligibility: Yes
- Sign provider documentation/orders (if implemented): Yes
- Amend finalized notes: Yes

### 3.5 Social Worker (SW) — Clinical EMR
- View assigned patients: Yes
- Create psychosocial assessments/notes: Yes
- Edit drafts: Yes
- Finalize SW notes: Yes
- View medications: No (except minimal necessary)

### 3.6 Chaplain — Clinical EMR
- View assigned patients: Yes (limited)
- Create spiritual care notes: Yes
- Finalize chaplain notes: Yes

### 3.7 Aide (CHHA) — Clinical EMR
- View assigned patients: Yes (care plan elements only)
- Create aide visit notes: Yes
- Finalize aide notes: Yes
- View meds/orders: No

### 3.8 Volunteer — Clinical EMR
- View assigned patient demographics: Minimal
- Create volunteer activity note: Yes (non‑clinical)
- View clinical notes: No

---

## 4. Survey Access Interface Roles

### 4.1 Surveyor — Survey Access (Read‑Only)
- View patient record (tenant‑scoped): Yes
- View finalized notes/POC/IDG evidence: Yes
- Create/Edit/Finalize/Amend: No
- Export: Optional (if policy allows) and always audited

---

## 5. Admin Console Interface Roles

### 5.1 Tenant Admin — Admin Console
- Manage users: Yes
- Assign/revoke roles (time‑bound grants): Yes
- Configure tenant settings: Yes
- View audit logs: Yes (tenant‑scoped)

### 5.2 QA / Compliance — Admin Console
- View patient record for QA: Yes (tenant‑scoped)
- View audit logs: Yes (tenant‑scoped)
- Create/Edit clinical documentation: No

---

## 6. Cross‑Cutting Security Rules

- All permissions are constrained by `tenant_id`.
- Authorization is evaluated using role assignment history at action time.
- Finalize/Amend events must record role/interface snapshots.
- Surveyor access is time‑limited and logged.
