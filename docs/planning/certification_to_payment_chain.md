# Certification-to-Payment Chain (Phase 54)

Status: verification synthesis. No production code changed. No billing feature or AI built.

## Can SNS trace Certification → Benefit Period → Claim → Payment without inference?

**NO — one link requires inference; the rest are either direct or partially direct.**

| Link | Traceable without inference? | Evidence | Missing link (if any) |
|---|---|---|---|
| Certification exists for the patient | Yes | `Certification` row, `CertificationStatusEvent` history | None |
| Certification → Benefit Period (this specific certification authorized this specific benefit period) | **NO — must be inferred** | `Certification.benefit_period_id` is a real FK, so one *can* query "which certifications reference this benefit period," but this is a **reverse** lookup (certification points at benefit period), not a forward authorization record (nothing on `BenefitPeriod` records "created because of certification X"). If a benefit period has zero referencing certifications, that absence is directly visible; but if it has one, there is no record that the certification was checked *before* the benefit period was created versus a certification that happens to have been created afterward and simply reference the same period. Sequencing itself is not evidenced, only co-existence. | The missing link is a **causal/temporal record**, not the FK itself — the FK enables inference, it does not eliminate the need for it. |
| Benefit Period → Claim (this claim was generated against this specific, validly-gated benefit period) | Partial | Claims reference a benefit period (implied by the billing pipeline's use of `benefit_period_id` in billing-readiness checks, confirmed in prior segments); whether every `Claim` row itself stores which benefit period it was generated against was not independently re-confirmed this pass | Flagged, not assumed compliant |
| Claim → Payment | Partial to unknown | 1 of 3 `Claim.status` writers is enforced/audited; the payment/remittance layer's own record integrity beyond the confirmed-fabricated 835 dashboard widget was not reconfirmed this engagement | Pre-existing, unchanged gap |

## Identified missing links (precise, not vague)

1. **No record that a certification check occurred at the moment a benefit period was created.** This
   is the single missing link that turns "Certification → Benefit Period" from a direct fact into an
   inference. Closing it requires exactly what the certification-gating fix (already scoped in the
   Hospice Reimbursement Chronology epic) would produce as a side effect: if `rollover_benefit_period`
   is changed to look up and require a valid certification before creating the period, the natural
   next step is to record *which* certification satisfied that check on the new `BenefitPeriod` row or
   its audit event — turning today's reverse-only FK into a forward, causal record.
2. **No confirmation, this engagement, of a direct `Claim.benefit_period_id` linkage independent of the
   billing-readiness computation.** Not proven to be missing — flagged as unconfirmed, to avoid
   overstating the gap.
3. **Claim/Payment audit gaps are pre-existing and already fully documented** (Phase 5/6) — repeated
   here only to complete the chain, not re-investigated.

No production code has changed. No billing feature or AI has been built.
