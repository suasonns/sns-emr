# Payer Reimbursement Matrix (Phase 30)

Status: research comparison. No production code changed. No billing feature or AI built. Sources: 42
CFR Part 418 (traditional Medicare), CMS VBID hospice-carve-in wind-down guidance (Medicare Advantage),
general commercial-payer hospice practice (no CMS-equivalent regulatory floor exists for PPO/commercial
— documented as such, not invented).

| Dimension | Medicare FFS | Medicare Advantage (current, post-1/1/2025) | Commercial PPO | Managed Care (commercial HMO) |
|---|---|---|---|---|
| Election | Signed election statement (42 CFR 418.24); mandatory addendum furnished within 5 days as of 10/1/2026 | **Identical to Medicare FFS** — the VBID hospice carve-in ended 12/31/2024; MA beneficiaries electing hospice are now billed exactly as traditional Medicare | Payer-defined equivalent; no CMS form or timing floor applies | Payer-defined equivalent; often modeled on Medicare's election concept contractually but not legally required to match it |
| Certification | Physician-signed, ≤6-month prognosis, timing windows per 42 CFR 418.22 | Identical to Medicare FFS | Payer-specific; commonly requires a physician certification but timing/format is a contract term | Payer-specific |
| Recertification | Face-to-face required for BP3+, 30-day pre-recert window | Identical to Medicare FFS | Payer-specific, may not use the 90/90/60 structure at all | Payer-specific |
| Authorization | Not applicable — Medicare hospice election itself is the authorization; no separate prior-auth step exists in the regulation | Not applicable (post-2025, reverted to FFS treatment) | **Commonly required** — commercial/PPO plans frequently require prior authorization for hospice admission and/or periodic re-authorization, a step that does not exist in Medicare's model at all | **Commonly required**, often more stringent than PPO (referral/gatekeeper models) |
| NOE | Required, 5-calendar-day filing/acceptance window, OSC 77 penalty for late filing | Required, billed to the MAC exactly as FFS (post-2025) | **Not applicable** — no NOE concept exists for commercial payers; there is no CMS-equivalent notice requirement | Not applicable |
| Claim | Submitted to MAC | Submitted to MAC (post-2025, not the MA plan) | Submitted per payer contract/portal, format and timely-filing windows vary by payer | Submitted per payer contract/portal |
| Payment | CMS hospice per-diem rates by level of care, per benefit period | Identical to Medicare FFS rates/structure (post-2025) | Negotiated contract rate; may be per-diem, case rate, or otherwise | Negotiated contract rate, often bundled/capitated arrangements possible |
| Denial Risk | Missing/late certification, late NOE (financial liability not just denial), F2F non-compliance, benefit-period sequencing errors | Identical risk profile to Medicare FFS (post-2025) | Missing prior authorization, payer-specific documentation not matching Medicare's format (if a payer expects Medicare-style docs but SNS's evidence doesn't map cleanly) | Same as PPO, often compounded by stricter authorization/referral requirements |
| Audit Risk | MAC/ZPIC/UPIC review of the full clinical + billing record; CDPH survey (facility-level, not payer-specific) | Identical to Medicare FFS (post-2025); no separate MA-specific audit body remains relevant for hospice specifically | Payer-specific audit/recoupment rights per contract; less standardized than Medicare | Same as PPO |

## Key conclusions

1. **Medicare Advantage hospice billing is not operationally distinct from Medicare FFS today.** The
   VBID hospice carve-in — the only mechanism that ever made MA hospice billing different — ended
   12/31/2024. Any engineering effort framed as "build MA-specific hospice billing" should be dropped;
   the correct target is simply "Medicare FFS-correct billing," which already covers MA beneficiaries
   electing hospice today.
2. **The single largest real operational difference in this matrix is Authorization** — Medicare has no
   prior-authorization step for hospice election at all (election itself is dispositive), while
   commercial PPO and managed-care/HMO payers commonly do. SNS's confirmed payer-agnostic
   `payer`/`payer_sequence` infrastructure in billing-readiness is architecturally correct groundwork
   for this, but no payer-specific authorization-tracking rule configuration was found to exist — this
   is the most actionable, evidence-grounded item in this matrix for future payer-specific work, though
   it remains a real but non-urgent gap relative to the certification-gating and election-addendum
   findings.
3. **NOE is a Medicare-only concept.** Any commercial/PPO/managed-care billing-readiness logic that
   assumes an NOE-equivalent exists for those payers would be a modeling error; this matrix confirms
   NOE should remain scoped to Medicare (and MA, since MA now bills as Medicare) only.
4. Commercial/managed-care denial and audit risk is real but governed by individual payer contracts,
   not a CMS regulatory floor — SNS cannot build a single universal "commercial compliance" check the
   way it can for Medicare; any future work here would need to be payer-configuration-driven, not a
   fixed rule set.

No production code has changed. No billing feature or AI has been built.
