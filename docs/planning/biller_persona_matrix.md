# Biller Persona Matrix

Date: 2026-09-08
Branch: `feature/production-hnp-clinical-runtime`

Phase 10 required deliverable. Each question a real biller would ask,
answered by tracing to an actual screen/API/report — not by assuming one
exists.

| Question | Current Answer Exists? | Screen | API | Report | Gap |
|---|---|---|---|---|---|
| **Has NOE been submitted?** | **YES** | `NoeTrackingPage.tsx` | `GET /billing/noe-tracking` (`fetchNoeTracking`) | Same screen doubles as the report | None found — this is a real, wired capability |
| **Why is this patient not billable?** | **YES** | `BillingOverviewPage.tsx` (and referenced from `RNICACommandWorkspace.jsx`) | `check_patient_billing_readiness` via the billing-readiness endpoint (`app/billing/api/billing_router.py`) | Returns explicit, short blocker reason strings (e.g. missing finalized certification, missing attested F2F, missing physician-approved POC, ambiguous payer sequence, late NOE filing without exception reason) | Blocker categories are curated (`categorize_blocker`) — if a real-world blocker doesn't map to a known category it may render less specifically; not verified against every possible real-world scenario this pass |
| **What certifications expire this week?** | **YES (14-day window, not strictly "this week")** | `PocCertificationPage.tsx` — "POC Expiring Soon" metric + "Expiring cert periods in the next 14 days" list, sorted soonest-first, with overdue counts shown in red | `GET /billing/poc-certification-status` (`fetchPocCertificationStatus`) | Same screen | The window is hardcoded to 14 days, not a calendar-week boundary — close enough to answer the question in practice, but not an exact match to "this week" |
| **Has this claim been paid?** | **YES** | `BillingDashboard.tsx` claim list, filterable by status including `PAID` | `GET /billing/claims?status=PAID` (`list_claims`, `app/billing/api/claims_router.py`) | Same screen | Status can be **wrong** if the "Export to Excel" bug has silently reverted a PAID claim to SENT (see `claim_status_architecture.md`) — the screen will confidently show an incorrect answer in that case, which is worse than showing no answer |
| **What claims failed transmission?** | **NO** | None found | No `ClaimTransmission` model/endpoint exists at all (see `claim_status_architecture.md` §2) | None | **Real gap.** There is no concept of transmission failure in the system today — a claim is either not yet exported or has `claim_control_number`/`exported_at` set by the export action succeeding. There is no representation of "we tried to transmit and it failed." |
| **Which patients require recertification?** | **YES** | `PocCertificationPage.tsx` (same screen as the certification-expiration question — recertification need and certification expiration are the same underlying data in this system) | `GET /billing/poc-certification-status` | Same screen | None found beyond the 14-day-window caveat above |
| **What claims lack remittance?** | **NO** | None found | `Payment.match_status="UNMATCHED"` exists in the data model (see `payment_posting_architecture.md` step 6) but is not exposed on any screen or dedicated report endpoint found | None | **Real gap.** The backend correctly tracks unmatched payments so they aren't silently dropped, but nothing surfaces "claims sent but never remitted" or "payments that arrived but couldn't be matched" to a biller. This is a real, fixable, backend-data-already-exists gap — a good Phase-1-after-Thursday candidate. |

## Summary

**4 of 7** biller questions have a real, wired, live-data answer today
(NOE submitted, why not billable, certs expiring, who needs
recertification — noting the certs-expiring/recert-needed answers come
from the same single screen). **1 of 7** (has this claim been paid) has
a real answer that **can be silently wrong** due to the confirmed
Claim.status bug. **2 of 7** (failed transmission, lacking remittance)
have **no answer at all** — one because the underlying data model
doesn't exist yet (transmission), one because the data exists but isn't
surfaced (unmatched remittance).
