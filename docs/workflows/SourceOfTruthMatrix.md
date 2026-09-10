# Source of Truth Matrix

> Permanent reference. For every field involved in the Benefit Period /
> Admission / Eligibility workflow, this table states who or what owns the
> value, so no future developer has to rediscover it. See
> `docs/workflows/BenefitPeriodWorkflow.md`, `AdmissionTypesWorkflow.md`,
> `DocumentHarvestMapping.md`, `PayerDeterminationWorkflow.md`, and
> `AuthorizationWorkflow.md` for the full narratives this table summarizes.

| Field | Source of Truth | Automated? | Notes |
|---|---|---|---|
| Admit Type | Staff | No -- staff selects | Drives all downstream conditional requirements. Never inferred from OCR, Medicare, or prior data. |
| Starting Cert | Staff | No -- staff enters | Required for every admit type. Never defaulted to `1`. |
| Benefit Period (determination) | Staff | No -- staff enters | Staff review of eligibility/history produces the value; system only stores it. |
| Transfer Source | Staff (Transfer only) | No | Only collected/required when Admit Type = TRANSFER_FROM_ANOTHER_HOSPICE. Hidden otherwise. |
| Transfer Evidence | Staff (Transfer only) | No | Uploaded document; only required for Transfer admit type. |
| Certification Sequence | Staff | No | Derived forward-looking certification *schedule* may be system-calculated once Starting Cert/Benefit Period are staff-established -- but the initial sequence anchor is never system-derived. |
| SOC Date | Staff | No -- staff enters, system enforces gate | The system validates completeness before allowing SOC entry; it does not choose the date. |
| Medicare Number | OCR Candidate + Staff Review | Partial -- harvested with confidence score | A fact; may be auto-populated as a candidate value pending staff confirmation. |
| MBI | OCR Candidate + Staff Review | Partial | Same as Medicare Number. |
| Policy Number | OCR Candidate + Staff Review | Partial | Same. |
| Subscriber Information | OCR Candidate + Staff Review | Partial | Same. |
| Payer Name | Staff Reviewed | Partial (candidate) then staff-confirmed | Eligibility verification / EOB is the real source of truth, not OCR alone. |
| Payer Determination (Medicare vs HMO/PPO/Commercial) | Staff Reviewed | No | Confirmed via eligibility verification, not OCR guess. |
| Contracted Status | Staff Reviewed | No | Staff answers Yes/No/Unknown; stored, never inferred. |
| Authorization Required? | Staff Reviewed | No | Staff answers Yes/No/Unknown; stored, never inferred. |
| Authorization Evidence | Staff Uploaded | No | Required when Authorization Required = YES. |
| Non-Authorization Verification (`NON_AUTH_VERIFICATION`) | Staff Uploaded | No | Required when Authorization Required = NO, to prove the "no auth needed" determination was verified, not assumed. |
| Eligibility Verification Status | Staff Reviewed | No | Manual entry method is the default (`verification_method = MANUAL_ENTRY`); electronic responses are stored as evidence, not auto-applied. |
| Readiness Status (READY / AT RISK / NOT READY / BLOCKED) | System-Computed | Yes -- computed from reviewed data only | Consumes reviewed Payer, reviewed Eligibility, reviewed Authorization, reviewed Benefit Period, reviewed Starting Cert, reviewed Admit Type. Never consumes raw OCR/extraction output directly. |
| Future recertification schedule / reminders / tasks | System-Computed | Yes -- but only after the anchor exists | Requires staff to have already established Admit Type, Starting Cert, Benefit Period, SOC (and Transfer fields if applicable) first. |
| Document Lifecycle Status (ACTIVE/ARCHIVED/DELETED) | Staff Action | No -- staff deletes/archives/restores | System records the transition and timestamp/actor; never changes lifecycle state on its own. |
| OCR Extraction Text / AI Key Findings | System-Generated | Yes | Raw harvested output. Feeds the Review Queue and Structured Mapping layer as *candidates* only -- never consumed directly by readiness or the SOC gate. |

## Reading this table

- **"Staff"** = a human-entered value with no system computation involved at all.
- **"Staff Reviewed"** = the system may harvest/suggest a candidate, but the value is not considered a source of truth until a staff member reviews/confirms it.
- **"OCR Candidate + Staff Review"** = same as above, explicitly naming the harvesting mechanism (OCR/document intelligence).
- **"System-Computed"** = the system is authorized to calculate this value, but only from already-reviewed/staff-established inputs -- never from raw extraction or from data staff have not yet confirmed.
