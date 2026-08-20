# IDG Domain Model — Three Separate Entities

`IDG` is overloaded in hospice. **Do not create or reuse one generic "IDG"
object.** There are three separate entities with different purposes and
different lifecycles. This is intentional and load-bearing for the voice-
to-documentation and physician batch-signing workflows — do not collapse
these back into one table/model.

## 1. PatientIDGReview
- **Class / table:** `IDGReview` in `app/models/idg_review.py` / `idg_reviews`
- **What it is:** Patient-chart clinical documentation — Admission,
  Initial, Routine, Recertification, and Significant-Change IDG review
  notes. Contains nursing/physician/MSW/chaplain discussion, POC review,
  and may contain signatures.
- **Belongs to:** ONE patient.
- **Is NOT:** a meeting.

## 2. IDGMeeting
- **Class / table:** `IDGMeeting` in `app/models/idg_meeting.py` / `idg_meetings`
- **What it is:** The recurring interdisciplinary team meeting (typically
  every 14 days) — date/time, attendees, agenda, minutes, status.
- **Contains:** the patient review queue (multiple patients).
- **Is NOT:** a patient note.

## 3. IDGMeetingPatientReview
- **Class / table:** `IDGMeetingPatientReview` in
  `app/models/idg_meeting_patient_review.py` / `idg_meeting_patient_reviews`
- **What it is:** The temporary, in-meeting review workspace created while
  one patient is being discussed during one IDGMeeting. Tracks POC review,
  medication list review, medication reconciliation, pending-orders
  review, physician review status (`PENDING` / `REVIEWED` / `DEFERRED`),
  defer reason/note, and the reviewed-item checklist. **Determines
  batch-signature-queue eligibility.**
- **Is NOT:** a patient note, and NOT the meeting itself.
- **Service layer:** `app/services/idg_physician_review_service.py`
- **API:** `app/api/idg/router.py` — `/idg/sessions/{idg_meeting_id}/...`

## Relationship

```
Patient
 └── PatientIDGReview (IDGReview)

IDGMeeting
 └── IDGMeetingPatientReview  ── Patient
```

## Workflow

```
IDGMeeting
 -> Open Patient
 -> Create/Load IDGMeetingPatientReview
 -> Review POC
 -> Review Medication List
 -> Perform Medication Reconciliation
 -> Review Orders
 -> Reviewed OR Deferred
 -> Update PatientIDGReview (IDGReview)
 -> Next Patient
```

## Review vs. Signature — always separate events

- **Review event** (on `IDGMeetingPatientReview`): `review_status`,
  `reviewed_at`, `physician_user_id`, `recorded_by_user_id`,
  `reviewed_by_physician_directly`, `defer_reason`, `defer_note`,
  reviewed-item checklist booleans.
- **Signature event** (on `PhysicianOrder`, via
  `physician_order_service.approve_order`): `signed_at`/`ordered_at`,
  `ordered_by_provider_*`, order status — occurs after IDG when the
  physician logs in and batch-signs. Never write signature fields onto
  the review row, and never infer a review from a signature.

## Batch-signing eligibility (enforced in
`idg_physician_review_service.get_batch_signature_queue` /
`batch_sign`)

Include only when **all** of:
- `review_status = REVIEWED`
- order `signature_status = UNSIGNED` (pending physician order)
- patient has signable orders

Always exclude:
- `review_status = DEFERRED` (also auto-creates an
  `IDG_DEFERRED_MD_REVIEW` Task so the MD is alerted to review/sign that
  patient individually later — see
  `_sync_deferred_md_review_task` in the service)
- `review_status = PENDING`
- no signable orders / cancelled orders

## Audit-trail honesty rule

`recorded_by_user_id` (who clicked) is tracked separately from
`physician_user_id` (physician of record) and
`reviewed_by_physician_directly` (bool). If a facilitator/RN records the
review while the MD verbally participates in IDG, the trail must say
"recorded by facilitator" — never falsely attribute the click to the
physician unless they personally authenticated and clicked it themselves.

## Critical architectural rule

- Do NOT reuse `IDGReview` (PatientIDGReview) as the meeting workspace.
- Do NOT store meeting workflow fields inside `IDGReview`.
- Do NOT store patient documentation fields inside `IDGMeeting`.

Keep all three entities separate. Each has a different purpose and a
different lifecycle.
