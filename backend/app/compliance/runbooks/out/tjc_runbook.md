# TJC Compliance Runbook

This runbook is generated directly from active compliance rules.
It reflects enforced system behavior.


## TJC-HOSPICE-TRACERS — Survey tracer readiness (documentation & care coordination)

**Regulator:** TJC  
**Version:** 2026.05  
**Effective Date:** 2026-05-23  
**Citation:** The Joint Commission Hospice Survey Tracers

### Description
Defines tracer expectations for documentation integrity and care coordination. Metadata-only module until tracer tasks are modeled in task_type enum.

### System Enforcement (Survey Defensibility)
- Rule Source: `app/compliance/tjc/`
- Rule Output: structured obligations (no direct DB writes)
- Task Engine Behavior:
  - Creates a task with a due date derived from clinical events
  - Enforces evidence linkage on completion
- Audit Evidence:
  - `tasks.status`, `tasks.due_date`
  - `tasks.completed_at`
  - `tasks.completion_reference_type`, `tasks.completion_reference_id`

---

