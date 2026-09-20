# RNICA Classification Test Scenarios

**STATUS:** DISCOVERY / AUTHORITY REFERENCE ONLY. NOT IMPLEMENTATION AUTHORIZATION.

## 1. Purpose

Document testable workflow expectations without implementing tests. This
document lists required test scenarios for future RNICA/HOPE visit
classification behavior — no test code, fixtures, or application behavior
is created here.

## 2. Referral and Election

1. Referral received, election incomplete.
2. Election completed.
3. Initial Assessment due.
4. Initial Assessment completed within 48 hours.
5. Initial Assessment overdue.
6. SNS referral-expiration threshold reached.
7. Referral reactivation.
8. Corrected election date.

## 3. Comprehensive Assessment Package

1. RNICA pending.
2. RNICA complete.
3. MSW ICA pending.
4. SC ICA pending.
5. All required contributions complete.
6. Conditional discipline not required.
7. Authorized exemption.
8. Contribution completed late.
9. Corrected contribution.
10. Package completion recalculation.

## 4. HUV1

1. RN visit Day 5 (before window).
2. RN visit Day 6 (window opens).
3. RN visit Day 15 (window closes).
4. RN visit after HUV1 completed.
5. Duplicate HUV1.
6. Missed HUV1.
7. Late HUV1.
8. Day-14 supervisory fallback accepted.
9. Day-14 supervisory fallback declined.

## 5. HUV2

1. RN visit Day 16 (window opens).
2. RN visit Day 30 (window closes).
3. RN visit after HUV2 completed.
4. Duplicate HUV2.
5. Missed HUV2.
6. Late HUV2.
7. Day-28 CHHA supervisory fallback.
8. Day-28 LVN supervisory fallback.
9. Fallback accepted.
10. Fallback declined.

## 6. SFV

1. Trigger at HOPE Admission.
2. Trigger at HUV1.
3. Trigger at HUV2.
4. No qualifying trigger.
5. RN completes SFV.
6. LPN/LVN completes permitted SFV items.
7. SFV late.
8. SFV corrected.
9. Initial Assessment incorrectly selected as SFV.
10. LVN visit identifies qualifying severe symptom during first 30 days.
11. LVN visit identifies qualifying severe symptom after HOPE Admission.
12. LVN visit identifies qualifying severe symptom during HUV1 window.
13. LVN visit identifies qualifying severe symptom during HUV2 window.
14. RN review requested from LVN severe-symptom finding.
15. RN review completed and SFV determined applicable.
16. RN review completed and SFV determined not applicable.
17. LVN severe symptom documented but RN review not completed.
18. Attempt to automatically classify LVN visit as SFV.
19. Attempt to mark SFV complete without RN review documentation.

## 7. Discipline Security

1. RN login with RN visit.
2. LVN login attempting RN-only assessment.
3. CHHA login attempting HUV.
4. Assigned discipline mismatch.
5. Expired credential.
6. Inactive worker.
7. Authorized reassignment.

## 8. Recertification

1. Recertification due.
2. Recertification not due.
3. Stability requiring explanation.
4. Improvement requiring explanation.
5. Missing physician narrative.
6. RN assessment incorrectly represented as certification.

## 9. Finalization

1. RNICA draft.
2. Blocking validation present.
3. RNICA finalized.
4. HOPE map visible after validation.
5. Post-finalization correction.
6. Post-finalization amendment.
7. Silent overwrite attempt.
8. Source record changed after finalization.

## 10. Documentation-Evidence Failures

1. Schedule completed without note.
2. HUV status without source visit.
3. Supervisory completion without supervisory evidence.
4. Comprehensive package complete with missing discipline contribution.
5. iQIES-ready status without validated record.

## 11. Expected Result Format

For each scenario, document:

- Preconditions
- Actor
- Source dates
- Source records
- Action
- Suggested classification
- Blocking conditions
- Required evidence
- Audit events
- Final state
- Authority classification

## 12. Traceability

Each scenario above traces to a rule in
`RNICA_ASSESSMENT_VISIT_CLASSIFICATION_RULES.md` and/or a row in
`RNICA_VISIT_CLASSIFICATION_DECISION_TABLE.md`. When implementation is
eventually authorized, these scenarios should become the basis for actual
automated test cases — not before.

## 13. Implementation Boundary

Test implementation remains `NOT_AUTHORIZED`.
