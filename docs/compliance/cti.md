# CTI (Certification of Terminal Illness) Compliance Runbook
SNS Hospice EMR

## Purpose
This document describes how Certifications of Terminal Illness (CTI) —
initial certification and recertification — are drafted, reviewed, signed,
and audited in SNS EMR to meet CMS Hospice Conditions of Participation
(42 CFR 418.22, 418.25) and California CDPH hospice requirements.

CTI is a **physician certification workflow**, strictly separate from the
Face-to-Face (F2F) **encounter** workflow (see `docs/compliance/f2f.md`,
Phase 3). Ability to perform/sign an F2F encounter never confers CTI
signing authority, and vice versa — the two are never combined or
inferred from one another.

---

## Certification Lifecycle (Phase 1, additive only)

Stored status literals are never renamed; a **display-label layer**
(`certification_service.label_for()` / `STATUS_LABELS`) presents
survey-facing terminology without changing the underlying value:

| Stored status       | Display label            |
|----------------------|---------------------------|
| DRAFT                 | Draft                     |
| PENDING_SIGNATURE     | CTI Pending Signature     |
| FINALIZED             | Signed                    |
| SUPERSEDED            | Superseded                |

```
DRAFT (physician narrative + LCD/clinical evidence captured)
  → PENDING_SIGNATURE (ready for physician review)
  → FINALIZED (physician-level signature — legally binding)
  → SUPERSEDED (automatically, when the next benefit period's cert is signed)
```

Any pre-existing "FINALIZED"-only record (no draft history) predating this
expansion remains fully valid and untouched.

---

## CTI Signing Authority (SNS final decision, additive/non-negotiable)

CTI is restricted to **physician-level certification roles only**, for
both Initial Certification and Recertification:

**Allowed:**
- Attending Physician
- Medical Director
- Medical Director Designee (aliases to Medical Director)
- Hospice Physician

**Never allowed:**
- Nurse Practitioner (NP)
- Physician Assistant (PA)
- RN
- LVN
- DPCS
- Administrator

This is enforced twice, independently:
1. **API gate** — `POST /certifications/{id}/sign` requires
   `require_roles(CTI_SIGNER_ROLES, allow_clinical_admin=False)`, so
   administrative rank (Administrator/DPCS) can never satisfy the gate via
   any "admin fallback" rule.
2. **Service-layer defense in depth** —
   `certification_service.is_authorized_cti_signer()` re-checks the role
   inside `sign_certification()` regardless of which endpoint/caller
   invoked it.

`signed_by_role` is **always** derived from the authenticated user's own
`user.role` — it is never accepted as a client-supplied request field. (The
pre-Phase-1 implementation accepted `signed_by_role` from the request
body and allowed Administrator in its role list — an Administrator account
could self-declare `"MD"` and finalize a certification with no prescribing/
certifying authority. This is fixed.)

A provider's ability to perform/sign an F2F encounter (e.g. a
hospice-employed NP) **never** implies CTI certification authority.

---

## Required Data Elements (Before Signature)

- `physician_narrative` — required, non-empty. CMS/LCD guidance requires
  **patient-specific evidence** supporting a prognosis of six months or
  less (clinical decline, functional status, comorbidities,
  disease-specific indicators) — conclusory statements alone are
  insufficient.
- `supporting_evidence` / `clinical_decline_indicators` — optional
  structured/free-text LCD evidence fields.
- Narrative/evidence may be edited while `DRAFT` or `PENDING_SIGNATURE`;
  once `FINALIZED`, the record is locked (`update_narrative()` rejects
  edits after signature).

---

## BP3+ Face-to-Face Gate

For the 3rd and later benefit periods, a certification **cannot** be
signed unless a completed F2F encounter task exists for that benefit
period (`recert_f2f_enforcement.require_f2f_completed_for_bp3_plus()`).
This re-validates at signature time, not just at submission.

## 15-Day Early-Signature Rule

A certification cannot be signed more than 15 days before its benefit
period's start date (preserved from the original implementation).

---

## Supersession Chaining

When a new certification is `FINALIZED`, the immediately-prior
`FINALIZED` certification for the same patient is automatically marked
`SUPERSEDED` (`superseded_by_id` / `superseded_at`), building a
continuous certification history per patient without manual bookkeeping.

---

## Immutable Status-History Audit Trail

Every transition — including the initial `DRAFT` creation — is recorded
as an append-only row in `certification_status_events` (from_status,
to_status, changed_by_user_id, changed_by_role, changed_at, reason,
automatic, evidence), retrievable via
`GET /certifications/{certification_id}/status-history`. This is in
addition to the generic `audit_log` table entry for the same event.

---

## Tenant Isolation

The `certifications` table previously had **no `tenant_id` column at
all** — a cross-tenant data-isolation gap on a compliance-critical
record predating this work. Phase 1 adds `tenant_id` (backfilled from
`patients.tenant_id`, `NOT NULL`), and every service-layer query
(`list_certifications`, `get_certification`, `sign_certification`, etc.)
is tenant-scoped.

---

## Dashboard Widgets

- `cti_due_missing` — task-based due/missing tracking (pre-existing,
  unchanged). Visible to agency-compliance roles + RN/Intake.
- `cti_pending_signature` — new, record-based: certifications in
  `DRAFT`/`PENDING_SIGNATURE`. Visible to CTI-signer roles (their own
  queue) plus Administrator/DPCS/Clinical Supervisor/Compliance/QA
  (monitor only — no signing capability implied by visibility).
- `cti_expiring` — new: `FINALIZED` certifications whose `expires_at` is
  within 15 days. Visible to CTI-signer roles + agency-compliance roles
  + RN.

These are independent, complementary signals (task due-date tracking vs.
certification-record lifecycle state), matching the Physician Orders
Phase 1 pattern.

---

## API Endpoints

| Method | Path                                              | Purpose                                  |
|--------|---------------------------------------------------|-------------------------------------------|
| GET    | `/certifications/patients/{patient_id}`            | List a patient's certifications           |
| GET    | `/certifications/{id}/status-history`              | Immutable audit trail                     |
| POST   | `/certifications/patients/{patient_id}/draft`      | Create DRAFT (narrative + evidence)       |
| PATCH  | `/certifications/{id}/narrative`                   | Edit narrative/evidence (pre-signature)   |
| POST   | `/certifications/{id}/submit`                      | DRAFT → PENDING_SIGNATURE                 |
| POST   | `/certifications/{id}/sign`                        | Physician-only signature → FINALIZED      |
| POST   | `/certifications/`                                 | Legacy one-shot create-and-sign           |
