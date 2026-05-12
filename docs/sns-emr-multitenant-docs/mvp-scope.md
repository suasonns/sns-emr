# Hospice EMR MVP Scope
**Updated for Multi‑Tenant Enterprise Platform**

---

## 1. Purpose

This document defines the MVP scope for SNS Hospice EMR while reflecting the **current enterprise direction**: multi‑tenant, tenant‑isolated, compliance‑first clinical documentation.

---

## 2. Included Features (MVP)

### 2.1 Enterprise Foundations
- Multi‑tenant support (tenant entity)
- Tenant‑scoped users (one tenant per user)
- Interface‑scoped RBAC (Clinical EMR + Admin Console + Survey Access)
- Time‑bound role assignments (grant/revoke)
- Immutable audit logging with role/interface snapshots

### 2.2 User Management
- Secure user login
- Tenant‑scoped user provisioning
- Role assignment per interface

### 2.3 Patient Management
- Patient demographics
- MRN unique within tenant
- Patient status (active, discharged, deceased)

### 2.4 Hospice Admission
- Admission documentation
- Eligibility certification tracking (evidence capture)

### 2.5 Clinical Visits
- RN and LVN visits
- NP and MD visits (documentation)
- Discipline‑specific visit notes

### 2.6 Clinical Documentation
- Draft vs finalized notes
- Finalization locks record and captures signer metadata (user + role + interface + timestamp)
- Amendments to finalized records (append‑only)

### 2.7 Medication Management
- Active medication list
- Medication history

---

## 3. Excluded Features (Post‑MVP)

- Billing and claims submission
- Medicare electronic submissions
- Pharmacy integrations
- Laboratory integrations
- Scheduling automation
- Mobile apps
- Reporting dashboards (beyond essential exports)

---

## 4. Success Criteria

MVP is successful if:
- Core hospice workflows complete end‑to‑end per tenant
- Tenant isolation is provable (no cross‑tenant access)
- Documentation is immutable after finalization
- Amendments preserve original content
- Audit logs support survey and legal defensibility
