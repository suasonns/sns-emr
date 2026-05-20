# Orders Compliance Runbook
SNS Hospice EMR

## Purpose
This document describes how hospice physician orders are created, approved,
tracked, and audited in SNS EMR to meet CMS Hospice Conditions of Participation,
ACHC, CDPH, TJC, and CHAP requirements.

---

## Order Lifecycle

DRAFT  
→ PENDING_HOSPICE_MD_APPROVAL  
→ APPROVED  
→ EXECUTED / CANCELLED  

Only the Medical Director (MD) may approve orders.

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