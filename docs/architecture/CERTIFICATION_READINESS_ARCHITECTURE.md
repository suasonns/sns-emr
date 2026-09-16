# Certification Readiness Architecture

Status: Architecture guidance — no implementation authorized by this
document alone.
Companion to: `docs/ONC_CERTIFICATION_ROADMAP.md` (phase tracker)

## 0. Governing Directive

> Design every subsystem to be certification-ready. Document all
> certification-relevant requirements. Implement architecture that
> supports future certification. Do NOT defer critical workflow
> improvements in order to chase certification. Workflow, usability,
> evidence attribution, auditability, and clinical accuracy take
> priority. Certification readiness is required. Certification
> pursuit is optional until business conditions justify the
> investment.

Read literally, this means:

- **Required now:** the data model, audit trail, and access-control
  architecture must not make future ONC certification harder or
  impossible. New tables/fields should be added in a way that keeps a
  future FHIR/C-CDA mapping realistic.
- **Required now:** every certification-relevant requirement must be
  documented (this file + the roadmap), so nothing is forgotten or
  has to be rediscovered later.
- **Not required now:** actually building the FHIR R4 API, C-CDA
  generator, or EHI export endpoints. That is real, multi-week
  engineering work with no near-term deadline, and building it now
  would come at the direct expense of clinical workflow, evidence
  traceability, and usability work that this directive explicitly
  says takes priority.
- **Not authorized by this document:** any code change. This is
  planning/documentation only, same as the Evidence Platform
  architecture docs it sits alongside.

---

## 1. Current State — What Already Satisfies Certification-Readiness

These three of the eight items from the original request are **already
built, tested, and in production** — no new work is needed for
architectural readiness, only eventual mapping to ONC's specific test
scripts when certification pursuit begins.

### 1.1 Audit Logging — READY
- `backend/app/models/audit_log.py` — tenant-scoped `AuditLog` model
  with `request_id` (cross-request traceability), `ip_address`, actor
  (`user_id`), action, entity type/id, severity, and
  `affected_permissions` (before/after diff on role changes).
- `backend/app/services/audit_log_service.py` — write path.
- `backend/app/api/audit_log.py` / `owner_admin.py` `list_audit_logs()`
  — read/filter path (entity, category, date range, tenant, severity,
  free-text search).
- Already covers ONC §170.315(d)(2) "Auditable events and tamper
  resistance" and §170.315(d)(3) "Audit report(s)" at the data-model
  level. What is NOT yet built: a dedicated, ONC-test-script-shaped
  audit *report export* endpoint (the current export is a client-side
  CSV of the filtered UI table, not a certified export format) — see
  §3.3.

### 1.2 Access Control — READY
- `backend/app/core/roles.py` — data-driven `PLATFORM_PERMISSION_MATRIX`,
  `ROLE_AUTHORITY_RANK`, `role_can()`. No hardcoded superuser bypass
  (removed in a prior security remediation pass).
- `backend/app/core/role_guards.py` — endpoint-level permission
  dependencies (`require_owner()`, `require_platform_permission()`).
- `backend/app/core/permissions.py` — capability/permission constants.
- Satisfies the intent of ONC §170.315(d)(1) "Authentication,
  access control, authorization" at the architecture level. Formal
  certification would require mapping this matrix explicitly against
  the ONC test-script role/permission scenarios — a documentation
  task, not a rebuild.

### 1.3 Security Hashing — READY
- `backend/app/core/crypto.py` / `backend/app/core/security.py` —
  password hashing (not plaintext, not reversible encoding).
- Satisfies ONC §170.315(d)(7) "End-user device encryption" is a
  separate device-level control (out of scope for a server EMR) but
  password/credential hashing and integrity verification for
  authentication is already correctly implemented.

**No action needed on these three today.** They remain "keep doing
what we're doing" — do not regress them while building other
features (this is already covered by the existing Evidence Platform
guardrail docs' "no architecture downgrade" principle, which applies
equally here).

---

## 2. Data Model — Certification-Readiness Principle

The existing clinical data model (`backend/app/models/`) already has a
natural, low-friction path to FHIR R4 resources because it is
already normalized around real clinical concepts rather than free-text
blobs:

| Existing model | Future FHIR R4 mapping (not built) |
|---|---|
| `patient.py` (`Patient`) | `Patient` resource |
| `physician.py` / `patient_physician_assignment.py` | `Practitioner`, `PractitionerRole` |
| `visit.py`, `f2f_encounter.py` | `Encounter` |
| `patient_diagnosis.py` | `Condition` |
| `plan_of_care.py`, `poc.py` | `CarePlan` |
| `patient_order.py`, `physician_order.py`, `medication.py` | `MedicationRequest`, `ServiceRequest` |
| `document_record.py` | `DocumentReference` (and `Binary` for the underlying file/C-CDA payload) |
| `patient_allergy.py` | `AllergyIntolerance` |
| `assessment.py`, `rnica_assessment.py`, `safety_assessment.py`, etc. | `Observation` / `QuestionnaireResponse` |

**Principle going forward (required now, zero code cost):** when
adding new clinical fields to these models, prefer discrete, typed
columns (or a documented structured JSON shape) over unstructured
free-text where the same information could be a coded/structured FHIR
element later (e.g. a diagnosis code, a status enum, a quantity +
unit). This is already the prevailing pattern in this codebase (see
`icd10_master.py`, `enums.py`) — no change in direction, just an
explicit instruction not to drift from it while building new features.

This principle must never be used to justify slowing down or
complicating clinical workflow work — it only applies as a
tie-breaker when a field could reasonably be structured either way at
no added cost or delay.

---

## 3. Certification-Relevant Technical Requirements (Documented, Not Implemented)

These are the concrete technical requirements each future subsystem
will need to satisfy ONC test scripts, captured now so no
rediscovery is needed later. None of this is implemented today.

### 3.1 FHIR R4 API (§170.315(g))
- Resources needed: `Patient`, `Practitioner`, `Encounter`,
  `Condition`, `CarePlan`, `Observation`, `DocumentReference`,
  `Binary`.
- Must support SMART-on-FHIR OAuth2 patient-access and
  clinician-access flows.
- Must support the standard FHIR search parameters ONC requires per
  resource (e.g. `Patient?identifier=`, `Encounter?date=`).
- Must expose a `/metadata` (CapabilityStatement) endpoint.
- Should be built as a new, additive API surface (e.g.
  `backend/app/api/fhir/`) that reads from existing models via a
  translation/mapping layer — must not replace or duplicate the
  existing internal API models (same "additive, not a competing
  model" principle already established for the Evidence Platform).

### 3.2 C-CDA Generation & Ingestion (§170.315(b))
- Generate: Continuity of Care Document (CCD) at minimum — Referral
  Note and Transitions of Care documents likely needed for hospice
  workflows (admission, transfer, discharge/death).
- Ingest: parse an incoming C-CDA and reconcile
  problems/medications/allergies against existing patient records
  (reconciliation workflow, not blind overwrite — consistent with
  Evidence Platform's "identity of data" principle).
- Requires an XML/XSD-validated document generator — realistically a
  dedicated library (e.g. a C-CDA templating engine), not hand-rolled
  XML string building.

### 3.3 EHI Export (§170.315(h))
- Full-patient-record export in both a machine-readable format (e.g.
  a structured JSON/XML bundle covering every table referencing that
  patient) and a human-readable format (e.g. rendered PDF/HTML).
- Must be a formal, dedicated export endpoint/job — not the
  audit-log's current client-side CSV export, which only covers audit
  events, not the full chart.
- Given patient records span 100+ tables in this schema, this needs a
  registry-driven export ("for patient X, export every row in every
  patient-scoped table") rather than a hand-maintained list — hand
  -maintained lists silently drift as new patient-scoped models are
  added.

### 3.4 Documentation & Test Script Preparation
- Once any of the above is built, required deliverables are: API
  documentation (OpenAPI/FHIR CapabilityStatement), a security
  documentation package, and a data-model/mapping document — all
  should live under `docs/` alongside this file when written.
- ONC test scripts themselves are published by ONC per criterion;
  preparation work is: (1) map each test script step to the
  corresponding SNS endpoint/workflow, (2) run it internally, (3) fix
  gaps, before ever engaging a certification body (see
  `docs/ONC_CERTIFICATION_ROADMAP.md` Phase 4).

---

## 4. What This Document Does NOT Do

- It does not create any FHIR endpoint, C-CDA generator, or export
  job.
- It does not change `structured_findings.py`, the evidence platform,
  or any tenant-facing clinical workflow.
- It does not commit to a certification timeline or vendor
  (Drummond Group / ICSA Labs) — that remains a business decision,
  tracked in the roadmap's Phase 5.

## 5. Relationship to Existing Architecture Docs

This document sits alongside, and does not conflict with, the
Evidence Platform governance set (`README_FIRST.md`,
`ARCHITECTURE_LOCK.md`, `EVIDENCE_TRACEABILITY_VISION.md`,
`EVIDENCE_INTELLIGENCE_ROADMAP.md`,
`TENANT_PLATFORM_IMPLEMENTATION_GUARDRAILS.md`). Same rules apply:
evidence/traceability first, additive-not-replacing future layers, no
fabrication, Owners Platform priority. Certification readiness is an
additional, parallel constraint — not a reason to reorder that
existing priority stack.
