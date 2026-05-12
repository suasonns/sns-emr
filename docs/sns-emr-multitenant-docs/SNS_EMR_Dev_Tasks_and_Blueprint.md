# SNS EMR Development Tasks + Blueprint Map
**Scope:** Billing Safety, IDG Engine, POC Engine, Migration Engine, Alerts Engine, e‑Prescribing.  **Status model:** ✅ Done/Locked, 🟡 Partial, 🔴 Not started, ⚠️ Deferred.

![SNS EMR Blueprint Map](SNS_EMR_Blueprint_Map.png)

## Billing Safety Engine (Not Claims)

### Goal
Prevent denial-causing billing leakage by enforcing ‘billable readiness’ rules. (No 837/835 generation in MVP.)
### Data Model
- Create `billable_events` (or `billing_guardrails_log`) table to record why an event is billable/non-billable (immutable).
- Add `migration_date` to patient/agency context (already captured in migration).
- Add `billable_status` computed field/view for visits and orders (NOT stored if you prefer).
### Backend Rules (Hard Gates)
- Block any billable artifact with service date `< migration_date`.
- Orders: `status != ACTIVE` or `md_signed_at IS NULL` ⇒ NON-BILLABLE.
- Visits: `note_status != SIGNED/FINALIZED` ⇒ NON-BILLABLE.
- POC: `poc_status != ACTIVE` ⇒ flag ‘care delivered outside active POC’ (alert, not block unless tenant policy).
### APIs
- `GET /billing/eligibility/visit/{visit_id}` returns billable verdict + reasons.
- `GET /billing/eligibility/patient/{patient_id}?from=&to=` returns list of non-billable items.
### Verification
- Create a migrated patient; attempt to mark a pre-migration visit/order billable ⇒ must fail with reason ‘pre-migration’.
- Create a Day-1 order without MD signature ⇒ non-billable.
- Finalize note ⇒ billable flips to true.
### Tests
- Unit: rule evaluation for migration date boundary.
- Integration: order signature required.
- Integration: visit note finalization required.

## IDG Engine (14-Day Cadence + Evidence)

### Goal
Ensure IDG cadence is enforced and provable: tasks created, due, overdue, completed with evidence.
### Data Model
- Ensure `tasks` supports `task_type=IDG_POC_REVIEW`, `due_date`, `status`, evidence fields.
- Add `idg_meetings` table (optional MVP) OR use tasks + attachments.
- Add `idg_last_completed_at` per patient (derived from tasks).
### Task Logic
- On migration day: set last IDG = migration day (because you migrate after last real IDG).
- Seed next IDG task: due_date = migration_date + 14 days.
- Overdue job: marks tasks overdue; triggers blocking alerts.
### APIs
- `POST /patients/{id}/idg/complete` completes IDG task and writes evidence (reference_type=NOTE or MEETING).
- `GET /patients/{id}/idg/status` returns last_completed, next_due, overdue flag.
### Verification
- After migration: next IDG due exactly +14 days.
- Completing IDG sets completion evidence fields and status COMPLETED.
### Tests
- Unit: cadence computation.
- Integration: overdue job updates status and generates alerts when enabled.

## POC Engine (RN-Owned, Continuity-Seeded, MD-Approved)

### Goal
Preserve continuity without retyping while keeping migrated records immutable.
### Data Model
- `poc_documents` table with fields: `id`, `patient_id`, `status` (MIGRATED_REFERENCE, DRAFT, ACTIVE, SUPERSEDED), `source_system`, `effective_from`, `effective_to`, `created_by`, `md_signed_at`.
- Link: `migrated_poc_id` → `seeded_poc_id`.
### Migration Behavior
- Store migrated POC as `MIGRATED_REFERENCE` (read-only).
- Create new SNS EMR POC seeded with same content: `status=DRAFT`, `effective_from=migration_date`.
### Workflow
- RN reviews DRAFT POC: updates problems/interventions/frequencies.
- MD approves/signs: status becomes ACTIVE.
- Only ACTIVE POC drives tasks/frequency validation.
### APIs
- `POST /patients/{id}/poc/seed-from-migration` (Owner system action; auto-run during migration).
- `PATCH /poc/{poc_id}` RN edits (only when status=DRAFT).
- `POST /poc/{poc_id}/md-sign` activates.
### Verification
- Attempt to edit migrated POC ⇒ 403.
- Seeded POC editable by RN until signed.
- Signed POC immutable.
### Tests
- Unit: status transitions.
- Integration: permissions (RN vs MD vs Owner).

## Migration Engine (Owner Bulk + Tenant Single Patient)

### Goal
Bulk-create active charts safely with mismatch prevention and two-phase migration.
### Owner Bulk Console (Owner-only endpoints)
- Upload batch facesheets ⇒ create patient shells (ACTIVE).
- Upload batch PDFs ⇒ require identity match and owner confirmation before attach.
- Enforce ‘one patient per PDF’ heuristic; flag multi-patient PDFs for manual split.
### Data Model
- `documents` table: `patient_id`, `source_system`, `doc_type`, `date_range_from/to`, `is_migrated`, `is_read_only`, `uploaded_by`, `owner_verified_at`, `match_confidence`.
- `migration_runs` table: run_id, tenant_id, started_at, completed_at, counts, failures.
### Matching Rules
- Require >=2 identifiers match (name + DOB + MRN/address/phone).
- Visual verification checkbox required; log it.
### Tenant Upload (single patient)
- Endpoint: `POST /patients/{id}/documents` with enforcement ‘single patient scope’.
### Continuity Seeding
- After attachments: create seeded SNS objects (POC, orders, meds, treatments, DME, supplies) effective from migration day.
### Verification
- Bulk upload with mismatched identifiers must stop and require manual choice.
- Tenant cannot access bulk endpoints (403).
### Tests
- Integration: owner vs tenant authorization.
- Integration: mismatch prevention.

## Alerts Engine (Blocking vs Informational + Escalation)

### Goal
Anything out of ordinary generates alerts; blocking alerts prevent go-live readiness.
### Data Model
- `alerts` table: `id`, `tenant_id`, `patient_id` (nullable for system), `alert_type`, `severity` (INFO/WARN/CRITICAL), `cms_reference_ids` (array/text), `created_at`, `resolved_at`, `resolved_by`, `payload_json`.
- `alert_rules` table: configurable thresholds per tenant (late note hours, schedule times).
### Blocking Alerts (MVP)
- Missing MD signature on Day-1 orders.
- Missing RN POC verification.
- IDG due/overdue.
- CHC criteria failed if LOC marked continuous.
### Informational Alerts
- Migration incomplete.
- Excessive export/print activity.
- High revocation risk admissions (decision support).
### Delivery Channels
- In-app dashboard first (admin).
- Optional email/SMS later (defer).
### Verification
- Trigger each blocking alert with a test patient and confirm it appears only within tenant.
- Resolve alert logs resolution and stops repeating.
### Tests
- Unit: rule evaluation.
- Integration: tenant scoping.

## e‑Prescribing Engine (Optional, Non‑Controlled Only)

### Goal
Tenant-requested optional eRx for non-controlled substances only; Owner-enabled.
### Feature Flag
- `FEATURE_KEY=EPRESCRIBING` default OFF; enabled per tenant by Owner.
### Constraints (Locked)
- Only SNS EMR Day-1+ orders with MD signature can be transmitted.
- Migrated orders cannot be transmitted.
- EPCS controlled substances out of MVP.
### Data Model
- `prescriptions` table: order_id, patient_id, prescriber_id, pharmacy_id, status (QUEUED/SENT/FAILED/ACKED), sent_at, error_message, payload_hash.
### APIs
- `POST /orders/{id}/erx/send` (MD-only; requires feature enabled).
- `GET /orders/{id}/erx/status`.
### Verification
- Feature OFF ⇒ endpoint returns 403/feature-disabled.
- Feature ON + MD signed order ⇒ creates prescription record and status transitions.
### Tests
- Integration: feature gating and MD-only permission.

## Blueprint Map (Mermaid)
```mermaid
flowchart TD
  A[Owner Bulk Migration] --> B[Patient Shells ACTIVE]
  A --> C[Historical Docs Vault (Read-only)]
  B --> D[Continuity Seeder Day-1 Objects]
  C --> D
  D --> E[POC Engine (RN-owned)]
  D --> F[Orders Engine (RN review -> MD sign)]
  D --> G[Meds/Treat/DME (RN verify)]
  E --> H[IDG Engine (14-day tasks)]
  H --> I[Alerts Engine]
  F --> J[Billing Safety Gate]
  I --> J
  J --> K[Security/PHI Controls MVP]
  J --> L[Optional eRx (Owner-enabled)]
  K --> M[Production Readiness Gate]
  J --> M
  I --> M
```