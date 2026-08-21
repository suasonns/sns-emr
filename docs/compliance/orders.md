# Orders Compliance Runbook
SNS Hospice EMR

## Purpose
This document describes how hospice physician orders are created, approved,
tracked, and audited in SNS EMR to meet CMS Hospice Conditions of Participation,
ACHC, CDPH, TJC, and CHAP requirements.

---

## Order Lifecycle (Phase 1 expansion — additive only)

Stored status literals are never renamed; a **display-label layer**
(`physician_order_service.label_for()` / `STATUS_LABELS`) presents the
survey-facing terminology below without changing the underlying value:

| Stored status                  | Display label                  |
|---------------------------------|---------------------------------|
| DRAFT                            | Draft                           |
| PENDING_CLINICAL_REVIEW          | Pending Clinical Review         |
| PENDING_HOSPICE_MD_APPROVAL      | Pending Physician Signature     |
| APPROVED                         | Signed                          |
| EXECUTED                         | Implemented                     |
| COMPLETED                        | Completed                       |
| EXPIRED                          | Expired                         |
| CANCELLED                        | Cancelled                       |

```
DRAFT
  → PENDING_CLINICAL_REVIEW (conditional, "Path A")
        → approve → PENDING_HOSPICE_MD_APPROVAL
        → return  → DRAFT (reason required)
  → PENDING_HOSPICE_MD_APPROVAL (direct, "Path B")
→ APPROVED (MD signature)
→ EXECUTED (Implemented)
→ COMPLETED (requires completion_evidence) | EXPIRED (expires_at reached)
(CANCELLED reachable from any non-terminal status; reason required)
```

Only the Medical Director (MD) may approve orders (sign). This has not
changed; Phase 1 adds lifecycle stages around that approval, it does not
change who may sign.

### Conditional Clinical Review ("Path A" vs "Path B")

Clinical review before MD signature is **not universal** — it is required
only when the order was NOT entered/authenticated by a self-verifying
clinical role:

- **Bypassed (Path B — straight to MD approval)** when priority is
  `STAT`/`URGENT`, or the submitting role is `MD`, `NP`, `PA`, or `RN` **and**
  `prescriber_authenticated = true`.
- **Required (Path A — routes through `PENDING_CLINICAL_REVIEW` first)**
  otherwise (e.g. office/administrative entry, or an unauthenticated LVN
  entry).
- A caller may force-bypass an otherwise-required review, but only with a
  recorded `bypass_reason` (`clinical_review_bypassed` +
  `clinical_review_bypass_reason` on the order, and on the transition
  event).
- Clinical review is completed by an authorized reviewer (e.g. RN) via
  `complete_clinical_review()`: approve → `PENDING_HOSPICE_MD_APPROVAL`
  (creates the MD task); reject → returns to `DRAFT` with a required
  reason.

### Implementation vs. Completion

`EXECUTED` ("Implemented") and `COMPLETED` are distinct. A standing/ongoing
order (e.g. a recurring medication order) may remain `EXECUTED`
indefinitely. `COMPLETED` requires linked `completion_evidence` — it is
never inferred solely from signature or transmission.

### Expiration

`APPROVED`/`EXECUTED` orders with a populated `expires_at` in the past are
moved to `EXPIRED` (manually via `expire_order()` or in a batch sweep via
`expire_due_orders()`). Expiration never erases the original signature
fields (`signed_by_user_id`, `signed_at`) — the signed record is preserved.

### Cancellation

`cancel_order()` requires a `reason` and is blocked once an order has
reached a terminal status (`COMPLETED`, `EXPIRED`, `CANCELLED`).

### Immutable Status-History Audit Trail

Every transition — including the initial `DRAFT` creation — is recorded as
an append-only row in `physician_order_status_events` (from_status,
to_status, changed_by_user_id, changed_by_role, changed_at, reason,
automatic, clinical_review_bypassed/reason, evidence), retrievable via
`GET /{order_id}/status-history`. This is in addition to the generic
`audit_log` table entry for the same event.

---

## Required Data Elements (Before Approval)

- ordered_by_provider_name
- ordered_by_provider_role ∈ {MD, NP, PA}
- source_type
- ordered_at timestamp
- order_text (explicit instructions)
- prescriber_authenticated = true
- phone_readback_confirmed = true (if VERBAL_PHONE)

Orders missing any required field **cannot** be approved.

---

## MD Approval Rules

- MD authentication required
- Approval recorded via:
  - signed_by_user_id
  - signed_at
  - signature_method
  - signature_event_id
- Approval transitions status to APPROVED

RN/LVN/NP/PA **cannot** approve orders.

---

## Task Enforcement

When an Order enters PENDING_HOSPICE_MD_APPROVAL:

- A task `ORDER_MD_APPROVAL` is created
- Assigned implicitly to MD role
- Due date = ordered_at + 24 hours
- Task references the Order ID

When the MD approves the Order:

- Task is automatically marked COMPLETED
- completed_at timestamp recorded
- Completion references the Order

---

## Audit & Survey Evidence

Surveyors may ask:

**Who approved this order?**  
→ orders.signed_by_user_id

**When was it approved?**  
→ orders.signed_at

**Was approval timely?**  
→ task.due_at vs task.completed_at

**Are verbal orders read back?**  
→ orders.phone_readback_confirmed

All answers are traceable in the database.

---

## Prohibited Actions

- Approving an order without MD role
- Approving without order_text
- Approving without prescriber authentication
- Bypassing task creation or completion

---

## Conclusion

The SNS Orders workflow enforces:
- Completeness
- Timeliness
- Role‑based authority
- Traceable audit evidence

This design is survey‑defensible across CMS, ACHC, CDPH, TJC, and CHAP.
``