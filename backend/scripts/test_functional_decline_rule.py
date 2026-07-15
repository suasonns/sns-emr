from app.rules.base import (
    RuleContext,
    Workflow,
    DiagnosisItem,
)

from app.rules.eligibility.functional_decline_readiness import (
    FunctionalDeclineReadinessRule,
)

ctx = RuleContext(
    workflow=Workflow.ADMISSION,
    primary_dx=DiagnosisItem(
        icd10="C34.90",
        description="Malignant neoplasm of lung",
    ),
    facts={
        "pps": 40,
        "kps": 50,
        "fast_stage": None,
    },
)

rule = FunctionalDeclineReadinessRule()

result = rule.evaluate(ctx)

print(result)