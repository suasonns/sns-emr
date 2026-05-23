# CMS Compliance Runbook

This runbook is generated directly from active compliance rules.
It reflects enforced system behavior.


## CMS-418.56-POC-UPDATE — Plan of Care update timing (ROUTINE vs CRISIS)

**Regulator:** CMS  
**Version:** 2026.05  
**Effective Date:** 2026-05-23  
**Citation:** CMS Hospice CoPs §418.56

### Description
Defines timing and evidence requirements for POC updates.

### System Enforcement (Survey Defensibility)
- Rule Source: `app/compliance/cms/`
- Rule Output: structured obligations (no direct DB writes)
- Task Engine Behavior:
  - Creates a task with a due date derived from clinical events
  - Enforces evidence linkage on completion
- Audit Evidence:
  - `tasks.status`, `tasks.due_date`
  - `tasks.completed_at`
  - `tasks.completion_reference_type`, `tasks.completion_reference_id`

---

### Tenant Policy Mapping
- **PP Policy 9-017** — Plan of Care (Policy ID: LFH-PP-POC)


## CMS-EVIDENCE-LINKAGE — Evidence linkage required for task completion

**Regulator:** CMS  
**Version:** 2026.05  
**Effective Date:** 2026-05-23  
**Citation:** Survey defensibility / audit integrity

### Description
Tasks must record evidence reference type+id at completion.

### System Enforcement (Survey Defensibility)
- Rule Source: `app/compliance/cms/`
- Rule Output: structured obligations (no direct DB writes)
- Task Engine Behavior:
  - Creates a task with a due date derived from clinical events
  - Enforces evidence linkage on completion
- Audit Evidence:
  - `tasks.status`, `tasks.due_date`
  - `tasks.completed_at`
  - `tasks.completion_reference_type`, `tasks.completion_reference_id`

---

### Tenant Policy Mapping
- **HR Policy 3-001** — Competency Program (Policy ID: LFH-HR-COMPETENCY)

