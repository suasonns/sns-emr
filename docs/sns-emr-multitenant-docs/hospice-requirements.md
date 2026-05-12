# Hospice EMR Requirements
**Multi‑Tenant Enterprise Requirements (Compliance‑First)**

---

## 1. Overview

The SNS Hospice EMR must support hospice clinical documentation, patient management, interdisciplinary workflows, and compliance reporting within a **multi‑tenant enterprise platform**. Each tenant is a distinct hospice agency with strict HIPAA‑aligned isolation.

---

## 2. Enterprise Scope

The system shall support:
- Multiple tenants (agencies) within a single deployment
- Tenant‑isolated data storage and access control
- Interface‑scoped role‑based access control (RBAC)
- Audit logging sufficient for surveys and legal defensibility

---

## 3. Tenancy & Data Isolation (HIPAA‑Critical)

The EMR shall:
- Assign every user to exactly one tenant
- Require `tenant_id` on all PHI/clinical records
- Prevent cross‑tenant reads/writes by design
- Log all access to patient records (tenant‑scoped)

---

## 4. Interfaces

The system shall support named interfaces:
- Clinical EMR
- Admin Console
- Survey Access (read‑only)
- Billing Portal (post‑MVP)

---

## 5. Role‑Based Access Control (RBAC)

The system shall:
- Assign roles within an interface (role is not global)
- Support time‑bound grants (assigned/revoked timestamps)
- Enforce minimum necessary access
- Support read‑only, time‑limited surveyor access

---

## 6. User Roles (Clinical EMR)

The system shall support at minimum:
- RN
- LVN
- NP
- Physician / Medical Director
- CHHA (Aide)
- Social Worker
- Chaplain
- Volunteer

The system shall support administrative roles:
- Tenant Admin (Admin Console)
- QA/Compliance (Admin Console)
- Surveyor (Survey Access)

---

## 7. Patient Lifecycle

The EMR shall support:
- Referral/intake → Admission
- Ongoing interdisciplinary visits
- Plan of Care (POC) creation and review
- IDG review documentation
- Discharge/transfer/death

Each stage shall be time‑stamped, tenant‑scoped, and attributed to a user.

---

## 8. Clinical Documentation Rules

The system shall allow authorized clinicians to:
- Create notes and visits (draft)
- Edit drafts prior to finalization
- Finalize notes/visits with immutable signer metadata
- View historical notes chronologically

Once finalized:
- Records shall not be deleted
- Corrections shall occur through amendments
- Original content must remain preserved

---

## 9. Medication Management

The EMR shall support:
- Active medication list
- Medication history
- Medication change documentation

The system does not initially manage dispensing or pharmacy integrations.

---

## 10. Audit and Legal Record Requirements

The EMR shall:
- Record who created/modified/finalized/amended a record
- Capture role + interface snapshots at signature events
- Maintain immutable audit logs for access and changes
- Protect audit logs from modification

Clinical documentation is a legal medical record.

---

## 11. Out of Scope (Initial)

- Claims/billing submission
- Medicare electronic submissions
- External pharmacy/labs integrations
- Mobile apps
- AI clinical decision support
