# SNS Hospice Solutions — External Billing Services (Biller's Dashboard) Figma Reference

Status: canonical visual reference for `sns-emr-frontend/src/components/billing/BillerShell.tsx`
and all `sns-emr-frontend/src/pages/billing/*` pages.

**Correction (2026-08-24): `docs/SNS_DESIGN_SYSTEM_1.0.md` is the single governing design system
for ALL SNS Hospice Solutions work — clinical modules AND the Biller's Dashboard/External Billing
Services portal. It is not scoped only to clinical charting**, despite its module list in §1 not
naming billing explicitly. Any Biller's Dashboard page must pass the "This is SNS" test in §1 of
that document and use its literal tokens (§3): font-size scale, font-weight scale, the exact
dark-mode hex color tokens (§3.5 — which already match this Figma reference's dark-navy/teal
palette: `bg #0f172a`, `card #1e293b`, `teal #10b7a2`), the Facesheet Card Standard (§7), the Bold
Text Policy (§4, bold reserved for the §6 Alert Hierarchy only), and the Color Policy (§5,
color communicates urgency only). This Figma reference below documents the Biller's Dashboard's
page-specific **layout/content** (sidebar nav, page structure, per-page metrics/tables/banners) —
it does NOT introduce a separate theme or override `SNS_DESIGN_SYSTEM_1.0.md`'s tokens. Where this
Figma reference and `SNS_DESIGN_SYSTEM_1.0.md` appear to conflict (e.g. a font size used in a
screenshot that isn't one of the 7 canonical tokens, or a bold/color usage outside the Alert
Hierarchy), `SNS_DESIGN_SYSTEM_1.0.md` wins.

These screenshots were originally shared as chat attachments only and were not persisted to the
repo, which caused the exact visual reference to be lost across a context compaction. They are
saved here so future sessions/agents always have the ground truth.

## Screenshots in this folder

| File | Page |
|---|---|
| `11-full-sidebar-dashboard-visits-poc.png` | **Most complete reference** — shows the full sidebar chrome (logo, Agency Context, nav, footer) alongside 3 stacked full pages: Dashboard, Visits & Notes Status, Plan of Care & Certifications |
| `10-billing-readiness.png` | Billing Readiness page (patient-level readiness detail + blocker breakdown) |
| `01-claims-management.png` | Claims Management |
| `02-billing-reports.png` | Billing Reports |
| `03-eligibility-verification.png` | Eligibility Verification |
| `04-payment-posting-simple.png` | Payment Posting (simple single-view variant — superseded by 07/09) |
| `05-noe-tracking.png` | NOE Tracking |
| `06-denials-appeals.png` | Denials & Appeals |
| `07-payment-posting-reconciliation-a.png`, `09-payment-posting-reconciliation-b.png` | Payment Posting & Reconciliation (tabbed variant — **canonical** design per checkpoint 130 reconciliation) |
| `08-edi-transaction-center.png` | EDI Transaction Center (orphaned page — folded into Claims/Payment Posting/Eligibility tabs, not a standalone nav item, per checkpoint 130) |

## Sidebar navigation (canonical — from `11-full-sidebar-dashboard-visits-poc.png`)

```
SNS Hospice Solutions
EXTERNAL BILLING SERVICES

AGENCY CONTEXT
[Agency Name — Agency #NNNN ▾]

Dashboard
Visits & Notes
POC & Certifications
Claims
Denials & Appeals
Eligibility
Payment Posting
NOE Tracking
Reports
Settings

(footer, pinned bottom)
External Billing Audit
HIPAA Audit Active
```

**IMPORTANT discrepancy vs. what was actually built** (`BillerShell.tsx`), found 2026-08-24:
the currently-implemented sidebar has a **"Billing Readiness"** nav item and **no "Settings"**
item — this doesn't match this reference. The most complete/authoritative screenshot
(`11-full-sidebar-dashboard-visits-poc.png`) shows `Dashboard` doubling as the billing-readiness
overview (its stat cards are Total Patients / Ready to Bill / Blockers Outstanding / Clean Claim
Rate — i.e. readiness data), with `Settings` as the 10th item instead. This needs to be resolved:
either (a) match this screenshot exactly (drop "Billing Readiness", add "Settings"), or (b) the
user confirms the earlier "Billing Readiness" nav item is still wanted and Settings should be
added as an 11th item. **Ask before changing** — do not silently guess.

Also note: the sidebar footer in this design reads "External Billing Audit / HIPAA Audit Active"
with no user avatar/sign-out control shown. The current implementation intentionally adds a user
avatar + "Sign out" menu per an explicit user instruction ("make sure there is sign in logout") —
that is a deliberate, approved deviation from this screenshot, not an oversight.

## Visual language (read from all screenshots)

- **Theme**: dark navy background/cards (`#0f172a`-ish page bg, `#1e293b`-ish card bg — same
  family as the clinical Facesheet dark tokens in `SNS_DESIGN_SYSTEM_1.0.md` §3.5, though this is
  a distinct component tree).
- **Accent**: teal/green (`#10b7a2`-ish) for primary buttons, active nav state, positive metrics,
  progress bars.
- **Status colors**: green = good/complete/paid, amber/orange = pending/attention, red = denied/
  overdue/error, blue = informational/in-transit — consistent with the Color Policy in
  `SNS_DESIGN_SYSTEM_1.0.md` §5 (urgency-only color use), even though this is a different theme.
- **Page header pattern** (every page): large page title (dimmed/ghosted style in mockups) +
  one-line subtitle description, with 1–2 action buttons top-right — one outlined secondary
  button (e.g. "Export ...", "Sync Clearinghouse") and one solid teal primary button (e.g. "New
  Report", "Batch Submission", "Run Batch Verification").
- **HIPAA / minimum-necessary banner**: present on every page, directly under the metric cards
  row or under the page header. Two banner color variants appear across screenshots — a teal/
  green box ("MINIMUM DATA VIEW" / "MINIMUM DATA PRINCIPLE") and an amber box with the same kind
  of copy. Exact copy varies slightly per screenshot but the concept is constant: billing staff
  only see administrative/status fields, never clinical narrative content.
- **Metric cards row**: 3–4 dark cards at the top of nearly every page, each with an uppercase
  label, a large colored number, and a one-line caption underneath.
- **Data tables**: dark zebra-free rows, uppercase column headers, colored status pill badges,
  pagination footer ("Showing X-Y of Z").
- **NOE Tracking specifics** (`05-noe-tracking.png`): a red alert banner above the metric cards
  when NOEs are approaching their deadline; 4 metric cards (Active NOEs / Filed On Time % / 
  Approaching Deadline / Late-Missed); a right-side "5-Day Filing Rules" panel with a 3-step
  timeline callout (Day 0 Admission → Days 1-4 compile → Day 5 deadline) and a compliance-rate
  progress bar; table columns are Patient ID / Admit Date / Due Date / Filed Date / Status /
  Remaining (Days). This does not fully match the currently-implemented NOE Tracking page (which
  uses Election Date/NOE Submitted/Non-Covered Days columns tied to the real
  `noe_penalty_service.py` calculation) — the backend's actual data model uses `election_date`
  and the 42 CFR 418.24(b) 5-calendar-day rule, so some relabeling (not a full rebuild) is likely
  the right reconciliation once the team decides how literally to follow this mockup.

## Known open items (do not silently resolve — ask the user)

1. Sidebar nav: "Billing Readiness" vs. "Settings" as the 10th item (see above).
2. Page-level "Export ..." / "Sync Clearinghouse" action buttons are not yet implemented on any
   of the 3 currently-real-data pages (Visits & Notes, POC & Certifications, NOE Tracking).
3. NOE Tracking page: add the approaching-deadline alert banner, the 4-metric layout, and the
   "5-Day Filing Rules" side panel to match `05-noe-tracking.png`.
4. HIPAA banner exact copy/color is inconsistent across the Figma screenshots themselves; pick one
   canonical version rather than matching per-page inconsistently.
