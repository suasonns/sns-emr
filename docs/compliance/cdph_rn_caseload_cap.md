# CDPH RN/LVN Caseload Cap — 12 Patients Per Licensed Nurse
SNS Hospice EMR — persistent compliance rule reference

## Purpose
This document records a standing business/regulatory rule so it is never
lost between sessions or treated as a "new" instruction. If this rule is
referenced again in the future, update this file rather than re-deriving
it from scratch.

## The rule
> **A licensed nurse must be assigned 12 or fewer patients.**

- **Regulator:** CDPH (California Department of Public Health)
- **Citation:** DPH-18-002E, *Hospice Agencies*, Article 3 — Services,
  **Section 74848. Nursing**, subdivision (b).
- **Exact text (subdivision (b)):** "A licensed nurse must be assigned 12
  or fewer patients. For the purposes of this section 'licensed nurse'
  means either a registered nurse or a licensed vocational nurse, and
  'assigned' means the licensed nurse has primary responsibility for the
  provision of care to a particular patient within their scope of
  practice."
- **Scope:** Applies per licensed nurse (RN or LVN) **per hospice
  agency/tenant** — i.e. the cap is on how many patients that nurse has
  primary-care assignment for at that specific agency, not a platform-wide
  total across every agency they may have an account in.
- **Related, not the same rule:** subdivision (d) of the same section
  clarifies only nurses employed by or contracted with the hospice and
  assigned to direct patient care count toward the nurse-to-patient ratio.
  Subdivisions (f)–(i) additionally require a documented "patient acuity
  system" governing when *additional* personnel (aides, volunteers, etc.)
  must be assigned in excess of the prescribed ratio — that acuity system
  is a separate, broader staffing methodology and does not raise or lower
  the hard 12-patient primary-assignment cap itself.

## Status in this codebase
As of this writing this is a **documented rule only** — there is no
enforcement yet. `StaffAssignment.jsx` currently displays a `caseload`
number per staff member as read-only mock data with no cap check (some
mock entries already show caseloads above 12, which is inaccurate to this
rule and should not be treated as sanctioned).

## Planned enforcement (not yet built)
When enforcement is implemented, it should:
1. Count active patients where a given `User` (role RN or LVN) is the
   **primary** assigned licensed nurse, scoped to that user's `tenant_id`
   (their agency) — not summed across other agencies via the cross-agency
   identity-linking feature.
2. Block (or clearly warn, per product decision) new primary-nurse
   assignments that would push that count above 12 for the target agency.
3. Surface the current caseload count next to the assignment UI
   (`StaffAssignment.jsx` and any staffing/roster views) so schedulers see
   the limit before assigning.

## Change log
- 2026-08-23 — Rule captured and documented per hospice agency owner
  direction; this is a re-statement of guidance already given in prior
  sessions, now persisted in the repo instead of only in chat history.
