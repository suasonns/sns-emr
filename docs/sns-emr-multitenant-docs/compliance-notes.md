# Hospice EMR Compliance Notes
**Multi‑Tenant Enterprise | Survey‑Defensible Controls**

---

## 1. Overview

This document summarizes compliance controls for SNS Hospice EMR as a **multi‑tenant enterprise platform** supporting HIPAA privacy/security and CMS Hospice Conditions of Participation (CoPs).

---

## 2. HIPAA Privacy & Minimum Necessary

The EMR shall:
- Restrict PHI access to authorized users only
- Enforce minimum necessary access by role and interface
- Record and retain access logs for PHI

---

## 3. Multi‑Tenant Isolation Controls (HIPAA‑Critical)

The EMR shall enforce tenant isolation via:
- `tenant_id` on all PHI/clinical records
- tenant‑scoped users (one tenant per user)
- tenant‑scoped authorization checks
- prevention of cross‑tenant queries by design

Optional defense‑in‑depth:
- PostgreSQL Row‑Level Security (RLS) policies

---

## 4. Role‑Based Access Control (Interface‑Scoped)

- Users are assigned roles based on job function
- Roles are scoped to an interface (Clinical EMR vs Admin Console vs Survey Access)
- Role grants are time‑bound (assigned/revoked timestamps)
- Authorization checks evaluate role validity **at the time of action**

---

## 5. Audit Logging (Immutable)

The EMR shall maintain immutable audit logs capturing:
- tenant_id
- user identity
- role snapshot
- interface snapshot
- action performed
- timestamp
- affected entity

Audit logs:
- are append‑only (no update/delete)
- are retained for the life of the record
- support survey and legal defensibility

---

## 6. Clinical Record Integrity (Legal Medical Record)

- Draft records may be edited (with audit)
- Finalized records are immutable
- Corrections occur via append‑only amendments
- Original content is preserved
- Amendments are time‑stamped and attributed

---

## 7. Surveyor / External Review Access

Surveyor accounts shall be:
- read‑only
- tenant‑scoped
- time‑limited
- fully audited

Surveyors cannot create, edit, delete, finalize, or amend records.

---

## 8. Data Retention

- Clinical records are retained per regulatory requirements and tenant policy
- Audit logs are retained for the life of the record
- Deletion of clinical records is restricted and controlled

---

## 9. Security Notes

- Server‑side authorization is mandatory (UI is not sufficient)
- Protect secrets/tokens; rotate and store in environment variables
- Enforce strong authentication and session controls
