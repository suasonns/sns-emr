# Gate 2 — Task Engine Mini‑Blueprint (Tenant‑Aware)

**Generated:** 2026-05-08T02:32:26Z

## Mandatory Columns
- agency_id (uuid, NOT NULL)

## Rules
- Tasks must never reference evidence from another agency.
- Evidence fields may only be present when status = COMPLETED.

## Explicit Exclusions
- Announcements do NOT generate tasks.
- Messaging does NOT generate tasks.
- Diagnosis validation failures do NOT generate tasks.

## Verification
- Attempt to complete task with mismatched agency_id → FAIL.
