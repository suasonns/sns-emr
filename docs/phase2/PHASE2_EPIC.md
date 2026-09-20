# PHASE 2 - Repository Validation & Compliance Discovery

## Objective

Validate the SNS Hospice EMR repository against the approved Patient Chart authority baseline, California hospice requirements, federal CMS requirements, applicable LCD guidance, and disease-specific documentation guidance.

## Scope Boundary

This issue authorizes repository discovery, evidence collection, validation, and documentation only.

It does **not** authorize application code changes, API changes, schema changes, migrations, production-data changes, permission changes, automated hospice-eligibility decisions, prognosis generation, physician-certification automation, or automatic Plan-of-Care activation.

## Child Issues

- [ ] P2-001 - LCD L33393 Validation
- [ ] P2-002 - Certification Ownership Audit
- [ ] P2-003 - Certification Lifecycle Validation
- [ ] P2-004 - Plan of Care Workflow Audit
- [ ] P2-005 - Plan of Care Review Validation
- [ ] P2-006 - Medical Record Correction Audit
- [ ] P2-007 - Amendment Workflow Audit
- [ ] P2-008 - Addendum Workflow Audit
- [ ] P2-009 - Reconciliation & Deficiency Analysis Audit
- [ ] P2-010 - Authentication Audit
- [ ] P2-011 - Audit Event Inventory
- [ ] P2-012 - Workflow Authority Validation
- [ ] P2-013 - Source Ownership Verification
- [ ] P2-014 - Regulatory Coverage Matrix
- [ ] P2-015 - Gap Classification Review
- [ ] P2-016 - Phase 3 Readiness Package

## Dependency Chain

```text
P2-001 -> P2-002 -> P2-003 --\
P2-004 -> P2-005 -----------\
P2-006 -> P2-007             \
       -> P2-008              > P2-014 -> P2-015 -> P2-016
       -> P2-009             /
P2-010 -> P2-011 ----------/
P2-012 -> P2-013 ---------/
```

## Exit Gate

- [ ] LCD L33393 section-level validation completed
- [ ] Certification ownership and lifecycle validated
- [ ] Plan-of-Care workflow and review behavior validated
- [ ] Record correction, amendment, addendum, reconciliation, and deficiency analysis validated
- [ ] Authentication, signature, countersignature, and audit-event behavior validated
- [ ] Workflow and source ownership validated
- [ ] Regulatory coverage matrix approved
- [ ] Gaps classified
- [ ] Phase 3 readiness package approved

## Final Authorization

- Repository discovery: `AUTHORIZED`
- Application implementation: `NOT_AUTHORIZED`
