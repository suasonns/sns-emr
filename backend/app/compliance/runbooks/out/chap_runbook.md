# CHAP Compliance Runbook

This runbook is generated directly from active compliance rules.
It reflects enforced system behavior.


## CHAP-HOSPICE-CORE — CHAP hospice accreditation core expectations

**Regulator:** CHAP  
**Version:** 2026.05  
**Effective Date:** 2026-05-23  
**Citation:** CHAP Hospice Accreditation Standards

### Description
Defines CHAP hospice accreditation expectations. Metadata-only module until CHAP-specific obligations are modeled.

### System Enforcement (Survey Defensibility)
- Rule Source: `app/compliance/chap/`
- Rule Output: structured obligations (no direct DB writes)
- Task Engine Behavior:
  - Creates a task with a due date derived from clinical events
  - Enforces evidence linkage on completion
- Audit Evidence:
  - `tasks.status`, `tasks.due_date`
  - `tasks.completed_at`
  - `tasks.completion_reference_type`, `tasks.completion_reference_id`

---

