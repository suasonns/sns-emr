# SNS EMR — Definition of Done (By Gate)

**Generated:** 2026-05-08T02:32:26Z

## Global Requirements (ALL GATES)
✅ Tenant isolation enforced on all PHI tables/queries by `agency_id`/`tenant_id`.
✅ Forward‑only Alembic migrations; never rewrite migration history.
✅ Enum safety patterns used; no duplicate type creation.
✅ Audit trails immutable.
✅ Evidence consistency: only COMPLETED tasks contain evidence fields.

✅ Primary Diagnosis validation enforced server‑side.
✅ Communications (announcements/messaging) isolated from alerts and compliance.

---

## Gate 1 — Clinical Core ✅
DONE when:
- Patient → Visit → Note lifecycle works per tenant
- Finalize/signature prevents edits
- Benefit periods exist and are referenced

## Gate 2 — Task & Obligation Engine ✅
DONE when:
- Tasks are tenant‑scoped
- Overdue logic works
- Completion evidence present only when COMPLETED
- IDG 15‑day cadence supported (IDG_POC_REVIEW)

## Gate 3 — QA / Compliance Read Models ✅
DONE when:
- Evidence queries reproducible per tenant

## Gate 4 — RARE (Regulatory Reporting) 🔴
DONE when:
- regulatory reports are tenant‑scoped and immutable after certification

## Gate 5 — HR / Volunteers / Vendors 🔴

## Gate 6 — Financial & Cost Reporting 🟡

## Gate 7 — Roles & Permissions 🔵 (Deferred)

## Gate 8 — Platform Governance & Communications 🟡
DONE when:
- Owner feature switches are enforced
- Platform announcements supported
- Tenant announcements supported
- Tenant messaging + files supported (optional)
