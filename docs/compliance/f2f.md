# F2F (Face-to-Face Encounter) Compliance Runbook
SNS Hospice EMR

## Purpose
This document describes how Face-to-Face (F2F) encounters are performed,
finalized, and audited in SNS EMR to meet CMS Hospice Conditions of
Participation (42 CFR 418.22(a)(4)) and California CDPH hospice
requirements for recertification support.

F2F is a separate **encounter workflow**, strictly independent from the
CTI **certification** workflow (see `docs/compliance/cti.md`, Phase 2).
Ability to perform/sign an F2F encounter never confers CTI certification
authority, and vice versa — the two are never combined or inferred from
one another. The F2F encounter note is **supporting evidence** for
physician recertification; it is never itself the certification.

---

## F2F Lifecycle (Phase 1, additive only)

Stored status literals are never renamed; a **display-label layer**
(`f2f_service.label_for()` / `STATUS_LABELS`) presents survey-facing
terminology without changing the underlying value:

| Stored status | Display label |
|----------------|----------------|
| DRAFT           | Draft          |
| FINALIZED       | Finalized      |

```
DRAFT (structured clinical findings + narrative captured by the performer)
  → FINALIZED (performer signature, or performer + physician attestation
    when performed by an NP/PA)
```

Any pre-existing "FINALIZED"-only record predating this expansion remains
fully valid and untouched.

---

## F2F Performer/Signer Authority (SNS decision, CMS/CDPH-aligned)

SNS follows current CMS/CDPH requirements and is not stricter than
CMS/CDPH absent a documented regulatory basis, and never permits what
CMS/CDPH prohibits.

**Allowed F2F performers:**
- Attending Physician
- Hospice Physician
- Medical Director
- Medical Director Designee (aliases to Medical Director)
- Nurse Practitioner (NP) — hospice-employed or contracted
- Physician Assistant (PA) — hospice-employed or contracted

**Never allowed:**
- RN
- LVN
- DPCS
- Administrator

This is enforced at the API layer: `POST /f2f/` and
`POST /f2f/{id}/finalize` both require
`require_roles(F2F_PERFORMER_ROLES, allow_clinical_admin=False)`, so
administrative rank (Administrator/DPCS) can never satisfy the gate via
any "admin fallback" rule. `performed_by_role`/`finalized_by_role` are
**always** derived from the authenticated user's own `user.role` — never
accepted as a client-supplied request field.

**F2F authority never grants CTI authority.** An NP or PA who
performs/signs an F2F gains **zero** CTI certification authority — see
`certification_service.is_authorized_cti_signer()`, which independently
excludes NP/PA regardless of F2F performer status.

---

## NP/PA-Performed F2F Requires Physician Attestation

When the encounter's `performed_by_role` is `NP` or `PA`, finalization
additionally requires a physician-level attestation captured on the
encounter (`attesting_provider_user_id` / `attested_at` /
`attestation_summary`). The attesting role must be one of
`F2F_PHYSICIAN_ATTESTOR_ROLES` (Medical Director, Attending Physician,
Hospice Physician) — **Administrator/DPCS may never satisfy this gate**,
since administrative rank is never clinical attestation authority.

---

## Clinical Narrative / LCD Support

The F2F's structured clinical findings and narrative may be documented
by RN, NP, PA, or Physician (same principle as CTI's narrative
contribution rule) — but for F2F specifically, only performer-tier
roles (`F2F_PERFORMER_ROLES`) may create the draft or finalize it, since
the encounter record itself attests "I performed this encounter."

---

## Required Data Elements (Before Finalization)

- At least one functional/disease scoring system (KPS, PPS, FAST, or
  NYHA class).
- ADL dependency level.
- At least one objective clinical decline indicator (weight loss,
  hospitalizations, oxygen requirement change, bedbound status, oral
  intake decline, or dysphagia).
- An individualized narrative summary (auto-generated from structured
  findings when not separately authored) of sufficient length to support
  an ADR (Additional Documentation Request) review.

---

## F2F Timing Window (BP3+)

For the 3rd and later benefit periods, the F2F `encounter_date` must fall
within 30 days prior to the benefit period's start date
(`recert_f2f_enforcement.validate_f2f_window()`). This is re-validated
both at draft creation and again at finalization.

---

## Immutable Status-History Audit Trail

Every transition — including the initial `DRAFT` creation — is recorded
as an append-only row in `f2f_encounter_status_events` (from_status,
to_status, changed_by_user_id, changed_by_role, changed_at, reason,
automatic, evidence), retrievable via
`GET /f2f/{f2f_id}/status-history`. This is in addition to the generic
`audit_log` table entry for the same event.

---

## Tenant Isolation

The `f2f_encounters` table previously had **no `tenant_id` column at
all** — the same class of cross-tenant data-isolation gap found in
`certifications` before the CTI fix. Phase 1 adds `tenant_id` (backfilled
from `patients.tenant_id`, `NOT NULL`), and every service-layer query
(`list_f2f_encounters`, `get_f2f_encounter`, `create_f2f`,
`finalize_f2f`) is tenant-scoped. The pre-existing `F2FEncounter` query in
`patient_charts.py` is now tenant-scoped as well.

---

## Dashboard Widgets

- `f2f_due_missing` — task-based due/missing tracking (pre-existing,
  unchanged). Visible to agency-compliance roles + RN.

---

## API Endpoints

| Method | Path                          | Purpose                                        |
|--------|-------------------------------|--------------------------------------------------|
| GET    | `/f2f/patients/{patient_id}`  | List a patient's F2F encounters                  |
| GET    | `/f2f/{id}/status-history`    | Immutable audit trail                            |
| POST   | `/f2f/`                       | Create DRAFT (performer-only, own encounter)     |
| POST   | `/f2f/{id}/finalize`          | Performer-tier finalize → FINALIZED (physician attestation required if NP/PA-performed) |
