# SNS RNICA Section 1 Implementation Contract
**Status:** DRAFT — for review before any Section 1 code change.
**Scope:** RN ICA Section 1 ("Patient & Encounter Snapshot" / Global Facesheet Frame) only.

---

## 1. Documents Reviewed

All governance docs for RN ICA live only under the mirrored workspace path
(`copilot-worktrees\sns-emr\suasonns-fluffy-winner\docs\`); they do not exist
in `C:\dev\SNS EMR\docs\` (that directory has an older/incomplete doc set) and
are excluded from git tracking there via `.gitignore` line 79
(`copilot-worktrees/`). Content on both paths is otherwise mirrored live, so
this contract file is created in `C:\dev\SNS EMR\docs\` for tracking, but was
researched from the workspace copy where the full chain exists.

| File | Version | Status | Role | Relevant lines |
|---|---|---|---|---|
| `SNS_RNICA_MASTER_MAP_1.0.md` | 1.0 | Superseded (Section 1-12 descriptions only) | Historical | L40-42 (old Section 1 stub) |
| `SNS_RNICA_MASTER_MAP_1.1.md` | 1.1 | **Controlling** — explicitly states it supersedes 1.0's Section 1-12 text | Controlling | L15 (Governance Freeze), L40-42 (supersession statement), L68-92 (Global Facesheet Frame), L94-151 (Section 1 full spec) |
| `SNS_RNICA_MASTER_MAP_MAPPING_2.0.md` | 2.0 | Phase 2 Step 1, frozen, not superseded | Supporting | L34 (Patient Demographics → Section 1, direct match) |
| `SNS_RNICA_BUILD_SEQUENCING_2.0.md` | 2.0 | Phase 2 Step 4, frozen | Supporting | L44-49 (Sequence 2: section reorganization is prerequisite for new fields) |
| `SNS_RNICA_GAP_VALIDATION_2.0.md` | 2.0 | Phase 2 Step 3, frozen | Supporting | L41 (only validated Section 1 gap: ACP path mismatch, MEDIUM) |
| `SNS_RNICA_SECTION_INVENTORY_1.0.md` | 1.0 | Phase 1, frozen | Supporting | L1317 (current→target mapping restated) |
| `SNS_RNICA_FIELD_INVENTORY_1.0.md` | 1.0 | Phase 1, frozen | Supporting | L74-175 (current "Patient Demographics" field list) |
| `SNS_RNICA_API_MAPPING_1.0.md` | 1.0 | Phase 1, frozen | Supporting | L137 (current demographics API/DB), L219-220 (sync functions) |
| `SNS_RNICA_DATABASE_MAPPING_1.0.md` | 1.0 | Phase 1, frozen | Supporting | L167-182 (Code Status / Contacts table mapping) |
| `SNS_RNICA_NARRATIVE_SOURCE_INVENTORY_1.0.md`, `SNS_RNICA_VALIDATION_INVENTORY_1.0.md`, `SNS_RNICA_AUDIT_INVENTORY_1.0.md`, `SNS_RNICA_HOPE_CROSSWALK_VERIFICATION_2.0.md` | 1.0/2.0 | Frozen | Supporting, not Section-1-specific | — |
| `SNS_POC_GENERATION_MATRIX_1.0.md`, `SNS_ACTION_CENTER_TRIGGER_INVENTORY_1.0.md`, `SNS_DESIGN_SYSTEM_1.0.md` | 1.0 | Frozen | Out of scope for Section 1 (POC/Action Center/global design tokens) | Not required for read-only Section 1 display |

**Precedence applied:** MASTER_MAP_1.1 §"Version 1.1 Amendment" (L42) is an
explicit, dated supersession statement — it wins over 1.0's Section 1
description wherever the two conflict. All Phase 2 documents (Mapping, Gap
Validation, Build Sequencing) are consistent with 1.1 and were not
overridden.

---

## 2. Controlling Section 1 Specification (verbatim source: `SNS_RNICA_MASTER_MAP_1.1.md` L68-151)

**Purpose:** A persistent, top-of-assessment identity/clinical/care-team
snapshot ("Global Facesheet Frame," always visible) plus a dedicated
Section 1 detail view ("Patient & Encounter Snapshot").

**Required visible information (Global Facesheet Frame, L70-91):**
Patient identity, MRN, DOB, Benefit period, Level of care, Terminal
diagnosis, Related diagnoses, Code status, Allergies, Residence/facility,
Attending physician, Medical director, Primary caregiver, Decision-maker,
Current PPS/KPS/FAST/NYHA, Assessment completion status, Autosave status,
Immediate clinical alerts, Admission Action Center, Current section
navigation.

**Section 1 detail contents (L97-149):** Patient (name, MRN, DOB, age, sex,
SOC date, benefit period, level of care, payer, residence type, facility,
site of service, admitted from, living arrangement); Clinical Identity
(terminal/related/unrelated diagnoses, comorbidities, code status,
allergies, current medication summary); Care Team (attending, medical
director, assigned RN, assigned disciplines, primary caregiver,
decision-maker, emergency contact); Communication (preferred language,
interpreter need, communication limitations, cultural considerations); POC
Functions (view Master POC, active problems, goals, interventions — links,
not data entry).

**Editable vs. read-only (L150-151, verbatim):** *"This section displays
authoritative information. It does not duplicate or independently own
patient data."* → **Section 1 is READ-ONLY.** It must not become a second
place to enter/edit demographics, diagnoses, or contacts.

**Source system:** Not specified field-by-field in the Master Map itself,
but per `SNS_RNICA_MASTER_MAP_MAPPING_2.0.md` L34 and
`SNS_RNICA_MASTER_MAP_1.0.md` L42-43, the current-state source for this
content is: **Patient Demographics, Caregiver Assessment, Advanced Care
Planning, Facesheet.** The already-existing, already-authoritative frontend
API for exactly this data is `GET /patients/{id}/facesheet`
(`src/api/facesheet.ts: fetchFacesheet`), the same call `PatientFacesheet.jsx`
uses.

**Does Section 1 store data or reference existing data?** References only.
No new table, no new write path, no new `_base_patient()`/patient_charts.py
fields.

**Required actions:** POC Functions are navigation links (View Master POC /
active problems / goals / interventions), not editors.

**Prohibited duplication:** Do not re-enter demographics/diagnoses/contacts
inside RNICA's Section 1. Existing RNICA "Patient Demographics" `form_data`
fields (firstName/lastName/dob/gender, HOPE A1110/A1005/A1010, ACP
F2000/F2100/F2200) are a **separate, still-authoritative HOPE-assessment
capture flow** per `SNS_RNICA_API_MAPPING_1.0.md` L137 (they sync **out** to
`patient_facesheets`/`patient_contacts`/`patient_code_statuses`) — Section 1
does not replace, remove, or re-derive from that flow; it is an
**additional, read-only display frame** sourced independently from the
Facesheet API.

**Required validation:** None (read-only display has no validation rules of
its own; existing HOPE/ACP validation on the Patient Demographics
form_data fields is unaffected).

**Required audit behavior:** None new. No writes occur from Section 1, so
no new audit events.

**Relationship to Facesheet/Admission/RNICA/POC/Finalization:** Facesheet is
the data source; Admission Action Center is a separate global surface
(not part of Section 1); POC Functions are read-only links into Section 11
(Master Plan of Care Review, not yet built — out of scope here); Section 1
has no relationship to Finalization (Section 12) beyond showing
"Assessment completion status," which already exists in RNICA's own
progress-tracking state.

---

## 3. Field Contract

| Display label | Source model/table | Source API + response property | Existing frontend property (Facesheet) | Status | Permitted behavior | Missing behavior | Planned file change |
|---|---|---|---|---|---|---|---|
| Patient name, MRN | `Patient` | `GET /patients/{id}/facesheet` → `identity.first_name/middle_name/last_name`, top-level `mrn` | `PatientBanner` | Exists | Display | — | RNICA.jsx: new read-only frame component |
| DOB, Age, Sex | `PatientFaceSheet` | `identity.dob`, `identity.gender` | `PatientBanner` (age computed) | Exists | Display | — | same |
| SOC date, Benefit period, Level of care | `PatientFaceSheet` | `service_dates.soc_date`, `level_of_care.*` | `HospiceSnapshotCard` (benefit period auto-calculated client-side) | Exists | Display | — | same |
| Payer | `PatientFaceSheet` | `insurance.primary_payer` | `HospiceSnapshotCard` | Exists | Display | — | same |
| Residence type, Facility, Site of service, Admitted from | `PatientFaceSheet` | `place_of_service.*` | `HospiceSnapshotCard` | Exists | Display | — | same |
| Living arrangement | `PatientFaceSheet` | Not in `FacesheetResponse` today | — | **BLOCKED BY MISSING SOURCE** | — | Not exposed by any authoritative API found | None — do not fabricate |
| Terminal/related/unrelated diagnoses, comorbidities | `PatientFaceSheet` diagnoses | `clinical.diagnoses.primary/secondary/comorbidities`, `clinical.active_*` | `HospiceSnapshotCard` | Exists | Display | — | same |
| Code status | `patient_code_statuses` | `GET /patients/{id}/code-status` (history) + facesheet snapshot if present | `HospiceSnapshotCard` (`codeStatusHistory` prop) | Exists | Display | — | same |
| Allergies | `PatientFaceSheet` | `clinical.allergies`, `clinical.has_allergies` | `PatientBanner` (`allergyList`) | Exists | Display | — | same |
| Current medication summary | Not in facesheet response | — | — | **BLOCKED BY MISSING SOURCE** | — | No authoritative summary endpoint identified in this review | None — do not fabricate |
| Attending physician, Medical director | `PatientFaceSheet` | `physicians.attending.*`, `physicians.medical_director.*` | `HospiceSnapshotCard` | Exists | Display | — | same |
| Assigned RN, Assigned disciplines | `PatientAssignment` (per `patient_charts.py` import) | Not present in `FacesheetResponse`; separate care-team/assignment source used elsewhere in `patient_charts.py` | `CareTeamCard` (via a different fetch than `fetchFacesheet`, not yet located in this review) | **Needs confirmation** | Display, once source located | Exact endpoint for care-team/discipline assignment not yet traced | Locate before coding; do not invent |
| Primary caregiver, Decision-maker, Emergency contact | `patient_contacts` | `contacts.responsible_party.*`, `contacts.emergency_contact.*` | Not directly in reviewed `CareTeamCard` snippet — needs confirmation of PCG/DPOA vs. "responsible_party" naming match | **Needs confirmation** | Display once field names reconciled | `patient_contacts` types (PCG/DPOA/decision-maker) vs. facesheet's `responsible_party`/`emergency_contact` naming not yet reconciled | Reconcile before coding |
| Preferred language, Interpreter need, Communication limitations, Cultural considerations | `PatientFaceSheet` | `identity.language` only; interpreter/communication-limitation/cultural fields not in `FacesheetResponse` | — | **Partially BLOCKED** | Display `language`; mark rest missing | Interpreter need, communication limitations, cultural considerations have no located authoritative source | Do not fabricate; omit or explicitly label "not captured" |
| PPS/KPS/FAST/NYHA | Performance status records | `GET /patients/{id}/performance-history` (`fetchPerformanceHistory`) | `HospiceSnapshotCard` (`performanceHistory` prop) | Exists | Display latest entry | — | same |
| Assessment completion status, Autosave status | RNICA's own in-memory/section-progress state | N/A — already computed client-side in RNICA.jsx | N/A (RNICA-only) | Exists | Display | — | same |
| POC Functions (View Master POC / problems / goals / interventions) | N/A — navigation only | Existing POC routes, if any | N/A | **Needs confirmation** | Read-only links | Confirm Section 11 (Master POC) route exists; per Mapping doc L63 it may not yet exist | Locate/confirm before coding; if absent, mark BLOCKED and omit link rather than invent a route |

---

## 4. Conflict Register

1. **"Patient Demographics" (current RNICA section, editable) vs. Section 1
   (target, read-only).**
   - Conflicting statements: `SNS_RNICA_API_MAPPING_1.0.md` L137 documents
     "Patient Demographics" as an editable RNICA form-data section
     (firstName/lastName/dob/gender, HOPE/ACP fields) that **writes** to
     `patient_facesheets`/`patient_contacts`. `SNS_RNICA_MASTER_MAP_1.1.md`
     L150-151 states the target Section 1 "does not duplicate or
     independently own patient data" (read-only).
   - Controlling statement: MASTER_MAP_1.1 governs the **new unified
     Section 1 frame** being added; it does not instruct removal of the
     existing HOPE/ACP-capturing "Patient Demographics" form fields, which
     remain the write path per `SNS_RNICA_MASTER_MAP_MAPPING_2.0.md`'s
     "direct match" framing (old section → new section is a *relocation*,
     not a *deletion*).
   - Reason: Build Sequencing Sequence 2 (§`SNS_RNICA_BUILD_SEQUENCING_2.0.md`
     L44-49) frames this as section reorganization, not field removal.
     Resolution: keep the existing editable demographics fields wherever
     they currently live in RNICA's flow; add Section 1 as an
     **additional, read-only** snapshot frame sourced from the Facesheet
     API. Do not merge or remove the editable fields as part of this work.

2. **Vitals / Symptom Impact / Diagnoses split conflicts** (Mapping doc
   L69-90) — **not applicable to Section 1**; these concern Sections 2, 3,
   5, 6, 7, deferred, out of scope here.

3. **PatientFacesheet.jsx role.** No document authorizes treating
   `PatientFacesheet.jsx`'s React components as an RNICA data source,
   component library, or API contract. Per explicit user direction,
   `PatientFacesheet.jsx` is a **visual design reference only** (layout,
   spacing, card treatment, typography). Superseded understanding: an
   earlier plan in this session to export/reuse its components directly is
   withdrawn.

---

## 5. Minimal Implementation Plan

**Frontend only. No backend changes.**

- `sns-emr-frontend/src/components/RNICA.jsx`:
  - Call `fetchFacesheet(resolvedPatientId)` (already exported from
    `src/api/facesheet.ts`) once per patient load, alongside the existing
    `fetchPatientSummary` call.
  - Call `fetchPerformanceHistory` and the code-status endpoint the same
    way `PatientFacesheet.jsx` does, for PPS/KPS/FAST and code-status
    history.
  - Add a new, independent, read-only presentational block (not an import
    from `PatientFacesheet.jsx`) rendering the Section 1 field set above,
    visually modeled on `PatientBanner`/`HospiceSnapshotCard`/`CareTeamCard`
    (spacing, card treatment, typography only).
  - No `update()`/write wiring — display only.
- **Before writing this component:** resolve the two "Needs confirmation"
  rows in §3 (assigned RN/disciplines source; PCG/decision-maker field
  reconciliation; POC Functions route existence) by tracing the actual
  fetch calls `PatientFacesheet.jsx`/`CareTeamCard` use beyond
  `fetchFacesheet`, without importing or coupling to that file's code.
- No API changes, no `_base_patient()` changes, no database changes.
- Tests: none exist today for RNICA header rendering; add a lightweight
  render test only if the project's existing test patterns cover
  `RNICA.jsx` (verify before adding new tooling).
- Owner-visible acceptance: open RNICA for a real patient, confirm the new
  Section 1 frame shows real DOB/gender/allergies/code status/attending/
  medical director sourced from the Facesheet (matching what
  `PatientFacesheet.jsx` shows for the same patient), confirm no field in
  the frame is editable, confirm existing "Patient Demographics" form
  fields elsewhere in RNICA are unchanged.

---

## 6. Explicit Non-Changes

- No edits to `PatientFacesheet.jsx` internals (no exports added, no
  refactor).
- No database schema changes.
- No changes to `_base_patient()` or any other `patient_charts.py`
  response shape.
- No role/capability work.
- No unrelated clinical sections (Sections 2-12 untouched by this
  contract).
- No compliance-audit work.
- No removal or modification of the existing "Patient Demographics"
  editable form-data fields/HOPE-ACP capture flow.

---

## 7. Open Items Blocking Full Implementation

1. Assigned RN / assigned disciplines source endpoint not yet traced.
2. Primary caregiver / decision-maker field-name reconciliation between
   `patient_contacts` types and the Facesheet response's
   `responsible_party`/`emergency_contact` naming not yet done.
3. POC Functions target route (Section 11 / Master POC) existence not
   confirmed — Mapping doc states Section 11 has no current-RNICA
   equivalent; if no route exists, these links must be omitted, not
   fabricated.
4. "Living arrangement," "current medication summary," "interpreter
   need," "communication limitations," "cultural considerations" have no
   located authoritative source — marked BLOCKED BY MISSING SOURCE; will
   be omitted from the initial Section 1 frame rather than fabricated.

No code changes will proceed until directed to resolve items 1-3 or to
build the frame with items 1-4 explicitly omitted/marked "not captured."
