# SNS Assessment Lifecycle Validation

**Document type:** Analysis / validation artifact. **NOT an
implementation specification.** No code tasks, no schema changes, no
architecture recommendations are made by this document.

**Status:** DISCOVERY ONLY. CODE: NOT AUTHORIZED. SCHEMA: NOT AUTHORIZED.

---

## Current Repository Evidence

### Can multiple Initial Comprehensive Assessments exist for one patient?

**Yes, across admissions; no, within a single admission** — directly
documented in the model itself:

```python
# backend/app/models/rnica_assessment.py:16-22
# Scopes this assessment to the admission episode it belongs to. The RN
# Initial Comprehensive Assessment (assessment_type == "RNICA") is only
# ever performed once per admission -- this column is what lets the
# backend enforce that (see _get_current_admission_for_patient /
# save_rnica_assessment in app/api/visits.py) while still allowing a
# brand-new one after a discharge + re-admission (new Admission row).
admission_id = Column(UUID(as_uuid=True), ForeignKey("admissions.id", ondelete="SET NULL"), nullable=True, index=True)
```

The one-per-admission rule is enforced in **application code**
(`_get_current_admission_for_patient` / `save_rnica_assessment` in
`backend/app/api/visits.py`), not by a database `UniqueConstraint` on
`(patient_id, admission_id, assessment_type)` — this document did not
locate such a constraint in this pass (open item below).

`RnicaAssessment.assessment_type` defaults to `"RNICA"` (the Initial
Comprehensive type) and is also used for other types on the same table:
`"RN_RECERT"` / `"RECERT"` / an "update assessment" type referenced in
`api/visits.py` as `RNICA_UPDATE_TYPE`. All three (initial, update,
recert) share the same `rnica_assessments` table, distinguished only by
`assessment_type` plus `admission_id`/`visit_id` scoping — there is no
separate table per assessment type.

### Update Assessment

`api/visits.py` defines `RNICA_UPDATE_TYPE` alongside
`RNICA_ADMISSION_TYPE` and `RNICA_RECERT_TYPE` (`visits.py:111,141`) —
queries filter `RnicaAssessment.assessment_type ==
normalized_assessment_type` (`visits.py:1156,1196`). This is a real,
implemented, distinct assessment type on the same row-family as the
Initial Comprehensive Assessment.

### Recertification Assessment

A legacy/parallel model also exists: `RNRecertAssessment`
(`backend/app/models/rn_recert_assessment.py:38`,
`form_type = Column(String(50), ..., default="RECERT")`), queried
separately from `RnicaAssessment` in
`services/assessment_history_service.py:248`
(`legacy_rn_recert_query = db.query(RNRecertAssessment)...`) — i.e.,
recertification assessments currently have **two** code paths: newer
rows via `RnicaAssessment(assessment_type="RECERT"/"RN_RECERT")` and an
older, separately-modeled `RNRecertAssessment` table, both still
queried (`assessment_history_service.py:244-255` queries both
`RnicaAssessment` and `RNRecertAssessment` plus `MswIcaAssessment` and
`ScicaAssessment` side by side when building patient assessment
history).

Recertification is also tied to `BenefitPeriod`
(`backend/app/models/benefit_period.py`): `benefit_type` enum
(`INITIAL`/`RECERT`), `UniqueConstraint(tenant_id, patient_id,
benefit_type, start_date)` — this **is** a real DB-level uniqueness
constraint, scoped to benefit periods, not to assessments directly.
`Certification.benefit_period_id` FK ties CTI/recert certification
directly to a specific benefit period.

### General `Assessment` model (separate from RNICA)

`backend/app/models/assessment.py` has its own, broader
`discipline`/`assessment_type` string fields and its own `status`
(default `DRAFT`)/`signed_at`/`signed_by` — this model is **not** the
same table as `RnicaAssessment`, and no evidence was found in this pass
of a singleton/one-per-admission rule enforced for it the way RNICA has
one. **NOT VERIFIED** either way for this model specifically.

## Observed Behavior

| Assessment family | Table | Singleton rule | Enforcement mechanism |
|---|---|---|---|
| RNICA Initial Comprehensive | `rnica_assessments` (`assessment_type="RNICA"`) | One per admission episode | Application code (`visits.py`), not a DB constraint |
| RNICA Update | `rnica_assessments` (`assessment_type=RNICA_UPDATE_TYPE`) | Not evidenced as singleton | — |
| RNICA Recert (current) | `rnica_assessments` (`assessment_type="RECERT"/"RN_RECERT"`) | Not evidenced as singleton | — |
| RN Recert (legacy) | `rn_recert_assessments` (`RNRecertAssessment`) | Not evidenced | Separate legacy table, still queried |
| Benefit Period | `benefit_periods` | One per `(tenant, patient, benefit_type, start_date)` | **DB-level** `UniqueConstraint` |
| General `Assessment` | `assessments` | Not evidenced | — |
| Body Systems | `body_systems_assessments` | One *open* (non-signed) at a time per patient | Application code only (`_get_or_create_current_assessment`, `body_systems.py:90-116`); no admission/episode scoping found (unlike RNICA's `admission_id`) |

## Expected SNS Workflow

Not asserted by this document — this is the one open product question
the requesting instruction poses directly ("Should they?"). Recorded
here only as an open decision, not answered.

## Validation Questions

1. **Can multiple Initial Comprehensive Assessments exist?** Yes, one
   per admission episode (by application-code convention); at most one
   per open admission.
2. **Should they?** Not answered by this document — product question.
3. **What is current behavior?** One `RnicaAssessment(assessment_type="RNICA")`
   permitted per `admission_id`, enforced in `api/visits.py`, not by a
   schema constraint. Body Systems has a looser rule: one *open*
   (non-signed) `BodySystemsAssessment` per patient, with no
   admission/episode scoping at all (different from RNICA's model).
4. **What is intended behavior?** Not established by repository
   evidence; no design document was found defining Body Systems'
   intended admission/episode scoping (if any).

## Open Decisions

1. Should the one-per-admission RNICA rule be enforced at the database
   level (`UniqueConstraint`) in addition to application code?
2. Should Body Systems adopt the same admission-episode scoping RNICA
   uses, rather than its current patient-only, status-only scoping?
3. Should the legacy `RNRecertAssessment` table be retired in favor of
   `RnicaAssessment(assessment_type="RECERT")`, given both are
   currently queried side-by-side in assessment history?
4. Does the general `Assessment` model need the same
   singleton/episode-scoping treatment RNICA has, or is it intentionally
   unconstrained?

## Repository Files Reviewed

- `backend/app/models/rnica_assessment.py`
- `backend/app/models/rn_recert_assessment.py`
- `backend/app/models/benefit_period.py`
- `backend/app/models/certification.py`
- `backend/app/models/assessment.py`
- `backend/app/models/body_systems.py`
- `backend/app/api/visits.py`
- `backend/app/services/assessment_history_service.py`
