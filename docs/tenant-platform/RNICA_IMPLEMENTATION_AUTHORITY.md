# RNICA Implementation Authority

STATUS: RNICA WORKFLOW AND DESIGN ARE FUNCTIONALLY COMPLETE.
REDESIGN: PAUSED. DO NOT CONTINUE DESIGN WORK ON THIS TRACK.
PURPOSE: ENABLE ENGINEERING IMPLEMENTATION WITHOUT DESIGN INTERPRETATION.

This is the master index for the RNICA implementation authority package.
It does not replace or reopen any prior document. It tells an engineer
exactly which document answers which implementation question, in what
order to read them, and what is and is not authorized right now.

## Document Set (read in this order)

1. **`RNICA_IMPLEMENTATION_AUTHORITY.md`** (this document) — index, ground
   rules, definition of "implementation-ready," and what remains blocked.
2. **`RNICA_SCREEN_AUTHORITY_MATRIX.md`** — per-screen field inventory:
   exact field, type, required/optional, source component, and screen
   placement, for all 13 RNICA screens. Answers "what does engineering
   build on each screen."
3. **`RNICA_DATA_MAPPING_MATRIX.md`** — field → API endpoint → backend
   model/column mapping. Answers "where does each field read from and
   write to."
4. **`RNICA_AI_GOVERNANCE.md`** — consolidated AI/Intelligence rules:
   what the RNICA rules engine may and may not do, refresh triggers,
   consumer boundaries. Answers "what can AI code do here."
5. **`RNICA_LOCK_READINESS_MATRIX.md`** — consolidated hard-blocker/
   warning matrix for Finalization and Lock. Answers "what must be true
   before Lock succeeds."

## Upstream documents this package implements (not reopened)

- `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` — the approved 13-screen Figma
  design authority.
- `RNICA_SCREEN_BY_SCREEN_EVIDENCE_MATRIX.md` — evidence traceability
  per screen.
- `RNICA_WORKFLOW_AUTHORITY_MAP.md` — entry/exit/failure-path authority
  per screen.
- `PATIENT_CHART_AUTHORITY_MAP.md` — chart-wide ownership/consumer
  boundaries (Patient Chart workflow redesign remains paused until this
  package is complete, per Owner instruction).
- `RNICA_CLINICAL_NARRATIVE_FINAL_DECISION.md`,
  `RNICA_LOCK_DEFECT_UNREACHABLE_NARRATIVE_REVIEW.md`,
  `RNICA_CLINICAL_NARRATIVE_REWIRING_MAP.md` — Clinical Narrative
  authority, referenced by screens 5 and 13.

## Authority Legend (unchanged, same seven labels)

- **[REPOSITORY-DISCOVERED]** Proven current field, behavior, model,
  endpoint, or validation rule, cited to a specific file.
- **[LOCKED PRODUCT DECISION]** Approved future-state decision.
- **[REGULATORY / CLINICAL AUTHORITY]** Controlling CMS/HOPE/LCD
  requirement.
- **[DESIGN REQUIREMENT]** Presentation/interaction requirement already
  approved in the Source of Truth package.
- **[FUTURE PRODUCT DIRECTION]** Not in scope for this implementation
  pass.
- **[NOT BUILT / NOT CONNECTED]** Explicit non-finding.
- **[OPEN DEFECT]** Existing defect, tracked separately, not repaired by
  this package.
- **[IMPLEMENTATION DISCOVERY REQUIRED]** New for this package. Marks a
  cell where the design intent is settled but the exact backend
  field/endpoint/column has not yet been verified against current code
  at the time of writing. Engineering must confirm before building —
  this label is a flag to verify, not permission to guess.

## What "Implementation-Ready" Means Here

A screen, field, or rule is implementation-ready when all of the
following are true:

1. Its Figma requirement is recorded in `RNICA_REDESIGN_SOURCE_OF_TRUTH.md`.
2. Its underlying data source is either confirmed
   **[REPOSITORY-DISCOVERED]** in `RNICA_DATA_MAPPING_MATRIX.md`, or
   explicitly flagged **[IMPLEMENTATION DISCOVERY REQUIRED]** with a
   named verification task.
3. Its validation/compliance behavior is recorded in
   `RNICA_LOCK_READINESS_MATRIX.md` (if it participates in Finalization/
   Lock) or explicitly marked not lock-relevant.
4. Any AI/advisory content it displays is bounded by
   `RNICA_AI_GOVERNANCE.md`.

A screen is **not** implementation-ready if any of the above is missing
— engineering should not interpret or invent behavior to fill the gap;
it should be raised as a discovery task instead.

## Scope Boundary (restated)

- **CODE: BLOCKED. SCHEMA: BLOCKED. MIGRATIONS: BLOCKED** — this package
  is documentation only. It authorizes precise, low-ambiguity
  implementation planning; it does not authorize writing or merging
  code.
- Patient Chart Navigation redesign (`PATIENT_CHART_AUTHORITY_MAP.md`
  scope) remains paused until this 5-document package is reviewed and
  approved, per this instruction.
- None of `RNICA_REDESIGN_SOURCE_OF_TRUTH.md`,
  `RNICA_SCREEN_BY_SCREEN_EVIDENCE_MATRIX.md`,
  `RNICA_WORKFLOW_AUTHORITY_MAP.md`, or `PATIENT_CHART_AUTHORITY_MAP.md`
  are reopened by this package.

## Screenshot Evidence Note

The five RNICA screenshots reviewed alongside this instruction (Finalize/
Lock readiness checklist, Diagnosis & LCD, AI Action Center, Functional
Status, Patient Story) are **[REPOSITORY-DISCOVERED, current build
evidence]** — they show a working v2.2/v3.2 build already implementing
much of the approved 13-screen design (Patient Story, Evidence & Intake,
Functional Status, Pain & Symptom Burden, Diagnosis & LCD, Body Systems,
Caregiver & Support, Safety & Clinical Risk, ACP & Goals of Care, Orders
& POC, Compliance & Readiness, AI Action Center, Finalization all appear
as left-nav items). This package documents that existing build precisely
so remaining gaps can be closed without re-deriving design intent.

Two concrete confirmations from the screenshots, folded into the other
four documents:
- The Finalize screen's "Lock Assessment (Blocked)" button plus a
  "2 BLOCKING ISSUES DETECTED" panel (Pain Reassessment Required, SFV
  Assessment Missing) confirms Lock is a hard, itemized gate —
  consistent with `RNICA_LOCK_READINESS_MATRIX.md`.
- The AI Action Center screen's "AI analysis last refreshed... Note:
  updates on Load, Save, and Lock" banner and "Advisory Findings — For
  Clinician Review Only... AI does not generate narratives, definitive
  prognoses, or physician certifications" disclaimer are direct,
  in-product confirmation of the refresh-trigger and advisory-only rules
  already locked in `RNICA_AI_GOVERNANCE.md` below.

## Change Control

Any future change to the four companion documents in this package must:
1. Cite the specific repository file/line or screenshot evidence.
2. Use the authority legend above — no unlabeled claims.
3. Not alter any Locked Product Decision already recorded in
   `RNICA_REDESIGN_SOURCE_OF_TRUTH.md` without a new, explicit Owner
   decision.
