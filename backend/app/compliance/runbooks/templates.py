from app.compliance.types import RuleMeta


def render_rule_markdown(rule: RuleMeta) -> str:
    return f"""
## {rule.code} — {rule.title}

**Regulator:** {rule.regulator}  
**Version:** {rule.version}  
**Effective Date:** {rule.effective_date}  
**Citation:** {rule.reference}

### Description
{rule.description}

### System Enforcement (Survey Defensibility)
- Rule Source: `app/compliance/{rule.regulator.lower()}/`
- Rule Output: structured obligations (no direct DB writes)
- Task Engine Behavior:
  - Creates a task with a due date derived from clinical events
  - Enforces evidence linkage on completion
- Audit Evidence:
  - `tasks.status`, `tasks.due_date`
  - `tasks.completed_at`
  - `tasks.completion_reference_type`, `tasks.completion_reference_id`

---
"""