# HOPE Canonical Registry Contract

Document ID: HOPE-REG-001  
Version: 1.0  
Status: Proposed

## Authority package
- Guidance Manual version:
- Data Specifications version:
- Errata versions:
- Item-set versions:
- Effective date:
- Verification date:

## Registry record

- `section`
- `itemId`
- `parentItemId`
- `officialTitle`
- `officialConcept`
- `allowedValues`
- `skippedValue`
- `notApplicableValue`
- `recordTypes`
- `timepoints`
- `lookBack`
- `dependencies`
- `skipRules`
- `triggerRules`
- `exportIdentifier`
- `correctionRule`
- `sourceVersion`
- `effectiveDate`
- `errata`
- `implementationStatus`

## Invariants

- Item IDs are unique.
- Official concept and source version are required.
- Section, value set, record type, and timepoint match controlling sources.
- Authoritative ownership is not duplicated without an approved exception.
- Every implemented item has tests.
- Every exported item has an authoritative source field.

## Exception record

- Exception ID:
- Reason:
- Requirement source:
- Owner:
- Approval date:
- Review/expiration date:
- Required tests:
- Status:
