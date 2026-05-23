from sqlalchemy.orm import Session

from app.rules.registry import get_rules_for_workflow
from app.rules.base import RuleContext, RuleOutcome


def dry_run_rules(ctx: RuleContext, *, db: Session | None = None) -> dict:
    """
    Evaluate rules and return structured dry-run report.
    IMPORTANT: No enforcement.
    """
    rules = get_rules_for_workflow(ctx.workflow, tenant_id=ctx.tenant_id, db=db)

    results = []
    pass_count = 0
    warn_count = 0
    block_count = 0

    for rule in rules:
        r = rule.evaluate(ctx)

        if r.outcome == RuleOutcome.PASS:
            pass_count += 1
        elif r.outcome == RuleOutcome.WARN:
            warn_count += 1
        elif r.outcome == RuleOutcome.VIOLATION:
            block_count += 1

        results.append({
            "rule_id": r.rule_id,
            "rule_name": r.rule_name,
            "outcome": r.outcome.value,
            "severity": r.severity.value,
            "reason": r.reason,
            "details": r.details,
            "evidence": r.evidence,
        })

    overall_status = "BLOCKING_FOUND" if block_count else ("WARN_ONLY" if warn_count else "PASS")

    return {
        "summary": {
            "total_rules": len(results),
            "pass_count": pass_count,
            "warn_count": warn_count,
            "block_count": block_count,
            "overall_status": overall_status,
        },
        "results": results,
    }