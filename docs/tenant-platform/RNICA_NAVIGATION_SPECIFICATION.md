# RNICA Navigation Specification

**STATUS:** AUTHORITATIVE DESIGN INPUT. NOT IMPLEMENTATION AUTHORIZATION.
**CODE:** BLOCKED until an implementation task explicitly cites this
document as authorization.

Companion document to `RNICA_WORKFLOW_AUTHORITY_MAP.md`,
`RNICA_SCREEN_AUTHORITY_MATRIX.md`, and `RNICA_REDESIGN_SOURCE_OF_TRUTH.md`.
Those documents establish Screen Authority, Workflow Authority, and Evidence
Authority. This document establishes **Navigation Authority**: the
canonical screen order and which navigation system owns which concern.

## 1. Canonical RNICA Workflow Order (supersedes prior numbering)

**[PRODUCT-AUTHORITY DECISION — 2026-09-22]** This is the approved order,
not a suggestion:

1. Patient Story
2. Evidence & Intake
3. Diagnosis & LCD
4. Pain & Symptom Burden
5. Functional Status
6. Body Systems
7. Caregiver & Support
8. Safety & Clinical Risk
9. ACP & Goals of Care
10. Orders & POC
11. Compliance & Readiness
12. AI Action Center
13. Finalization

**Rationale:** Diagnosis provides context for all downstream assessment;
symptom burden is evaluated before deeper functional assessment; functional
interpretation depends on diagnosis and symptom context. This mirrors the
hospice nursing thought process.

**Non-linear navigation remains permitted.** Per
`RNICA_WORKFLOW_AUTHORITY_MAP.md`, this is the recommended default nurse
path, not a forced linear gate. The server does not enforce a
section-completion order; Finalization/Lock readiness checks are the only
enforced gate, evaluated regardless of navigation order.

## 2. Navigation Ownership

Two distinct navigation concerns exist and must remain visually and
architecturally separate:

- **Patient Chart Navigation** — global, cross-module navigation between
  chart areas (Facesheet, Care Overview, Intake & Admission, Nursing
  Assessment, Visits, Orders, Medications, Physician Orders, etc.). Owned
  by the chart shell (e.g. `PatientChartSidebar`), not by RNICA.
- **RNICA Workflow Navigation** — navigation between the 13 RNICA screens
  once Nursing Assessment/RNICA is active. Owned exclusively by the RNICA
  workspace shell (`RnicaScreenShell` in
  `sns-emr-frontend/src/components/rn-ica/RNICACommandWorkspace.jsx`).

**[REPOSITORY-DISCOVERED — 2026-09-22]** Today, `/rnica` is a standalone
top-level route (`App.tsx`), not nested inside `PatientChart`/
`PatientChartSidebar`. The two navigation systems therefore do not
currently render simultaneously on screen. If/when RNICA is nested inside
the chart shell, this section governs how the two navigation layers must
remain visually distinguishable (the user must always know whether a
control changes chart context or assessment workflow step).

## 3. RNICA Workflow Navigation Model

- Desktop: a dedicated RNICA workflow rail (not a horizontal tab bar),
  listing all 13 screens with index + active-state highlighting and
  progress/readiness indication. No horizontal scrolling for workflow
  navigation.
- Mobile: the rail collapses into a compact, always-visible "current
  screen" control that opens a full list (sheet/drawer) for quick
  navigation. No overflow.
- Screen switching remains in-memory state (`selectScreenTab`); no new
  per-screen routes are required by this document. If URL-addressable
  screens become a goal, that is a separate, later authorization.

## 4. Constraints Carried Forward (unchanged)

- Preserves 100% of existing clinical data, validation, HOPE mapping,
  readiness, Lock, amendment, and audit behavior. This document authorizes
  presentation/ordering changes only.
- shadcn/ui components are primitives only (`ScrollArea`, `Badge`,
  `Collapsible`/`Accordion`, `Sheet`), not a generated dashboard/nav
  system. SNS owns the workflow structure and branding.
