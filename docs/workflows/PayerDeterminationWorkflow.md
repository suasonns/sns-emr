# Payer Determination Workflow

**Status:** Business-rule specification, part of the permanent
`docs/workflows/` documentation set. Companion to `BenefitPeriodWorkflow.md`
and `DocumentHarvestMapping.md`.

## Purpose

Document how a patient's payer is identified and confirmed, why OCR must never
decide the downstream workflow branch, and why an Explanation of Benefits (EOB)
is frequently the real source of truth rather than any point-in-time
eligibility check.

## The workflow map

```
Unknown Payer
   |
   v
Document Upload (insurance card, HNP, transfer packet, referral documents)
   |
   v
OCR Harvest (suggests candidate payer name/type — a FACT, not a determination)
   |
   v
Eligibility Verification (270/271 check or manual verification — performed
outside SNS EMR via a payer portal, clearinghouse, or phone; the result is
uploaded as evidence)
   |
   v
Payer Confirmed (staff reviews harvested candidate + eligibility evidence, confirms)
   |
   v
Branch:
   -> Medicare                         (see BenefitPeriodWorkflow.md)
   -> HMO / PPO / Commercial            (see AuthorizationWorkflow.md)
```

## Why OCR does not determine the payer workflow branch

OCR/AI extraction may identify a payer *name* on a document (e.g. "Medicare",
"Blue Shield HMO") and populate it as a candidate value with a confidence
score. That is a fact-harvesting operation, no different from harvesting an
MBI or policy number (see `DocumentHarvestMapping.md`).

**Choosing which downstream workflow branch to run (Medicare benefit-period
review vs. HMO/PPO contracted/authorization review) is a staff decision, not an
OCR decision**, for the same reasons benefit period itself is never automated:

- A document may reference multiple payers (e.g. a prior primary payer plus a
  new payer after a mid-episode change) and OCR has no reliable way to know
  which one is currently financially responsible.
- A payer name string alone does not tell you whether the plan is a Medicare
  Advantage (HMO) plan billed like Medicare vs. billed like a commercial HMO —
  that determination has real claims-routing consequences and must be
  confirmed by staff, consistent with the facesheet's own warning banner:
  *"Per Authorization or Eligibility, only enter the Payer that is financially
  responsible. The claim will be submitted to this Payer only."*
- OCR confidence scores reflect text-recognition confidence, not
  claims-eligibility confidence — they are not a substitute for a verified
  eligibility response.

## Why the Explanation of Benefits (EOB) is often the real source of truth

A payer name harvested from an intake document, or even a real-time
eligibility (270/271) response, reflects what the payer's system *currently*
believes about coverage — which, as documented in `BenefitPeriodWorkflow.md`,
can be incomplete or stale in transfer scenarios (e.g. the sending hospice has
not yet billed, so the receiving hospice's eligibility check may not reflect
the true benefit-period state). An **Explanation of Benefits** received after a
claim has actually been adjudicated is frequently the first document that
confirms, after the fact, what benefit period/cert sequence a payer actually
recognized. This is why:

- Eligibility verification results are treated as *evidence to upload and
  review*, not as an automatic determination.
- Staff must be able to correct a payer determination later if an EOB
  contradicts the earlier eligibility check.
- The Payer Determination workflow never "locks in" silently — it is always a
  staff-reviewed, staff-confirmed step, exactly like Benefit Period.

## Summary rule

Readiness and downstream workflows must consume the **staff-confirmed payer**,
never the raw OCR-harvested payer name and never an unreviewed eligibility
response. See `ReadinessConsumptionMap.md` for the full consumption rules.

## Insurance verification boundary

SNS EMR is not an eligibility-verification system. It has no NGS Connex, CMS,
Medicare, or payer-database lookup integration, and no automated
name+DOB+SSN insurance-discovery capability — that is explicitly out of
scope. Insurance verification is performed outside SNS EMR (NGS Connex,
Availity, other payer portals, phone). SNS stores and audits reviewed results
and supporting evidence — recorded on `PatientFaceSheet` as
`payer_verified_date`, `payer_verified_by` (always server-stamped from the
acting user, never client-supplied), `payer_verification_notes`, and
`verification_document_reference` (pointing to an uploaded verification
document classified under `ELIGIBILITY_VERIFICATION`, `MEDICARE_VERIFICATION`,
`MEDICAID_VERIFICATION`, `COMMERCIAL_PAYER_VERIFICATION`, `INSURANCE_CARD`,
`PAYER_SCREENSHOT`, or `OTHER_INSURANCE_EVIDENCE`).
