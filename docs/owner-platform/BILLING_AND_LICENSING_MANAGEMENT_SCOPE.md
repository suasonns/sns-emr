==================================================

BILLING & LICENSING MANAGEMENT

OWNER PLATFORM — SCOPE BOUNDARY

==================================================

PROBLEM

Billing & Licensing Management is drifting into Biller Platform
responsibilities.

==================================================

OWNER PLATFORM BILLING MUST ONLY ANSWER

==================================================

1. What agencies are subscribed?

2. What features are enabled?

3. What AI services are enabled?

4. What is being consumed?

5. What invoices are open?

6. What revenue-sharing agreements exist?

7. What does SNS earn?

==================================================

DO NOT BUILD

==================================================

- Claims

- Eligibility

- Authorization Tracking

- Aging Reports

- Collections

- Payment Posting

- EDI

- Cap Monitoring

These belong exclusively to the future Biller Platform.

==================================================

CURRENT PRIORITY

==================================================

Track subscriptions first.

Track feature enablement second.

Track consumption third.

Determine pricing later after sufficient production usage data exists.

---

## Status

Future Design Specification / Scope Boundary. **DO NOT IMPLEMENT UNTIL
APPROVED.** This document defines what Owner Platform "Billing &
Licensing Management" is and is not responsible for. No code, UI, or
data model changes are authorized by this document alone.

## Relationship to Other Documents

- Sharpens the boundary already stated in
  `docs/roadmap/Owner-Platform-Roadmap.md` ("Owner Platform Does Not
  Contain: ... Billing Operations, DDE Operations") — this document
  defines the narrow slice of billing (subscriptions, feature/AI
  enablement, consumption, invoices, revenue share, SNS earnings) that
  IS Owner Platform scope, distinct from revenue-cycle/claims
  operations.
- The "Do Not Build" list (Claims, Eligibility, Authorization Tracking,
  Aging Reports, Collections, Payment Posting, EDI, Cap Monitoring)
  belongs exclusively to the future Biller Platform per
  `docs/roadmap/Biller-Platform-Roadmap.md` (Batch Billing, Managed
  Billing, DDE Workflow Concepts, Revenue Cycle Vision, Eligibility
  Concepts, Claim Lifecycle Concepts) — any future work matching that
  list must be built there, not on the Owner Platform.
- The stated build order (subscriptions -> feature enablement ->
  consumption -> pricing determined later from production usage data)
  is the sequencing rule for this area going forward; it does not
  itself authorize starting that work.
- Revenue-sharing/what-SNS-earns concepts should be tracked as
  candidate entries in
  `docs/roadmap/Future-Ideas-And-Research.md` until pricing is
  determined, per that document's Date Added/Platform Area/Problem
  Being Solved/Expected Benefit/Status format.

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Document created — Billing & Licensing Management scope boundary for the Owner Platform: the 7 questions Owner Platform billing must answer (subscriptions, feature enablement, AI service enablement, consumption, open invoices, revenue-sharing agreements, SNS earnings), an explicit Do Not Build list reserved for the future Biller Platform (Claims, Eligibility, Authorization Tracking, Aging Reports, Collections, Payment Posting, EDI, Cap Monitoring), and the current build priority (subscriptions, then feature enablement, then consumption; pricing determined later from production usage data). |
