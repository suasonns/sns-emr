"""
Model/migration parity regression tests for Sprint 1 (Eligibility
Traceability Epic): BenefitPeriod audit trail + billing-readiness
persistence.

Migrations v3w4x5y6z7a8 and u2v3w4x5y6z7 create a unique constraint and an
index directly at the DB level (op.create_unique_constraint /
op.create_index). Those DB objects were briefly *not* mirrored in the
corresponding SQLAlchemy models' `__table_args__`, which is invisible at
runtime (the constraint/index already exist in the DB) but is caught by
CI's `alembic revision --autogenerate` schema-drift check, since
autogenerate diffs live DB state against model metadata, not migration
history.

These tests assert directly against SQLAlchemy table metadata (not just
"insert works" / DB behavior), so they fail immediately if either model
declaration is ever removed again while the migration itself is left
untouched -- closing the gap a future developer could otherwise
reintroduce without any test failing.
"""

from sqlalchemy import Index, UniqueConstraint

from app.models.benefit_period import BenefitPeriod
from app.billing.models.billing_readiness_verdict import BillingReadinessVerdict


def test_benefit_period_has_tenant_patient_type_start_unique_constraint():
    """BenefitPeriod must declare uq_benefit_periods_tenant_patient_type_start
    matching migration v3w4x5y6z7a8 exactly (name + column order)."""
    unique_constraints = [
        c for c in BenefitPeriod.__table__.constraints if isinstance(c, UniqueConstraint)
    ]
    named = {c.name: c for c in unique_constraints}

    assert "uq_benefit_periods_tenant_patient_type_start" in named, (
        "BenefitPeriod is missing the uq_benefit_periods_tenant_patient_type_start "
        "UniqueConstraint declaration in __table_args__. This constraint already "
        "exists at the DB level (migration v3w4x5y6z7a8) -- it must also be "
        "declared on the model or `alembic revision --autogenerate` will report "
        "false schema drift."
    )

    constraint = named["uq_benefit_periods_tenant_patient_type_start"]
    column_names = tuple(col.name for col in constraint.columns)
    assert column_names == ("tenant_id", "patient_id", "benefit_type", "start_date"), (
        f"uq_benefit_periods_tenant_patient_type_start column order must exactly "
        f"match migration v3w4x5y6z7a8's ['tenant_id', 'patient_id', 'benefit_type', "
        f"'start_date']; got {column_names}."
    )


def test_billing_readiness_verdict_has_patient_evaluated_at_index():
    """BillingReadinessVerdict must declare ix_brv_patient_evaluated_at
    matching migration u2v3w4x5y6z7 exactly (name + column order)."""
    named = {idx.name: idx for idx in BillingReadinessVerdict.__table__.indexes}

    assert "ix_brv_patient_evaluated_at" in named, (
        "BillingReadinessVerdict is missing the ix_brv_patient_evaluated_at "
        "Index declaration in __table_args__. This index already exists at "
        "the DB level (migration u2v3w4x5y6z7) -- it must also be declared "
        "on the model or `alembic revision --autogenerate` will report false "
        "schema drift."
    )

    index = named["ix_brv_patient_evaluated_at"]
    column_names = tuple(col.name for col in index.columns)
    assert column_names == ("patient_id", "evaluated_at"), (
        f"ix_brv_patient_evaluated_at column order must exactly match migration "
        f"u2v3w4x5y6z7's ['patient_id', 'evaluated_at']; got {column_names}."
    )
    assert isinstance(index, Index)
