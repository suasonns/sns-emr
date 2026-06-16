# SNS EMR – Locked Baseline Summary

**Baseline Tag:** sns-emr-stable-2026-06-04  
**Alembic Head:** 3d7785acaf04  
**Status:** Production-stable, survey-defensible

## Proven Guarantees
- Admission authorization is idempotent
- Exactly one INITIAL_RN_ICA and one NOE_DUE per patient
- Enforced at BOTH service and DB levels
- SOC is immutable (no-op on reauthorization)
- ADR audit fails closed (F1) on schema/DB failure
- A2 invalid ADR period detected
- Discipline scope enforced (403 where required)

## DB-Level Invariants
- Partial unique index:
  uq_tasks_initial_unique_per_patient
  (tenant_id, patient_id, task_type)
  WHERE task_type IN ('INITIAL_RN_ICA', 'NOE_DUE')

## Test Proof
- python scripts/preflight.py --pytest ✅