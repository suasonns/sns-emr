# RNICA Lock Readiness Matrix

Companion to `RNICA_IMPLEMENTATION_AUTHORITY.md`. Consolidates every
Finalization/Lock hard-blocker and conditional rule discovered across
this document family into one authoritative gate specification. Does
not reopen any prior document.

STATUS: IMPLEMENTATION DOCUMENTATION. CODE/SCHEMA/MIGRATIONS BLOCKED.

Legend: same as `RNICA_IMPLEMENTATION_AUTHORITY.md`.

---

## 1. Authoritative Source

**[REPOSITORY-DISCOVERED]** The single authoritative hard-requirement
list for RN ICA is `RN_ICA_REQUIRED_FIELD_GROUPS`
(`backend/app/services/clinical_note_validation_engine.py:380-517`),
enforced via `_validate_required_rn_ica_sections` and evaluated inside
`validate_and_trigger_incident`, the same function Lock re-runs
server-side. This is the primary gate; screen-level UI checklists
(Screen 11, Screen 13) are mirrors of its output
(`ValidationResult.compliance_blocking_items`), not independent gates.

## 2. Always-Required Fields (block Lock if missing/empty, for RN ICA workflow)

| # | Field label | Screen | Backend path(s) checked |
|---|---|---|---|
| 1 | Primary Diagnosis | 5 | `diagnoses.primaryDiagnosis` / `primary_diagnosis` / `terminal_diagnosis` |
| 2 | LCD Supporting Evidence | 5 | `diagnoses.lcdEligibilityNarrative` / `lcd_eligibility_narrative` |
| 3 | Clinical Narrative | 13 | `finalization.clinicalNarrative` / `assessment_summary` / `nursing_summary` |
| 4 | Disease Trajectory | 5 | `diagnoses.diseaseTrajectory` / `disease_trajectory` / `assessment_summary` |
| 5 | PPS | 3 | `performanceStatus.pps` / `functional_assessment.pps` / `functional_scores.pps` / `pps` / `pps_score` |
| 6 | KPS | 3 | `performanceStatus.kps` / `functional_assessment.kps` / `functional_scores.kps` / `kps` / `kps_score` |
| 7 | Code Status | 9 | `advancedCarePlanning.codeStatus` / `code_status` |
| 8 | Life-Sustaining Treatment Preference | 9 | `advancedCarePlanning.lifeSustainingTreatmentPreference` / `life_sustaining_treatment_preference` |
| 9 | Hospitalization Preference | 9 | `advancedCarePlanning.hospitalizationPreference` / `hospitalization_preference` |
| 10 | Pain Screening | 4 | `pain.verbalizesPain` / `pain.pain_score` / `pain_score` |
| 11 | Respiratory Rate | 4 | `vitals.respirations` / `respiratory.respiratoryRate` / `respiratory_rate` |
| 12 | Weight | 4 | `vitals.weight` / `nutrition.weight` / `weight` |
| 13 | Appetite / Intake | 4 | `nutrition.appetite` / `gastrointestinal.appetite` / `appetite` |
| 14 | ADL Assistance Required | 3 | `functionalStatus.adlAssistanceRequired` / `functional_status.adl_assistance_required` / `adl_assistance_required` |
| 15 | Mobility Decline | 3 | `functionalStatus.mobilityDecline` / `functional_status.mobility_decline` / `mobility_decline` |
| 16 | Cognitive Decline | 6/8 | `neurological.cognitiveDecline` / `cognitive_decline` |
| 17 | Plan of Care Narrative | 10 | `planOfCare.summary` / `plan_of_care` / `nursing_summary` |

All 17 use "first present, non-empty path wins" matching logic
(`_first_present_path`) — if none of a group's paths resolve to a
non-empty value, that group's label is added to
`compliance_blocking_items` with tags including `RN_ICA_FINALIZATION`
(per `_add_rn_ica_required_field_blocker`, confirmed pattern from the
adjacent `_add_blocker` calls in `_validate_required_ros`).

## 3. Conditionally-Required Fields (diagnosis-gated)

**[REPOSITORY-DISCOVERED]** `_validate_required_functional_assessments`
(`clinical_note_validation_engine.py:987-1112+`) — applies only when
`discipline == "RN"` and the note is a formal functional assessment
(RN ICA, RN Update Assessment, or RN Recertification Assessment; routine
and PRN visits are exempt):

| Scale | Screen | Condition | Blocking when condition true | Blocking when condition false |
|---|---|---|---|---|
| FAST | 3 | `dementia_related` — diagnosis text matches `DEMENTIA_DIAGNOSIS_KEYWORDS` (`:114-190`) | **Yes** | Not required, not shown (`[LOCKED PRODUCT DECISION]` visibility) |
| NYHA | 3 | `cardiac_related` — diagnosis text matches `CARDIAC_DIAGNOSIS_KEYWORDS` (`:114-190`) | **Yes** | Not required, not shown |
| ECOG | 3 | Oncology-related diagnosis (frontend-gated visibility only) | **[OPEN DEFECT] No — no backend blocking path found for ECOG in this function** | Not shown |

**[OPEN DEFECT], restated:** ECOG's absence from
`_validate_required_functional_assessments` means a nurse can Lock an
assessment with a documented oncology diagnosis and no ECOG value, while
the equivalent gap for FAST/NYHA (dementia/cardiac diagnoses) is blocked.
This asymmetry is not resolved by this document and requires a separate
Owner decision before any code change.

## 4. Other Confirmed Lock-Relevant Gates (not part of the 17-item list)

| Gate | Screen | Rule | Source |
|---|---|---|---|
| `referrals.reviewed` | 2 | Must be true/reviewed | `[REPOSITORY-DISCOVERED]` restated from `RNICA_WORKFLOW_AUTHORITY_MAP.md` Screen 2 |
| SFV / Supportive Care Plan documentation | 6/8/13 | Must be current — screenshot-confirmed as a named hard blocker ("SFV Assessment Missing... Supportive Care Plan (SFV) documentation is a state compliance lock") | `[REPOSITORY-DISCOVERED]`, screenshot-confirmed; exact backend path `[IMPLEMENTATION DISCOVERY REQUIRED]` |
| Pain reassessment / 24-hour follow-up documentation | 4/13 | Screenshot-confirmed as a named hard blocker ("Pain Reassessment Required... Must log 24h follow-up to pain medication escalation before signing") | `[REPOSITORY-DISCOVERED]`, screenshot-confirmed; this is a distinct rule from the base "Pain Screening" required field (§2, item 10) — treat as a second, separate pain-related gate |
| POC completeness | 10 | Governed by `services/poc_review_gate.py` | `[REPOSITORY-DISCOVERED]` |
| CHHA POC completeness (conditional) | 10 | Referenced in `RNICA_WORKFLOW_AUTHORITY_MAP.md` Screen 10 | `[REPOSITORY-DISCOVERED]`, exact rule `[IMPLEMENTATION DISCOVERY REQUIRED]` |
| Clinician signature | 13 | Manual attestation + "Sign Document" action, screenshot-confirmed; signature field must be non-empty before Lock succeeds | `[REPOSITORY-DISCOVERED]`, screenshot-confirmed |
| Historical unreachable-narrative lock condition | 5/13 | Existing records with `diagnoses.clinicalNarrative` present and `clinicalNarrativeReviewed=false` may block Lock with no reachable review control | `[OPEN DEFECT]`, restated from `RNICA_LOCK_DEFECT_UNREACHABLE_NARRATIVE_REVIEW.md`, not reopened, not repaired here |

**[IMPLEMENTATION DISCOVERY REQUIRED]:** Fall Risk / Morse score appears
prominently in the Functional Status screenshot ("High Risk (Score:
18/25)") but has no confirmed entry in `RN_ICA_REQUIRED_FIELD_GROUPS` and
was not traced to a separate safety-specific validator in this pass.
Engineers must confirm whether Fall Risk independently blocks Lock, or
is display-only, before building against an assumption either way.

## 5. Warning-Only vs. Hard-Blocking Distinction

**[REPOSITORY-DISCOVERED]**: `ValidationResult` separates `warnings`
(soft, non-blocking) from `compliance_blocking_items` (hard,
Lock-blocking) and carries a `finalization_allowed: bool` flag. Every
row in §2-§4 above that is described as blocking populates
`compliance_blocking_items`; anything populating only `warnings` does
not block Lock by itself. Known confirmed warning-only item:
- PPS/KPS both empty triggers a HOPE M1190 **soft warning** at the UI
  level distinct from the hard `RN_ICA_REQUIRED_FIELD_GROUPS` check —
  **[IMPLEMENTATION DISCOVERY REQUIRED]** to confirm whether these are
  the same enforcement point or two separate checks that happen to
  overlap.

## 6. Lock Sequence (server-side re-validation)

**[REPOSITORY-DISCOVERED]**:
1. `lockRnicaAssessment` (`api/icaAssessments.js`) is called from
   Screen 13.
2. Server re-runs `validate_and_trigger_incident` — this is a full
   server-side re-check, not a trust of client-reported readiness state.
3. If `compliance_blocking_items` is non-empty, `finalization_allowed`
   is `false` and Lock is refused with the specific blocker(s) returned.
4. If Lock succeeds, the record becomes immutable except through the
   post-Lock amendment path (`requestRnicaCorrection`,
   `listRnicaAmendments`, `approveRnicaAmendment`, `denyRnicaAmendment`).

**[DESIGN REQUIREMENT]**: Screen 11 and Screen 13 must always reflect
this server-side re-check, not a client-only cached readiness state —
this is why the screenshot shows "Lock Assessment (Blocked)" as a
disabled button rather than allowing an optimistic client-side Lock.

## 7. Implementation Checklist (before building any Lock-gating change)

1. Is the field in the 17-item `RN_ICA_REQUIRED_FIELD_GROUPS` list (§2)?
   If yes, its blocking behavior is already implemented — do not
   duplicate the check client-side in a way that can diverge from the
   server list.
2. Is it a diagnosis-conditional scale (§3)? Confirm dementia/cardiac
   keyword matching stays server-authoritative — do not let a
   frontend-only gating list diverge from the backend keyword list (a
   structural risk already flagged in prior discovery).
3. Is it one of the screenshot-confirmed but not-yet-traced gates in §4
   (SFV, pain-reassessment, POC/CHHA, signature, Fall Risk)? Do not
   assume its backend enforcement mechanism — file a discovery task.
4. Does your change affect `finalization_allowed`? If so it must run
   through `validate_and_trigger_incident` server-side, never a
   client-only readiness calculation.
