# Hospice EMR Role & Permission Matrix

## 1. Overview

This document defines role-based permissions for the hospice EMR system.

Permissions are designed to:
- Support real hospice workflows
- Protect patient health information (PHI)
- Enforce compliance with HIPAA and hospice regulations
- Ensure accountability through auditability

---

## 2. Permission Definitions

- View: Read-only access to records
- Create: Create new records or notes
- Edit (Draft): Modify records prior to finalization
- Finalize: Sign and lock clinical documentation
- Amend: Add corrections to finalized records
- Admin: System-level configuration

---

## 3. Role Permissions

### 3.1 Registered Nurse (RN)

- View assigned patients: Yes
- Create admissions: Yes
- Create visit notes: Yes
- Edit draft notes: Yes
- Finalize visit notes: Yes
- Amend finalized notes: Yes
- Manage medications: Yes
