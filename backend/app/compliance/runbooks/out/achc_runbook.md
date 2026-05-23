# ACHC Compliance Runbook

This runbook is generated directly from active compliance rules.
It reflects enforced system behavior.


## ACHC-DOC-TIMELINESS — Clinical documentation timeliness (visit note completion)

**Regulator:** ACHC  
**Version:** 2026.05  
**Effective Date:** 2026-05-23  
**Citation:** ACHC Hospice documentation timeliness expectations

### Description
Ensures visit documentation is completed within an expected time window and is evidence-linked for survey defensibility.

### System Enforcement (Survey Defensibility)
- Rule Source: `app/compliance/achc/`
- Rule Output: structured obligations (no direct DB writes)
- Task Engine Behavior:
  - Creates a task with a due date derived from clinical events
  - Enforces evidence linkage on completion
- Audit Evidence:
  - `tasks.status`, `tasks.due_date`
  - `tasks.completed_at`
  - `tasks.completion_reference_type`, `tasks.completion_reference_id`

---

