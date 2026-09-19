# Anti-HospiceMD Design Rules — SNS Hospice Solutions

## Status

**LOCKED.** **IMPLEMENTATION AUTHORIZATION BLOCKER.**

These rules apply to: Figma, Tenant Platform, future UI designs,
GitHub implementation, design reviews, and acceptance reviews. They
govern the (separate, not-yet-started) Tenant Platform Redesign
referenced as an Implementation Authorization blocker in
`docs/biller-platform/IMPLEMENTATION_AUTHORIZATION_PACKAGE.md`. This
document only records the rules; it does not perform, plan, or
authorize any redesign, schema, migration, code, API, or UI work.

---

## Rule 1 — No Screen-by-Screen Recreation

**PROHIBITED:** creating SNS screens by copying HospiceMD layout,
navigation, workflow, dashboard structure, or patient chart structure
— even if colors, fonts, and labels change. A visual repaint is not
sufficient.

## Rule 2 — Workflow First

SNS must be designed around hospice, clinical, compliance, billing,
and AI workflows — not around the layout of an existing EMR.

## Rule 3 — AI-First Design

Every major tenant workflow must evaluate: what the user is trying to
accomplish; what evidence is required; what AI can assist with; what
validation can occur before completion. HospiceMD-style data entry
screens are not the target state.

## Rule 4 — No Patient Chart Clone

**PROHIBITED:** reproducing a HospiceMD-style chart hierarchy. SNS
chart structure must be organized around Patient Story, Care Journey,
Evidence, Compliance, Workflow State, and Billing Readiness — not
simply document categories.

## Rule 5 — No Left-Nav Mirroring

**PROHIBITED:** using the same navigation architecture as HospiceMD.
SNS navigation must be justified by workflow efficiency, user role,
operational need, and AI assistance. Every navigation section must
have a documented purpose.

## Rule 6 — Dashboard Must Be Different

**PROHIBITED:** dashboards focused primarily on census numbers, static
widgets, or legacy administrative summaries. SNS dashboards should
focus on action required, readiness, risk, evidence gaps, compliance
issues, and AI guidance.

## Rule 7 — No Copy of Patient List

**PROHIBITED:** replicating HospiceMD patient-table layouts. SNS
patient workspace should prioritize current status, clinical risk,
documentation readiness, billing readiness, next action, and AI
recommendations.

## Rule 8 — Nurse-First Design

All workflows should answer "What does the nurse need right now?" —
not "What did HospiceMD do?" The nurse experience is the design
authority.

## Rule 9 — Billing Visibility

Billing must be integrated naturally; avoid separate disconnected
billing worlds. The tenant should understand readiness, missing
evidence, authorization requirements, and contracting risks without
leaving workflow context.

## Rule 10 — Evidence-First

Every major decision should trace to source document, review status,
verification status, and audit history. UI should expose evidence
before conclusions.

## Rule 11 — Compliance-First

Every workflow must support traceability, auditability, reviewability,
and historical preservation. Compliance should be embedded in UX.

## Rule 12 — No Competitor Terminology Reuse

Avoid inheriting competitor terminology simply because users are
familiar with it. Each label must be justified by hospice workflow,
regulatory requirement, or SNS architecture.

## Rule 13 — Distinct Information Architecture

Every major SNS area must have a documented purpose. Figma must
justify navigation, workspaces, dashboards, patient views, clinical
views, and billing views. "Because HospiceMD does it" is not an
accepted rationale.

## Rule 14 — Older Nurse Usability

All workflows must be reviewed for minimal clicks, clear wording,
visibility, cognitive load, and mobile usability. The target user is
not a software engineer.

## Rule 15 — GitHub Implementation Rule

GitHub may not use HospiceMD screenshots, layouts, navigation, or
workflow structure as implementation authority. **Implementation
authority is approved SNS Figma only.**

---

## Implementation Authorization Blocker (Tenant Platform Redesign)

Implementation Authorization may not be approved until:

- ☐ Tenant navigation redesigned
- ☐ Dashboard redesigned
- ☐ Patient workspace redesigned
- ☐ Intake workflow redesigned
- ☐ Clinical workflow redesigned
- ☐ AI workflow redesigned
- ☐ Dark theme reviewed
- ☐ Light theme reviewed
- ☐ Anti-HospiceMD review completed
- ☐ Figma approved

This is the current, locked version of the Tenant Platform Redesign
blocker checklist, superseding the checklist previously recorded in
`IMPLEMENTATION_AUTHORIZATION_PACKAGE.md`. No item above has been
started, verified, or completed by this document.

## Final Test

Ask: *"If HospiceMD disappeared tomorrow, would SNS still look and
feel like SNS?"*

The answer must be **YES**. If the answer is **NO**, tenant redesign
is not complete.

---

## Status Summary

All 15 rules and the Implementation Authorization blocker checklist
recorded as **LOCKED** reference material for all future Figma,
Tenant Platform, GitHub implementation, design review, and acceptance
review work. **No redesign work, schema, migration, code, API, or UI
change is performed or authorized by this document.**

**IMPLEMENTATION REMAINS BLOCKED.**
