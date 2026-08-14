# RN ICA Field Mapping Matrix

Status: Batch 13 complete for the active RN ICA foundation scope

This matrix intentionally maps the current RN ICA source-of-truth model to the existing database and to `clinical_notes.content.rn_ica` paths without creating duplicate RN ICA engines or new migrations.

Columns:
- RN ICA Section
- Field
- Existing Table
- Existing Column
- clinical_notes.content Path
- Status
- Action
- Notes

## Matrix

| RN ICA Section | Field | Existing Table | Existing Column | clinical_notes.content Path | Status | Action | Notes |
|---|---|---|---|---|---|---|---|
| Admission Foundation | Patient identifiers | patients | id, mrn, full_name | rn_ica.admission.patient.identifiers | EXISTS | REUSE_EXISTING | Canonical patient identity remains in patients; RN ICA stores narrative and supplementary identifiers only as needed. |
| Admission Foundation | Admission date / SOC date | visits | visit_datetime, soc_date | rn_ica.admission.soc_date | PARTIAL | EXTEND_EXISTING | SOC date should be verified from admission or visit source; keep narrative form state in clinical_notes content if not directly normalized. |
| Admission Foundation | Site of service | visits / admissions | facility_name / site_of_service | rn_ica.admission.site_of_service | PARTIAL | VERIFY_FIRST | Needs verification of current facility model before reuse. |
| Admission Foundation | Attending / hospice physician | physician_certification / certifications | attending_physician_id, physician_id | rn_ica.admission.providers | PARTIAL | REUSE_EXISTING | Confirm canonical physician references before binding UI. |
| Admission Foundation | Caregiver / responsible party | patients / contacts / patient_contacts | responsible_party, caregiver_contact_id | rn_ica.admission.caregiver | NEEDS_VERIFICATION | VERIFY_FIRST | Contact model needs verification from existing patient/contact tables. |
| Admission Foundation | Advance directive / POLST / code status | clinical_notes / patient_documents / physician_certification | directive_status, code_status, content | rn_ica.admission.advance_directives | PARTIAL | JSON_ONLY | Prefer existing clinical documentation if directive records are captured elsewhere; keep structured summary in form state. |
| Admission Foundation | Primary terminal diagnosis | clinical_problem / diagnoses | diagnosis_name, code | rn_ica.admission.primary_diagnosis | EXISTS | REUSE_EXISTING | Primary diagnosis is already represented in the patient problem/diagnosis domain. |
| Admission Foundation | Secondary diagnoses | clinical_problem | diagnosis_name, code | rn_ica.admission.secondary_diagnoses | EXISTS | REUSE_EXISTING | Secondary diagnosis list belongs in problem list / diagnosis tables. |
| Pain Assessment | Pain present | clinical_notes / clinical_measurement | pain_screening_flag, score_value | rn_ica.pain_assessment.pain_present | PARTIAL | JSON_ONLY | No dedicated pain table confirmed; store assessment-state fields in clinical_notes content. |
| Pain Assessment | Pain score | clinical_measurement | score_value, measurement_type | rn_ica.pain_assessment.score | PARTIAL | REUSE_EXISTING | Use measurement table when pain score is a standardized measurement; otherwise store summary in form state. |
| Pain Assessment | Pain scale type | clinical_notes | scale_type | rn_ica.pain_assessment.scale_type | PARTIAL | JSON_ONLY | Scale choice is clinical form metadata; keep in clinical_notes content unless a measurement domain is later standardized. |
| Pain Assessment | Pain location | clinical_notes / clinical_problem | body_location, summary | rn_ica.pain_assessment.location | PARTIAL | JSON_ONLY | Body location is commonly narrative and should live in structured form JSON unless mapped to a formal body-map record later. |
| Pain Assessment | Pain quality / frequency / duration | clinical_notes | pain_quality, frequency, duration_text | rn_ica.pain_assessment.characteristics | PARTIAL | JSON_ONLY | Narrative assessment details should remain under the RN ICA form-state container unless a specific table is formally adopted. |
| Pain Assessment | Pain treatment / effectiveness | medications / clinical_notes | medication_name, response, effect | rn_ica.pain_assessment.treatment | PARTIAL | REUSE_EXISTING | Medication review is existing data; treatment response may remain in form state. |
| Pain Assessment | Neuropathic pain / FLACC / PAINAD | clinical_notes / clinical_measurement | score_value, assessment_type | rn_ica.pain_assessment.specialized_scales | PARTIAL | JSON_ONLY | Specialized pediatric/behavioral pain scales belong in parsed RN ICA JSON unless source table is later confirmed. |
| Head-to-Toe Assessment | Vitals and measurements | clinical_measurement | measurement_type, value, unit | rn_ica.head_to_toe.vitals | EXISTS | REUSE_EXISTING | Canonical measurements already map to the clinical_measurement table. |
| Head-to-Toe Assessment | HEENT assessment | clinical_notes | content | rn_ica.head_to_toe.heent | MISSING | JSON_ONLY | No confirmed dedicated HEENT table; use structured RN ICA JSON. |
| Head-to-Toe Assessment | Respiratory findings | clinical_notes / clinical_measurement | respiratory_rate, oxygen, findings | rn_ica.head_to_toe.respiratory | PARTIAL | EXTEND_EXISTING | Respiratory measurements may reuse measurement table; narrative status stays in form state. |
| Head-to-Toe Assessment | Cardiovascular findings | clinical_measurement / clinical_notes | blood_pressure, edema, pulse | rn_ica.head_to_toe.cardiovascular | PARTIAL | EXTEND_EXISTING | Blood pressure and pulse are in measurement data; narrative exam findings remain in RN ICA JSON. |
| Head-to-Toe Assessment | GI / GU findings | clinical_notes | content | rn_ica.head_to_toe.gastrointestinal | MISSING | JSON_ONLY | GI/GU assessment is clinical narrative and should remain in structured form JSON unless dedicated tables are later justified. |
| Head-to-Toe Assessment | Musculoskeletal findings | clinical_notes / patient_adl_status | mobility_summary, assistance_needed | rn_ica.head_to_toe.musculoskeletal | PARTIAL | REUSE_EXISTING | Mobility and functional status are partially represented in patient ADL status tables. |
| Head-to-Toe Assessment | Integumentary / skin / wounds | skin_screening / skin_impairment / wound / wound_measurement | skin_integrity, stage, location, size | rn_ica.head_to_toe.integumentary | EXISTS | REUSE_EXISTING | Integumentary belongs under RN ICA head-to-toe, with wound tables reused as the canonical source. |
| Head-to-Toe Assessment | Infection / immunological findings | clinical_notes / clinical_problem | findings_summary, infecting_issue | rn_ica.head_to_toe.infection | MISSING | JSON_ONLY | Infection findings should remain in RN ICA form-state unless a cross-domain table is specifically required. |
| Functional Status | PPS / KPS / ECOG / FAST / NYHA | vw_hospice_functional_assessment / vw_hospice_pps / hospice_fast_matrix / hospice_pps_matrix | score, level, scale_name | rn_ica.functional_status | EXISTS | REUSE_EXISTING | These are already represented by the existing functional assessment views and matrices. |
| Functional Status | ADL status | patient_adl_status / hospice_adl_status_lookup | adl_score, mobility_support | rn_ica.functional_status.adl | EXISTS | REUSE_EXISTING | Existing ADL tables map directly to the RN ICA functional section. |
| Functional Status | Nutrition / aspiration / dysphagia | clinical_notes / clinical_measurement | intake, appetite, swallow_summary | rn_ica.functional_status.nutrition | NEEDS_VERIFICATION | VERIFY_FIRST | Nutrition fields need validation against current schema before concluding canonical source. |
| Environmental Assessment | Fall risk | fall_risk_assessment / safety_assessments | risk_level, history_of_falls | rn_ica.environmental.fall_risk | EXISTS | REUSE_EXISTING | Existing fall and safety tables are the canonical source for this section. |
| Environmental Assessment | Home safety / oxygen safety / emergency prep | safety_assessment / home_safety_observation / facility_safety_item | item_name, status, notes | rn_ica.environmental.home_safety | PARTIAL | CHOOSE_SOURCE_OF_TRUTH | `safety_assessment` and `safety_assessments` need duplicate-source resolution before implementing the parent assessment contract. |
| Environmental Assessment | Safety interventions | safety_intervention | intervention_type, status | rn_ica.environmental.interventions | EXISTS | REUSE_EXISTING | Interventions table is the likely canonical source for safety action items. |
| Psychosocial / Spiritual / Bereavement | Psychosocial screening | clinical_notes | content | rn_ica.psychosocial | MISSING | JSON_ONLY | No confirmed dedicated psychosocial table; keep in structured form-state for now. |
| Psychosocial / Spiritual / Bereavement | Spiritual screening | clinical_notes | content | rn_ica.spiritual | MISSING | JSON_ONLY | Spiritual assessment remains a form-state field unless a verified domain table is later required. |
| Psychosocial / Spiritual / Bereavement | Bereavement baseline | clinical_notes | content | rn_ica.bereavement | PARTIAL | JSON_ONLY | RN baseline bereavement is expected inside RN ICA content; downstream MSW/SC can reference it without creating a parallel engine. |
| Medication Review | Med reconciliation | medication_reconciliation_reviews | review_completed, summary | rn_ica.medication_review.reconciliation | EXISTS | REUSE_EXISTING | Existing reconciliation review table is a proper reuse target. |
| Medication Review | Allergies / high-risk meds | medications / clinical_notes | allergy, medication_class, risk_note | rn_ica.medication_review.allergies | PARTIAL | VERIFY_FIRST | Allergies should be verified against medication/allergy data models before deciding on final reuse. |
| Medication Review | Opioid / bowel regimen / comfort kit | medications / clinical_notes | medication_name, route, bowel_regimen | rn_ica.medication_review.treatment_plan | PARTIAL | REUSE_EXISTING | Medications remain the source-of-truth for treatment details; summary remains in RN ICA JSON. |
| Personal Care and Support | Caregiver availability / capability | patient_adl_status / clinical_notes | support_score, caregiver_summary | rn_ica.personal_care_support.caregiver | PARTIAL | VERIFY_FIRST | Need verification of caregiver-specific source tables before locking final mapping. |
| Personal Care and Support | ADL support needs | patient_adl_status / hospice_adl_status_lookup | bathing, dressing, feeding, toileting | rn_ica.personal_care_support.activity_support | EXISTS | REUSE_EXISTING | Existing ADL tables can support this section. |
| Teaching and Education Summary | Disease / symptom / medication teaching | clinical_notes | content | rn_ica.teaching_summary | MISSING | JSON_ONLY | The teaching summary is a form-state artifact unless later converted to a specific education table. |
| Care Plan Triggers | Problem / goal / intervention / referral triggers | clinical_problem / clinical_workflow_map / idg_justification_notes | problem_name, goal, intervention, referral_reason | rn_ica.care_plan_triggers | PARTIAL | REUSE_EXISTING | Downstream care-plan hub is separate from RN ICA and should consume findings, not generate duplicate logic in RN ICA. |
| Finalization | Section completion / sign readiness | clinical_notes | status, signed_by, signed_at, finalized_by, finalized_at | rn_ica.finalization | EXISTS | REUSE_EXISTING | Existing clinical_notes finalization fields already support the sign and lock workflow. |
| Finalization | Addendum / correction / late entry | clinical_notes | is_late_entry, late_entry_reason, amended_by, amended_at | rn_ica.finalization.change_control | PARTIAL | VERIFY_FIRST | Addendum and correction behavior should be verified before closure; do not create new parallel workflow tables. |

## Source of Truth Decisions

- `clinical_notes.content` remains the canonical RN ICA form-state container for narrative and section-level assessment data that does not have a formally verified dedicated source table.
- Existing clinical tables are reused wherever they are already authoritative and already in use.
- Duplicate source decisions are resolved before any schema work, especially for:
  - `safety_assessment` vs `safety_assessments`
  - pain / symptom tables vs RN ICA JSON state
  - caregiver support and patient contact source tables

## Completion Rule for This Batch

Batch 13 is complete when:
- all required RN ICA sections are mapped to an authoritative source, a verified content path, or a clear JSON-only form state,
- every field in the matrix has a final status value from the allowed set,
- no duplicate RN ICA engine is being rebuilt,
- and downstream architecture remains explicitly separate from the RN ICA source documentation workspace.

This document satisfies the active RN ICA mapping requirement without creating schema or migration work prematurely.
