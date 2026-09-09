# Certification Monitor — Design Spec

Date: 2026-09-08
Branch: `feature/production-hnp-clinical-runtime`

**Design only — nothing in this document has been implemented.**

## What data exists today

| Data point | Exists? | Source |
|---|---|---|
| Current certification (finalized flag) | YES | Checked by `_has_finalized_certification` in `billing_readiness_service.py` |
| Recert due date | YES | `BenefitPeriod.end_date` (current period) |
| Recert overdue | YES (derivable) | `daysUntil(end_date) <= 0`, already rendered distinctly (red) in `PocCertificationPage.tsx` |
| Expiring this week | PARTIAL | Current window is 14 days, not a calendar-week boundary — same data, different threshold |
| Expiring next 30 days | NO | Not found; only the 14-day window exists today |
| Missing signature | UNKNOWN | Not confirmed this pass whether a "signed vs. unsigned" state is tracked separately from "finalized" |
| Missing physician | UNKNOWN | Physician association to certification not re-verified this pass |
| Missing medical director | UNKNOWN | Same |
| Certification risk (composite score) | NO | No scoring/composite concept exists; today it's binary (has a finalized cert or does not) |

## What calculations exist today

- `daysUntil(benefit_period.end_date)` — the only calculation found,
  computed client-side in `PocCertificationPage.tsx`.
- `_has_finalized_certification` — a boolean gate, not a calculation.

## What UI exists today

`PocCertificationPage.tsx` — "POC Expiring Soon" metric card + sorted
list of periods expiring within 14 days, red for overdue. This is the
entire certification-monitoring UI surface found this pass.

## What reporting exists today

None beyond the one screen above — it doubles as the report.

## What is missing (the actual spec)

A real Certification Monitor, if built, would need to add — not
replace — the existing 14-day view:

1. **Configurable windows**: this-week / 30-day / custom, rather than a
   hardcoded 14 days.
2. **Missing-signature / missing-physician / missing-medical-director**
   states — requires first confirming (not assumed) whether the
   underlying certification model even distinguishes these states today;
   this is a prerequisite investigation, not yet done.
3. **Certification Risk** as an explained composite (e.g. "overdue AND
   missing physician" = higher risk than "expiring in 10 days, fully
   signed") — must show its reasoning, per the project's explicit
   "AI must explain, not decide" principle; this is not a black-box score.
4. A **push/proactive alert** channel (today's red/amber coloring is
   passive — a user must open the screen to see it).

## Inputs / Rules / Dependencies (for future implementation, not built)

- **Inputs**: `BenefitPeriod.end_date`, `BenefitPeriod.is_current`,
  certification finalization flag, (unconfirmed) physician/medical
  director association fields.
- **Rules**: date-window thresholds (config-driven, not hardcoded);
  overdue = `end_date < today`; the risk-composite rule would need to be
  written and reviewed before any implementation, not invented ad hoc.
- **Dependencies**: `billing_readiness_service.py` for the finalized-cert
  check; `BenefitPeriod` table for dates; whatever certification table
  holds signature/physician fields (not yet located this pass).

## Not built. Awaiting go-ahead per explicit instruction.
