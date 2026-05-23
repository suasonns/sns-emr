# CDPH Compliance Runbook

This runbook is generated directly from active compliance rules.
It reflects enforced system behavior.


## CDPH-CA-HOSPICE-BASELINE — California hospice compliance baseline

**Regulator:** CDPH  
**Version:** 2026.05  
**Effective Date:** 2026-05-23  
**Citation:** CDPH Hospice Program Expectations (CA)

### Description
California-specific hospice compliance expectations. Metadata-only module until specific CA rules are encoded as obligations.

### System Enforcement (Survey Defensibility)
- Rule Source: `app/compliance/cdph/`
- Rule Output: structured obligations (no direct DB writes)
- Task Engine Behavior:
  - Creates a task with a due date derived from clinical events
  - Enforces evidence linkage on completion
- Audit Evidence:
  - `tasks.status`, `tasks.due_date`
  - `tasks.completed_at`
  - `tasks.completion_reference_type`, `tasks.completion_reference_id`

---

