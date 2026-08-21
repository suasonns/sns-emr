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

Order signature authority is **not** MD-only — see the "Provider Signature
Authority Model" section below for the full Primary/Alternate signer
tiering. Phase 1 added lifecycle stages around approval; the Provider
Signature Authority Model (below) is what changed who may sign and under
what conditions.

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

- Approval requires an authorized provider signer per the Provider
  Signature Authority Model (see below) — no longer MD-only.
- Approval recorded via:
  - signed_by_user_id
  - signed_by_provider_role (NEW — the actual signer's provider role/credential)
  - signed_at
  - signature_method
  - signature_event_id
  - alternate_signer_reason (NEW — required when an alternate authorized
    provider signer, NP/PA, signs)
- Approval transitions status to APPROVED

Administrator, DPCS, and any non-provider role **cannot** approve orders,
regardless of rank (`allow_clinical_admin=False`).

---

## Provider Signature Authority Model (owner directive 2026-08-21)

SNS does not ask "is this a physician?". It asks "is this provider
authorized to sign THIS document under THIS workflow?" Signature
authority is evaluated by document type, provider credential, agency
policy, workflow type, order type, and urgency — never a flat role
equivalence.

### Primary Signers (may sign any order, any priority/category)

Routed to in this precedence order when a specific physician is sought:

1. Attending Physician
2. Hospice Physician
3. Medical Director
4. Medical Director Designee

The legacy `"MD"` provider-discipline literal is also accepted as a
primary signer for backward compatibility with orders/accounts predating
this model.

### Alternate Authorized Provider Signers (conditional)

- Nurse Practitioner (NP)
- Physician Assistant (PA)

NP/PA may sign an order **only** when both are true:

- `priority` is `STAT` or `URGENT` (the workflow must never delay patient
  care — oxygen, comfort medications, DME, hospital bed, supplies, symptom
  management, immediate treatment changes — while attempting to reach a
  specific physician), **and**
- `order_category` is one of `MEDICATION`, `DME`, `SUPPLY`, `TREATMENT`.

NP/PA can never sign a `ROUTINE` order, and never a `LAB`/`DIET`/`OTHER`
category order regardless of urgency.

Every alternate-signer use **requires** a recorded `alternate_signer_reason`
documenting why the alternate signer acted instead of the primary
provider. This is enforced at the service layer
(`physician_order_service.approve_order()`) — omitting it raises a
validation error and the order cannot be signed.

### Enforcement layer

`is_authorized_order_signer(role, priority=..., order_category=...)` in
`app/services/physician_order_service.py` is the single source of truth
for this decision. The `POST /physician-orders/{id}/approve` endpoint
gates on the union of primary + alternate roles
(`svc.ORDER_ALL_SIGNER_ROLES`, `allow_clinical_admin=False`); the
STAT/URGENT-category restriction on NP/PA is enforced inside
`approve_order()` itself, since it is a per-order (not per-role) decision.

### Dashboard widget

The signature queue widget key is `orders_requiring_provider_signature`
(renamed from `orders_requiring_my_signature`) — visible to Medical
Director, Attending Physician, Hospice Physician, NP, and PA. Dashboard
*visibility* of this widget does not by itself grant signing capability;
the API/service layer above is the actual enforcement point, exactly as
with the CTI/F2F oversight-vs-authority separation.

### Audit requirements

Every provider signature captures: user ID, provider ID
(`signed_by_user_id`), provider type/credential (`signed_by_provider_role`),
date/time (`signed_at`), document version (`signature_event_id`), and — for
alternate signers — the reason (`alternate_signer_reason`). This is in
addition to the generic `audit_log` entry and the immutable
`physician_order_status_events` row for the same transition.

### Document-specific authority (not shared across workflows)

CTI, F2F, and Physician Orders each define **independent** signer-role
rules for their own document type — there is no single generic
"provider authority engine." A provider authorized to sign a physician
order is not automatically authorized to certify a CTI or perform an F2F
encounter; see `docs/compliance/cti.md` and `docs/compliance/f2f.md`.

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

- Approving an order without an authorized provider signer role (see
  Provider Signature Authority Model)
- NP/PA signing a ROUTINE order, or a non-eligible-category order, or
  without a recorded alternate_signer_reason
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