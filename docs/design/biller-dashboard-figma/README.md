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

**RESOLVED 2026-08-24**: user decided to keep **both**. `BillerShell.tsx` nav keeps the existing
"Billing Readiness" item (still routes to `/billing/dashboard` today, pending a real dedicated
readiness page) and adds `Settings` as an 11th item, backed by a `ComingSoonPage` placeholder route
(`/billing/settings`) since there is no real settings backend yet. This intentionally does not
match the 10-item Figma screenshot exactly — that is an approved deviation, not an oversight.

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
  Remaining (Days). **Implemented 2026-08-24**: `NoeTrackingPage.tsx` now shows this layout —
  the table's "Election Date" and "Due Date" columns are derived from the real
  `election_date` field plus the true 42 CFR 418.24(b) 5-calendar-day rule (not the mockup's
  "Admit Date" framing, since the backend's actual filing clock starts at election, not
  admission); `noe_submitted_date` maps to "Filed Date"; a computed `remaining` days value
  drives Approaching/Overdue/Filed/Late/Exempt/Data-gap status chips honestly rather than
  fabricating the mockup's exact bucket boundaries.

## Rebuild pass (2026-08-24) — corrected drift from an ad hoc self-designed shell

The first implementation pass of `BillerShell.tsx` and its 3 real-data pages diverged
significantly from this Figma reference (plain nav with no icons, light page background
instead of dark navy throughout, no page-header action buttons, no metric-card rows, generic
table layouts). This was flagged and corrected: the shell and all 3 pages
(`VisitsNotesPage.tsx`, `PocCertificationPage.tsx`, `NoeTrackingPage.tsx`) were rebuilt against
the actual screenshots in this folder, using new shared components
(`components/billing/PageHeader.tsx`, `MetricCardRow.tsx`, `HipaaBanner.tsx`) so future pages
(Claims, Denials & Appeals, Eligibility, Payment Posting, Reports) can be built consistently
once their backend data exists, instead of drifting again.

**Dashboard page also rebuilt (2026-08-24)**: `/billing/dashboard` previously rendered the
older, unrelated `pages/BillingDashboard.tsx` (a 14-tab report browser used by `/analytics`,
predating this Figma work). That component is untouched and still serves `/analytics`; a new
`pages/billing/BillingOverviewPage.tsx` now serves `/billing/dashboard` instead, matching
`11-full-sidebar-dashboard-visits-poc.png`'s Dashboard panel: 4 metric cards (Total Patients /
Ready to Bill / Blockers Outstanding / Clean Claim Rate, the last computed from real
accepted/denied claim-lifecycle counts), a "Blocker Breakdown by Unresolved Flag" panel (client
categorizes the real per-patient blocker strings from `/billing/readiness-report` using the
same category prefixes as `billing_readiness_service.categorize_blocker`), and an "Active
Billing Batch Lifecycle Stages" 4-card row mapped directly from the real claim-lifecycle
ready/sent/accepted/paid counts. **One deviation**: the mockup's "Readiness Compared by
Associated Agency" panel is a cross-agency comparison table, but that data is only exposed by
an owner-only endpoint (`GET /api/dashboard/billing-readiness`) — a billing-role user viewing
one agency at a time has no legitimate access to every other agency's readiness numbers. That
panel was replaced with a "Claims Lifecycle Snapshot" for the selected agency instead of
fabricating cross-agency numbers or exposing data outside the current tenant scope.

## Known open items (do not silently resolve — ask the user)

1. ~~Sidebar nav: "Billing Readiness" vs. "Settings" as the 10th item~~ — **resolved 2026-08-24**:
   user chose to keep both (11 items total), see above.
2. ~~Page-level "Export Audit Logs" / "Sync Clearinghouse" action buttons~~ — **resolved
   2026-08-24**: added via the shared `PageHeader` component to all 3 real-data pages, default
   behavior (no backend for these two actions yet, so they are currently inert — no onClick
   handler is wired until an export/sync endpoint exists).
3. ~~NOE Tracking page layout (alert banner, 4-metric layout, 5-Day Filing Rules panel)~~ —
   **resolved 2026-08-24**, see above.
4. HIPAA banner exact copy/color is inconsistent across the Figma screenshots themselves — we
   standardized on the amber "MINIMUM DATA PRINCIPLE ACCESS" left-border variant (shared
   `HipaaBanner.tsx` component) as canonical across all billing pages.
