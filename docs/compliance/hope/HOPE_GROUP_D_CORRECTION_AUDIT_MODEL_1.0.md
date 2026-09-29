# HOPE Correction and Audit Model

Document ID: HOPE-AUDIT-001  
Version: 1.0  
Status: Designed, not implemented

## Provenance categories

A. Clinician-entered  
B. Prefilled and clinician-confirmed  
C. System-derived  
D. Imported  
E. Corrected  
F. Migrated or transformed  
G. Historical origin unknown

## Record states

Draft, Validated, Exported, Submitted, Rejected, Accepted, Modified, Inactivated

## Event fields

- Event ID
- Event type
- Actor
- Timestamp
- Assessment ID
- HOPE record type
- Timepoint
- Item ID
- Original value
- New value
- Reason
- Source type and record
- Clinician confirmation
- Submission state
- CMS validation result
- Rule/software version
- Related event
- Audit visibility
- Retention rule

## Required event types

- HOPE_DRAFT_CREATED
- HOPE_VALUE_ENTERED
- HOPE_VALUE_PREFILLED
- HOPE_VALUE_CONFIRMED
- HOPE_VALUE_DERIVED
- HOPE_VALUE_CORRECTED
- HOPE_RECORD_VALIDATED
- HOPE_EXPORT_CREATED
- HOPE_SUBMISSION_ATTEMPTED
- HOPE_SUBMISSION_REJECTED
- HOPE_SUBMISSION_ACCEPTED
- HOPE_RECORD_MODIFIED
- HOPE_RECORD_INACTIVATED
- HOPE_SFV_TRIGGERED
- HOPE_SFV_COMPLETED
- HOPE_SFV_NOT_COMPLETED

## Pre-acceptance correction

## Post-acceptance correction

## Modification

## Inactivation

## Resubmission

## Historical-record handling
