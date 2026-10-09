# SNS Hospice EMR Body Systems
## Engineering Specification for GitHub Copilot

**Status:** Implementation baseline  
**Scope:** Body Systems workspace for Initial Comprehensive RN Assessment, with reusable Routine RN and Recertification modes  
**Priority:** Initial Comprehensive RN Assessment first  
**Audience:** Engineering, product owner, clinical reviewer, QA  

---

## 1. Purpose

Implement the approved SNS Body Systems clinical register without allowing generated code, Figma examples, or hardcoded demonstration content to redefine clinical behavior.

The implementation must preserve these product rules:

1. One clinical fact has one owning body system.
2. A fact may be referenced elsewhere but may not be reassessed elsewhere.
3. All ten body systems remain visible and in scope in every visit mode.
4. Blank is not normal and historical data is not current evidence.
5. Admission establishes baseline, Routine RN emphasizes current change, and Recertification emphasizes comparison and progression.
6. Manual workflow is complete and usable without AI.
7. AI is optional and assists extraction only; the RN remains authoritative.
8. Final nurse review is by exception and does not duplicate system documentation.
9. The body diagram is a location aid; the wound record is the clinical record.
10. Figma sample values, dates, counts, statuses, and patient facts are fixtures, not business rules.

---

## 2. Scope Boundary

### 2.1 In scope for the first implementation milestone

- Initial Comprehensive RN Assessment
- Ten-system navigation and progress tracking
- Clinical register shell
- System-level review states
- Detailed system forms
- Partial/unable-to-assess workflow
- Integumentary wound records, body location aid, and Braden scale
- Draft persistence
- Final nurse review by exception
- Audit history for create, update, correction, review, and source acceptance
- Responsive desktop and mobile behavior
- Extension points for Routine RN, Recertification, and optional AI

### 2.2 In scope as reusable architecture, but not the first production milestone

- Routine RN mode
- Recertification comparison mode
- AI-assisted evidence extraction
- Source-linked evidence suggestions

### 2.3 Out of scope unless separately specified

- Hospice eligibility determination
- Physician certification or recertification approval
- Orders
- Automatic plan-of-care changes
- Billing
- HOPE submission generation
- iQIES submission
- Medication administration
- Automatic coding
- Automatic clinical conclusions

---

## 3. Unverified Technical Stack

The repository is the source of truth for versions and installed packages. Before implementation, inspect:

- `package.json`
- lock file
- framework configuration
- existing component library
- Tailwind/PostCSS configuration
- shadcn configuration
- form and validation dependencies
- database client and migration framework
- test framework

Do not install or upgrade packages until those files are inspected.

### Preferred stack if already present

- React with TypeScript
- shadcn/ui components
- Tailwind only if already configured or required by the current shadcn setup
- React Hook Form
- Zod
- Lucide icons

If the repository differs, adapt this specification to the existing stack rather than replacing the stack during the Body Systems feature.

---

## 4. Domain Model

### 4.1 Core enums

```ts
export const BODY_SYSTEMS = [
  "neurological",
  "respiratory",
  "cardiovascular",
  "nutrition",
  "gastrointestinal",
  "genitourinary",
  "musculoskeletal",
  "integumentary",
  "infection_immunological",
  "endocrine",
] as const;

export type BodySystemCode = (typeof BODY_SYSTEMS)[number];

export type VisitMode =
  | "admission_comprehensive"
  | "routine_rn"
  | "recertification";

export type AssessmentSituation =
  | "no_current_concern"
  | "stable_existing"
  | "new_or_worsening"
  | "unable_to_assess";

export type SystemReviewState =
  | "not_reviewed"
  | "in_progress"
  | "reviewed"
  | "reviewed_with_exception";

export type EvidenceSourceType =
  | "rn_observation"
  | "patient_report"
  | "caregiver_report"
  | "prior_clinical_record"
  | "external_record"
  | "device_measurement"
  | "ai_extraction";

export type ExceptionType =
  | "unreviewed_system"
  | "required_field_missing"
  | "partial_scope"
  | "unable_to_assess"
  | "source_missing"
  | "date_time_missing"
  | "conflicting_evidence"
  | "nurse_judgment_required"
  | "low_confidence_ai"
  | "follow_up_missing";
```

### 4.2 Primary entities

```ts
interface BodySystemsAssessment {
  id: string;
  patientId: string;
  visitId: string;
  visitMode: VisitMode;
  status: "draft" | "ready_for_review" | "recorded" | "signed";
  startedAt: string;
  recordedAt?: string;
  recordedBy?: string;
  signedAt?: string;
  signedBy?: string;
  version: number;
}

interface SystemAssessment {
  id: string;
  bodySystemsAssessmentId: string;
  system: BodySystemCode;
  situation?: AssessmentSituation;
  reviewState: SystemReviewState;
  assessedAt?: string;
  assessedBy?: string;
  limitation?: AssessmentLimitation;
  summary?: string;
  version: number;
}

interface ClinicalFinding {
  id: string;
  systemAssessmentId: string;
  ownerSystem: BodySystemCode;
  findingType: string;
  value: unknown;
  currentState: "present" | "absent" | "unknown" | "not_assessed";
  changeState?: "baseline" | "stable" | "improved" | "worsened" | "new" | "resolved" | "unknown";
  observedAt?: string;
  sourceEvidenceIds: string[];
  createdBy: string;
  createdAt: string;
  updatedBy: string;
  updatedAt: string;
  version: number;
}

interface Evidence {
  id: string;
  sourceType: EvidenceSourceType;
  sourceRecordId?: string;
  sourceDateTime?: string;
  excerpt?: string;
  enteredBy?: string;
  enteredAt: string;
  status: "current" | "historical" | "proposed" | "rejected";
}

interface Intervention {
  id: string;
  systemAssessmentId: string;
  description: string;
  performedAt?: string;
  response?: string;
  performedBy?: string;
}

interface FollowUp {
  id: string;
  systemAssessmentId: string;
  responsibleRole?: string;
  responsibleClinicianId?: string;
  timing?: string;
  contingency?: string;
  status: "needed" | "planned" | "completed" | "not_needed";
}

interface AssessmentLimitation {
  scope: string[];
  reason: string;
  assessedPortion?: string;
  followUpRequired: boolean;
  responsibleClinicianId?: string;
  timingOrContingency?: string;
}

interface ReviewException {
  id: string;
  bodySystemsAssessmentId: string;
  system: BodySystemCode;
  type: ExceptionType;
  fieldPath?: string;
  message: string;
  blockingLevel: "informational" | "draft_allowed" | "record_blocking" | "signature_blocking";
  status: "open" | "resolved" | "waived";
  resolvedAt?: string;
  resolvedBy?: string;
  resolutionNote?: string;
}
```

### 4.3 Wound entities

```ts
interface WoundRecord {
  id: string;
  systemAssessmentId: string;
  label: string;
  locationText: string;
  bodyRegionCode?: string;
  bodyDiagramMarker?: BodyDiagramMarker;
  woundType: string;
  stage?: string;
  lengthCm?: number;
  widthCm?: number;
  depthCm?: number;
  undermining?: string;
  tunneling?: string;
  woundBed?: string;
  drainage?: string;
  odor?: string;
  periwound?: string;
  dressing?: string;
  changeFromPrior?: string;
  assessedAt: string;
  assessedBy: string;
  priorWoundRecordId?: string;
  version: number;
}

interface BodyDiagramMarker {
  view: "anterior" | "posterior" | "left_lateral" | "right_lateral";
  normalizedX: number;
  normalizedY: number;
  label: string;
}

interface BradenAssessment {
  id: string;
  systemAssessmentId: string;
  sensoryPerception: number;
  moisture: number;
  activity: number;
  mobility: number;
  nutrition: number;
  frictionShear: number;
  total: number;
  assessedAt: string;
  assessedBy: string;
  riskFollowUp?: string;
}
```

Body-diagram coordinates never replace `locationText`, wound type, stage, measurements, tissue, drainage, periwound, or dressing data.

### 4.4 AI entities

```ts
interface AIExtractionRun {
  id: string;
  visitId: string;
  sourceEvidenceId: string;
  modelMetadata: Record<string, string>;
  createdAt: string;
  status: "proposed" | "partially_reviewed" | "completed" | "dismissed";
}

interface AISuggestion {
  id: string;
  extractionRunId: string;
  ownerSystem: BodySystemCode;
  targetFieldPath: string;
  proposedValue: unknown;
  confidence?: "low" | "medium" | "high";
  sourceExcerpt: string;
  disposition: "pending" | "accepted" | "edited" | "rejected";
  reviewedBy?: string;
  reviewedAt?: string;
}
```

AI suggestions must not be stored as current clinical findings until an authorized clinician accepts or edits them.

---

## 5. Clinical Ownership Registry

Ownership must be represented in code, not inferred from component placement.

```ts
interface OwnershipRule {
  owner: BodySystemCode;
  factKeys: string[];
  referenceableBy: BodySystemCode[] | "all";
}
```

Minimum registry:

- Neurological owns orientation, cognition, responsiveness, mental status.
- Respiratory owns dyspnea, cough, sputum, lung sounds, respiratory rate/pattern, oxygen use, ventilator/airway support, respiratory exertion tolerance.
- Cardiovascular owns edema, pulse/rhythm, heart sounds/perfusion, blood pressure/orthostatic findings, chest pain, syncope, circulation, cardiac devices.
- Nutrition owns intake, weight, weight change, appetite, swallowing/nutritional burden when defined as nutritional status.
- Gastrointestinal owns bowel status and gastrointestinal symptoms.
- Genitourinary owns urinary status and genitourinary symptoms.
- Musculoskeletal owns gait, balance, transfers, mobility, weakness as a mobility/function assessment.
- Integumentary owns skin integrity, wounds, pressure injuries, wound treatment detail, body-diagram wound markers, and Braden.
- Infection/Immunological owns active infection status and infection findings.
- Endocrine owns diabetes and endocrine findings.

### Non-duplication rules

- Edema is owned by Cardiovascular and may be referenced but not reassessed in Integumentary.
- Braden mobility and nutrition subscores are pressure-risk inputs and do not complete Musculoskeletal or Nutrition assessments.
- Body-diagram wound location is contextual and does not complete the wound record.
- Historical evidence may be displayed in any allowed context but cannot mark a current system reviewed.

---

## 6. Visit-Mode Behavior

### 6.1 Shared invariants

- Same ten systems and same ownership registry in all modes.
- Same primary entity model.
- Same final exception engine.
- Same source/evidence model.
- Mode controls required field profiles, labels, comparison views, and validation rules.

### 6.2 Admission / Comprehensive

Primary goal: establish current baseline.

Required behavior:

- All ten systems remain visible.
- Every system must receive an explicit current review outcome or documented limitation.
- Detailed baseline fields are available inline or via the owning system detail view.
- Existing records may be used as historical evidence but do not become current without clinician review.
- Abnormal findings can generate interventions and follow-up.
- Admission must not be reduced to a change-only workflow.

### 6.3 Routine RN

Primary goal: document the current state, change, intervention response, and follow-up without re-entering unchanged baseline detail.

- Prior evidence is read-only until explicitly confirmed or updated.
- Current review is still required for all ten systems.
- Stable does not mean normal.
- New/worsening and unable-to-assess selections open required detail.

### 6.4 Recertification

Primary goal: compare dated current evidence with dated prior-period evidence.

- Show current, prior-period, progression/change, symptom burden, and evidence gaps.
- Do not copy prior values into current fields.
- Unknown source/date remains unknown.
- Recertification review does not require recreating an admission assessment.

---

## 7. System State Machine

```text
NOT_REVIEWED
  -> IN_PROGRESS
  -> REVIEWED
  -> REVIEWED_WITH_EXCEPTION

REVIEWED_WITH_EXCEPTION
  -> IN_PROGRESS when correction opens
  -> REVIEWED when all exceptions resolve
```

Situation branches:

```text
NO_CURRENT_CONCERN
  -> record explicit current review evidence

STABLE_EXISTING
  -> require current confirmation and retain dated prior reference

NEW_OR_WORSENING
  -> require current finding/change, intervention/response, and follow-up decision

UNABLE_TO_ASSESS
  -> require scope, reason, assessed portion if any, follow-up responsibility, and timing/contingency
```

“Unable to assess” must never be converted to normal, reviewed without limitation, or fully assessed.

---

## 8. Validation Architecture

Keep validation in three separate layers:

1. **Field schema validation**: type, format, allowed values.
2. **Clinical workflow validation**: required evidence according to mode and selected branch.
3. **Completion validation**: exceptions that affect record or signature readiness.

Do not place all rules inside JSX components.

Suggested modules:

```text
/domain/body-systems/ownership.ts
/domain/body-systems/fieldSchemas.ts
/domain/body-systems/workflowRules.ts
/domain/body-systems/exceptionRules.ts
/domain/body-systems/completionRules.ts
```

### Required invariants

- All ten system rows are created for a new Body Systems assessment.
- A system cannot be marked reviewed merely because prior data exists.
- A required finding cannot be silently defaulted to normal.
- AI cannot set `assessedBy`, `recordedBy`, or signature fields.
- An accepted AI suggestion must record source, reviewer, time, original proposal, and accepted/edited value.
- A limitation requires a reason.
- Partial scope retains the unassessed scope as an exception.
- Wound marker alone cannot satisfy wound documentation.
- Braden total must be derived from subscales, not independently editable.

### Blocking policy

- Draft save is allowed with open exceptions.
- “Record review” requires all `record_blocking` exceptions resolved.
- Signature requires all `signature_blocking` exceptions resolved.
- Do not hardcode which fields are blocking until the approved field inventory identifies them.
- Unresolved items stay visible; the application must not pretend completion.

---

## 9. AI Governance

### AI may

- extract observations from a selected source
- propose structured values
- identify missing or ambiguous evidence
- group related suggestions
- show source excerpts

### AI may not

- auto-accept
- auto-save as current evidence
- infer nurse-only assessments
- infer symptom impact on comfort/function from severity alone
- determine hospice eligibility
- approve documentation
- create orders
- approve or change the plan of care
- mark a body system reviewed

### Acceptance flow

```text
source selected
-> extraction run created
-> suggestions displayed with source context
-> RN accepts, edits, rejects, or dismisses
-> accepted/edited values write to current form
-> RN saves
-> audit event records all dispositions
```

Group acceptance may be offered only when every item in the group is individually visible and editable, and uncertain or nurse-only fields are excluded.

---

## 10. UI Component Architecture

```text
BodySystemsWorkspace
├── VisitContextHeader
├── BodySystemsSidebar
├── VisitModeIndicator
├── AssessmentProgress
├── SystemRegister
│   └── SystemRegisterRow × 10
│       ├── SystemStatusSummary
│       ├── PriorEvidenceSummary
│       └── SystemRowActions
├── SystemAssessmentPanel
│   ├── SituationSelector
│   ├── CurrentEvidenceSection
│   ├── InterventionSection
│   ├── FollowUpSection
│   ├── LimitationSection
│   ├── PriorEvidencePanel
│   └── SystemSpecificFields
├── AIExtractionPanel optional
├── ReviewExceptionDrawer
└── StickyVisitActions
```

System-specific extensions:

```text
NeurologicalFields
RespiratoryFields
CardiovascularFields
NutritionFields
GastrointestinalFields
GenitourinaryFields
MusculoskeletalFields
IntegumentaryFields
├── SkinConditionFields
├── ImpairmentSelector
├── WoundRecordList
│   └── WoundRecordEditor
├── BodyLocationAid
└── BradenAssessment
InfectionImmunologicalFields
EndocrineFields
```

### shadcn/ui mapping if available

- Accordion or Collapsible for system rows
- Form, Input, Textarea, Select, Checkbox, RadioGroup
- Card for evidence groups
- Alert for safety/evidence notices
- Badge for concise state markers
- Dialog/Sheet for source evidence and mobile detail
- Tabs only where content is truly mutually exclusive
- Tooltip for short explanations only
- Button with explicit labels, not icon-only primary actions

Do not render each Figma text box as a separate hardcoded input. Fields must be driven by schemas/configuration where appropriate and specialized components where clinical behavior differs.

---

## 11. Responsive Behavior

### Desktop

- Persistent ten-system navigation when viewport permits.
- Register and expanded details remain in one workspace.
- Avoid navigation to separate pages for routine system-to-system movement.

### Mobile

- Single-column order.
- System selector/jump menu remains available.
- One expanded system at a time is acceptable.
- Sticky save/review actions must not cover fields.
- Source evidence and AI suggestions use an accessible sheet or inline expandable card.
- Preserve all clinical fields and exceptions; mobile is not a reduced clinical assessment.

---

## 12. Persistence and Concurrency

- Autosave may be added only if the existing application has an established pattern.
- Provide an explicit Save Draft action.
- Use optimistic concurrency with a version or row-version field.
- On conflict, do not overwrite silently. Show the conflicting record and require resolution.
- Preserve timestamps in UTC and display in the user’s configured timezone.
- A current finding must retain its clinical observation time separately from record creation/update times.

---

## 13. Audit Trail

Audit events must be append-only and include:

- assessment created
- system review started/completed/reopened
- field created/changed/cleared
- limitation recorded or changed
- prior evidence viewed/linked
- AI source selected
- AI suggestion accepted/edited/rejected/dismissed
- exception created/resolved/waived
- draft saved
- review recorded
- signature applied
- correction/addendum created

Each event must include actor, role, timestamp, patient/visit context, entity type/id, action, and before/after values where appropriate. Clinical corrections must not rewrite history.

---

## 14. API Contract Principles

Use repository conventions for transport and naming. Minimum operations:

```text
GET    visit body-systems assessment
POST   create body-systems assessment
PATCH  update system assessment
POST   add clinical finding
PATCH  update clinical finding
POST   add wound
PATCH  update wound
POST   save Braden assessment
GET    prior evidence for system
GET    open review exceptions
POST   resolve review exception
POST   record final review
POST   create AI extraction run
POST   disposition AI suggestion
```

Server must independently enforce ownership, authorization, review state, and completion rules. Client validation is not sufficient.

---

## 15. Security and Authorization

- Never use production patient data in source code, fixtures, screenshots, public demos, or external AI prompts.
- Use synthetic fixtures by default.
- Role permissions must distinguish view, edit, review, sign, correct, and administer.
- The RN identity associated with an assessment is server-derived, not accepted blindly from the client.
- Sensitive source excerpts must follow the same access controls as the clinical record.
- Log access and mutations according to the application’s established audit pattern.

---

## 16. Figma-to-Code Interpretation Rules

Every visible element must be classified before implementation:

1. **Sample content**: patient facts, dates, values, counts, names, narrative text.
2. **Visual token**: color, spacing, border, typography.
3. **Reusable component**: row, card, form field, alert, panel.
4. **Workflow state**: not reviewed, in progress, reviewed, exception.
5. **Business rule**: behavior approved in this specification.
6. **Clinical requirement**: validated field or rule from the approved field inventory.

Unless this specification or an approved field inventory says otherwise:

- sample text is not a default
- a displayed count is not a computed rule
- a colored badge is not a new enum
- a mock date is not timing logic
- a button does not imply permission
- an empty field does not imply optionality
- a visible field does not automatically become database schema

---

## 17. Repository and Migration Guardrails

Before changing the database:

1. Inspect live schema and migration history.
2. Identify existing visit, assessment, audit, evidence, wound, and signature models.
3. Prefer extending existing entities over creating parallel duplicates.
4. Use forward-only migrations.
5. Do not edit applied migrations.
6. Do not create duplicate enums or database types.
7. Separate schema migration from backfill.
8. Provide rollback/recovery instructions appropriate to the repository’s migration framework.
9. Verify migration on a clean database and a representative upgraded database.

---

## 18. Testing Requirements

### 18.1 Unit tests

- ownership registry resolves each fact to one owner
- Braden total calculation
- assessment state transitions
- exception generation and resolution
- AI suggestion disposition
- completion readiness
- historical evidence does not complete current review

### 18.2 Component tests

- all ten systems render
- selecting each situation displays correct fields
- unable-to-assess requires reason and scope
- draft save retains incomplete data and open exceptions
- body marker does not satisfy wound validation
- accepted AI suggestion writes only after RN action
- keyboard navigation and accessible names

### 18.3 Integration tests

- create admission and complete all ten systems
- save and reopen draft
- partial assessment appears in final review
- correction in final review updates owning field and resolves exception
- add, update, and compare wound records
- concurrency conflict does not silently overwrite
- historical values remain historical

### 18.4 End-to-end scenarios

1. Comprehensive admission with all systems reviewed and no major abnormality.
2. Admission with respiratory new/worsening findings and unresolved evidence.
3. Admission with one partial/unable neurological assessment.
4. Admission with a sacral pressure injury and completed Braden assessment.
5. Draft saved with five systems incomplete.
6. Final review corrects an exception in the owning field.
7. Routine stable visit reuses history without copying it as current evidence.
8. Recertification shows dated current/prior evidence and an unresolved evidence gap.
9. AI extraction accepted, edited, and rejected within one source group.
10. AI suggestion cannot populate nurse-only symptom-impact fields.

### 18.5 Acceptance criteria for first milestone

- Initial Comprehensive RN Assessment works without AI.
- All ten systems are always available.
- Every current review is explicit.
- Drafts can be saved incomplete without false completion.
- Exceptions are generated predictably and link to the owning field.
- Integumentary supports multiple wounds, body location aid, wound detail, and Braden.
- No cross-system duplicate ownership is introduced.
- Audit history can reconstruct who changed what and when.
- Desktop and mobile preserve the same clinical meaning.

---

## 19. GitHub Copilot Implementation Instructions

Use this preamble for every implementation request:

```text
Implement only the requested slice of SNS Body Systems.

Before editing:
1. Inspect repository structure and package versions.
2. Identify existing patterns for forms, validation, API calls, authorization, audit, database models, and tests.
3. State which files will change and why.
4. Do not install or upgrade dependencies without an explicit requirement.
5. Do not infer business rules from Figma sample content.

During implementation:
- Preserve one-fact/one-owner rules.
- Keep all ten systems present.
- Do not treat prior evidence as current assessment.
- Do not allow AI to auto-document or mark a system reviewed.
- Keep clinical rules outside presentational JSX.
- Use the smallest safe change.
- Add tests for every behavior changed.
- Do not modify unrelated features.
- Do not rewrite migration history.

If the repository conflicts with this specification, stop and report the conflict rather than inventing a solution.
```

### First recommended GitHub task

```text
Create the Body Systems domain types, ownership registry, visit-mode configuration, state machine, and unit tests only. Do not create UI or database migrations yet. Reuse existing repository conventions. Return a file-by-file summary and any unresolved conflicts.
```

### Second recommended GitHub task

```text
Create the read-only Body Systems workspace shell using existing shadcn/ui components if present: visit context header, ten-system navigation, system register, progress summary, and responsive mobile layout. Use synthetic fixture data behind a typed fixture adapter. Do not hardcode clinical rules into JSX and do not add persistence yet.
```

### Third recommended GitHub task

```text
Implement the Initial Comprehensive RN Assessment form flow for one pilot system, Respiratory, including explicit situation selection, baseline evidence, intervention, follow-up, limitation handling, draft save contract, exception generation, and tests. Do not implement AI in this task.
```

### Fourth recommended GitHub task

```text
Implement Integumentary as a specialized system extension: skin condition, impairment selection, multiple wound records, visual location aid, wound legal-record fields, Braden subscales with derived total, interventions, follow-up, exceptions, and tests. Edema must not be reassessed here.
```

---

## 20. Unresolved Inputs Required Before Production Completion

- Confirm actual repository stack and package versions.
- Confirm database schema and migration framework.
- Approve full clinical field inventory for all ten systems.
- Approve which exceptions block record, signature, or neither.
- Confirm role/permission matrix.
- Confirm signature and addendum behavior.
- Confirm HOPE field mapping and effective specification separately.
- Confirm accessibility target and supported browsers/devices.
- Confirm retention, audit export, and correction requirements.
- Validate workflow timing through usability testing before making performance claims.

---

## 21. Regulatory/Clinical Design Basis

This engineering specification treats baseline, follow-up, progression, current observations, and dated evidence as distinct record concepts. It also preserves clinician judgment and avoids converting historical or inferred information into current findings. Regulatory and payer rules must remain versioned, source-linked configuration or policy modules rather than being scattered as unexplained JSX conditions.
