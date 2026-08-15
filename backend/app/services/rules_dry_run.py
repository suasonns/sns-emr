from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.rules.registry import get_rules_for_workflow
from app.rules.base import RuleContext, RuleOutcome


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dict(value: Any) -> Dict[str, Any]:
    """
    Prevent JSON serialization errors for API responses.
    """
    if isinstance(value, dict):
        safe: Dict[str, Any] = {}

        for k, v in value.items():
            try:
                if isinstance(v, (str, int, float, bool, type(None), list, dict)):
                    safe[str(k)] = v
                else:
                    safe[str(k)] = str(v)
            except Exception:
                safe[str(k)] = "<unserializable>"

        return safe

    return {}


def dry_run_rules(ctx: RuleContext, *, db: Session | None = None) -> dict:
    """
    Evaluate rules and return structured dry-run report.
    IMPORTANT: No enforcement.
    """

    rules = get_rules_for_workflow(
        ctx.workflow,
        tenant_id=ctx.tenant_id,
        db=db,
    )

    results: List[Dict[str, Any]] = []

    pass_count = 0
    warn_count = 0
    block_count = 0
    error_count = 0

    started_at = _utc_now_iso()

    # ✅ deterministic execution order
    rules = sorted(rules, key=lambda r: r.rule_id)

    for rule in rules:
        try:
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
                "details": _safe_dict(r.details),
                "evidence": _safe_dict(r.evidence),
                "regulator": r.regulator,
                "rule_version": r.rule_version,
                "evaluated_at": r.created_at.isoformat(),
            })

        except Exception as e:
            # ✅ isolate rule failure
            error_count += 1

            results.append({
                "rule_id": getattr(rule, "rule_id", "UNKNOWN"),
                "rule_name": getattr(rule, "rule_name", "UNKNOWN"),
                "outcome": "ERROR",
                "severity": "WARN",
                "reason": f"Rule execution failed: {str(e)}",
                "details": {},
                "evidence": {},
                "regulator": getattr(rule, "regulator", None),
                "rule_version": getattr(rule, "version", None),
                "evaluated_at": _utc_now_iso(),
            })

    overall_status = (
        "BLOCKING_FOUND"
        if block_count
        else ("WARN_ONLY" if warn_count else "PASS")
    )

    return {
        "summary": {
            "total_rules": len(results),
            "pass_count": pass_count,
            "warn_count": warn_count,
            "block_count": block_count,
            "error_count": error_count,
            "overall_status": overall_status,
            "started_at": started_at,
            "completed_at": _utc_now_iso(),
        },
        "results": results,
    }