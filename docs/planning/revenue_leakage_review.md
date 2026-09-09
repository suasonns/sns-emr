# Revenue Leakage Review

Date: 2026-09-08
Branch: `feature/production-hnp-clinical-runtime`

Phase 11 required deliverable. Traces the full pipeline
Patient → Election → Benefit Period → Certification → Claim →
Transmission → Remittance → Payment → Revenue, and classifies every
point revenue can be lost, using only what has been directly confirmed
this session (Phase 4/5/6 evidence) plus explicitly-flagged unknowns
carried forward from earlier phases.

| Pipeline Point | Leakage Risk | Classification | Evidence |
|---|---|---|---|
| Patient → Election | Election tracking's own writer/SSOT not verified this pass | **UNKNOWN** | Carried forward from Phase 5; not re-investigated per the "don't repeat completed work" instruction — flagged, not assumed safe or broken |
| Election → Benefit Period | Automatic linkage (does an election reliably produce/attach the correct benefit period without manual intervention?) | **UNKNOWN** | Same — carried forward, unverified |
| Benefit Period → Certification | Certification finalization is checked as a billing-readiness blocker (`_has_finalized_certification` in `billing_readiness_service.py`) — a claim cannot pass readiness without one | **LOW** (a real gate exists) | `billing_readiness_service.py:129` |
| Certification → Claim (rate gap) | An unpriced claim line (`rate_gap_reason` set) is blocked from reaching the 837I text at all | **LOW** (enforced, tested gate — `test_edi_builder_rate_gap.py`) | Confirmed passing test, re-verified this session's broader billing suite run |
| Claim → Transmission | **No `ClaimTransmission` model exists.** A claim can be marked `SENT` (via either writer) with no corresponding verified-transmission record. There is no way to distinguish "we successfully sent this to the clearinghouse" from "we flipped a status flag." | **CRITICAL** | `claim_status_architecture.md` §2; confirmed by repo-wide grep, zero results |
| Transmission (bypass path) | The "Export to Excel" button can move a claim's status to `SENT` **from any current status, including PAID**, via one click, with **no audit event** | **CRITICAL** | `billing_action_map.md`; `test_export_patient_claim_edi_bypasses_allowed_transitions_for_real` (Phase 4, passing/reproducing the bug) |
| Transmission → Remittance | 835 remittance ingestion is backend-correct (matching, payment posting, denial creation) but has **no upload UI** — remittances can only enter the system via direct API call today | **HIGH** (not a correctness risk, an operational-blockage risk: if billing staff cannot upload files, remittances simply never get posted in practice, and revenue sits unrecognized) | `payment_posting_architecture.md` steps 1, 10 |
| Remittance → Payment matching | Unmatched payments are correctly preserved (`match_status="UNMATCHED"`), not dropped — but nothing surfaces this list to a biller for manual reconciliation | **MEDIUM** (data is safe, but invisible — a real payment could sit unmatched indefinitely with nobody prompted to reconcile it) | `payment_posting_architecture.md` step 6; `biller_persona_matrix.md` "what claims lack remittance" |
| Payment → Credit Balance | No code path connects 835-detected overpayment to automatic `CreditBalanceCase` creation; credit balance is a separately-triggered, manually-initiated feature | **MEDIUM** (an overpayment could exist in `Payment` data with no automatic prompt to open a credit-balance case) | `payment_posting_architecture.md` step 9 |
| Payment → Revenue (reporting) | The one dashboard widget that visually represents 835/remittance activity to a human is **fabricated data**, not derived from the real `Payment`/`RemittanceAdvice` tables at all | **CRITICAL for decision-making integrity** (not a money-movement risk — a *visibility* risk: a manager could believe remittance volume/revenue is at a level it is not) | `payment_posting_architecture.md` "The 835 widget specifically" |
| Discharge → billing closure | Whether discharge reliably triggers final billing closure (final claim generation, benefit-period closure) was not re-verified this pass | **UNKNOWN** | Carried forward from Phase 5, explicitly flagged rather than guessed at |

## Ranked by severity

1. **CRITICAL** — No transmission-confirmation data model exists at all;
   a claim can be marked "sent" with zero proof it was actually
   transmitted, and the one path that sets that flag can do so
   incorrectly and silently.
2. **CRITICAL** — The dashboard's remittance widget shows fabricated
   numbers, risking decisions (including a demo audience's trust) being
   based on invented data.
3. **HIGH** — 835 files cannot be uploaded by any staff member through
   any UI, meaning real remittances may never enter the system in
   day-to-day operation regardless of backend correctness.
4. **MEDIUM** — Unmatched payments and potential overpayments are
   correctly retained in the data but are invisible to biller workflows,
   risking silent, indefinite non-reconciliation.
5. **UNKNOWN (carried forward, not newly discovered)** — Election
   linkage, discharge-triggered billing closure — these remain
   unverified and must not be assumed either safe or broken.

## What this means for "revenue leakage" specifically

The evidence gathered this session does not show proof of *money
actually disappearing* (e.g., a claim being paid and the payment never
recorded) — every money-movement code path traced (835 posting, claim
matching, denial creation) was confirmed correct by execution. The real
leakage risk profile found is **operational and visibility-based**:
revenue-relevant events either (a) cannot be entered into the system at
all today by a human (835 upload), (b) can be misrepresented once
entered (fabricated widget), or (c) can have their status corrupted
after the fact with no trace (Export to Excel bug). All three are
serious, but none of them is "the code silently loses money" — they are
"the code cannot yet be operated correctly by staff, and one path can be
operated incorrectly by accident."
