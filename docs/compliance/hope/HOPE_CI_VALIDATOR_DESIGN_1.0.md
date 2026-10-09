# HOPE CI Validator Design

Document ID: HOPE-CI-001  
Version: 1.0  
Status: Designed, not implemented

## Inputs

## Canonical registry source

## Scanned source paths

## Validation rules

- Unknown item ID
- Duplicate authoritative owner
- Wrong section or concept
- Incomplete or wrong value set
- Wrong skipped/not-applicable value
- Wrong record type or timepoint
- Missing export mapping
- Missing correction behavior
- Missing required tests
- Registry/UI/API/storage/export mismatch
- Unapproved exception

## Failure output

- File
- Property
- Item ID
- Expected concept
- Actual concept
- Reason
- Source requirement

## CI integration

## Local developer command

## Regression fixtures

## Test strategy

## Rollback

## Exception controls

No permanent exceptions. Each temporary exception requires a source, owner,
test, approval, and review/expiration date.
