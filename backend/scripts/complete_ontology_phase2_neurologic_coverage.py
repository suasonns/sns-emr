# scripts/complete_ontology_phase2_neurologic_coverage.py
"""
Neurologic Phase 2 Atomic Concept Coverage Repair.

This script does NOT redesign the Neurologic hierarchy, disease list, family
structure, or schema. It resolves the six already-approved Phase 2 diseases
by name and adds the approved ATOMIC concepts that were identified as
missing from the PR #34 coverage reconciliation:

    - Stroke
    - Hemiplegia
    - Hemiparesis
    - Contracture
    - Dementia Due To Alzheimer's Disease
    - Senile Degeneration of Brain

CONCEPT ATOMICITY
------------------
One clinically distinct concept = one ontology record. Where PR #34 stored
a compressed aggregate record (e.g. "Dysarthria/Aphasia", "Deep Vein
Thrombosis/Pulmonary Embolism", "Physical/Occupational Therapy"), this
script adds the INDIVIDUAL atomic concepts (e.g. "Dysarthria", "Aphasia",
"Deep Vein Thrombosis", "Pulmonary Embolism", "Physical Therapy",
"Occupational Therapy") as their own independent rows.

Per approved decision (Option 2):
    - No active/status column is added to any concept table.
    - No migration, schema, model, or enum change is made.
    - No compressed aggregate record is hard-deleted or modified.
    - Existing compressed records remain present, unchanged, and continue
      to coexist temporarily alongside the new atomic records.
    - Compressed aggregate records are NOT treated as satisfying atomic
      concept coverage -- the atomic concepts are added regardless of
      whether a compressed record already covers the same ground.

Every new atomic concept:
    - is inserted only if a matching (disease_id, name[, category]) row does
      not already exist -- idempotent, safe to re-run
    - receives an active OntologyEvidenceRule with
      patient_fact_requires_evidence = True
    - is never itself a patient-specific fact -- general ontology knowledge
      only, per the existing ontology hard rule

Senile Degeneration of Brain remains a distinct canonical disease. Its
hospice-eligibility-support content (none added by this script; it already
carries general-decline-only support from PR #34) is never grounded in the
Alzheimer's-specific LCD. No Alzheimer's-specific hospice criteria are
attached to it here.

No new disease, family, or body-system row is created by this script; all
six diseases are resolved strictly by existing name. No other body system is
touched.

Run with (from backend/):
    .\\.venv\\Scripts\\python.exe -m scripts.complete_ontology_phase2_neurologic_coverage
"""

from __future__ import annotations

import uuid
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from app.core.database import SessionLocal

import app.models.poc  # noqa: F401
from app.models.ontology_disease_blueprint import (
    OntologyDisease,
    OntologyDiseaseComplication,
    OntologyDiseaseDiagnosticTest,
    OntologyDiseaseEndStageFinding,
    OntologyDiseaseFinding,
    OntologyDiseaseFunctionalImpact,
    OntologyDiseaseHospiceEligibilitySupport,
    OntologyDiseaseLab,
    OntologyDiseaseMedication,
    OntologyDiseaseNutritionalImpact,
    OntologyDiseasePrognosticIndicator,
    OntologyDiseasePsychosocialConcern,
    OntologyDiseaseSpiritualConcern,
    OntologyDiseaseSymptom,
    OntologyDiseaseTreatment,
    OntologyDiseaseTreatmentLimitation,
    OntologyEvidenceRule,
)

STROKE = "Stroke"
HEMIPLEGIA = "Hemiplegia"
HEMIPARESIS = "Hemiparesis"
CONTRACTURE = "Contracture"
ALZ = "Dementia Due To Alzheimer's Disease"
SDB = "Senile Degeneration of Brain"

ALL_DISEASE_NAMES = [STROKE, HEMIPLEGIA, HEMIPARESIS, CONTRACTURE, ALZ, SDB]

CEREBROVASCULAR_SOURCE = (
    "General cerebrovascular-disease, hemiplegia/hemiparesis/contracture clinical "
    "literature -- atomic-concept coverage repair (PR #34 reconciliation)."
)
ALZ_SOURCE = (
    "General Alzheimer's-dementia clinical literature -- atomic-concept coverage repair "
    "(PR #34 reconciliation)."
)
SDB_SOURCE = (
    "General decline/terminal-status clinical literature (non-Alzheimer-specific) -- "
    "atomic-concept coverage repair (PR #34 reconciliation)."
)

EVIDENCE_SOURCE_BY_DISEASE_NAME: Dict[str, str] = {
    STROKE: CEREBROVASCULAR_SOURCE,
    HEMIPLEGIA: CEREBROVASCULAR_SOURCE,
    HEMIPARESIS: CEREBROVASCULAR_SOURCE,
    CONTRACTURE: CEREBROVASCULAR_SOURCE,
    ALZ: ALZ_SOURCE,
    SDB: SDB_SOURCE,
}

# ---------------------------------------------------------------------------
# Small builder helpers -- keep each atomic concept name authoritative while
# generating consistent, non-empty supporting text for the other columns.
# ---------------------------------------------------------------------------


def _sym(name: str, severity: str = None) -> Tuple[str, str, str, str]:
    return (name, f"{name} -- atomic symptom concept (coverage-repair addition).", None, severity)


def _finding(name: str) -> Tuple[str, str]:
    return (name, f"{name} -- atomic clinical finding concept (coverage-repair addition).")


def _lab(name: str) -> Tuple[str, str, str, str, str]:
    return (
        name,
        None,
        None,
        f"{name} -- atomic laboratory concept (coverage-repair addition).",
        None,
    )


def _dx(name: str) -> Tuple[str, str, str, str]:
    return (name, f"{name} -- atomic diagnostic concept (coverage-repair addition).", None, None)


def _comp(name: str) -> Tuple[str, str, str, str]:
    return (name, f"{name} -- atomic complication concept (coverage-repair addition).", None, None)


def _prog(name: str) -> Tuple[str, str, str]:
    return (name, f"{name} -- atomic prognostic indicator (coverage-repair addition).", None)


def _func(name: str) -> Tuple[str, str, str]:
    return (name, f"{name} -- atomic functional impact concept (coverage-repair addition).", None)


def _nutr(name: str) -> Tuple[str, str, str]:
    return (name, f"{name} -- atomic nutritional impact concept (coverage-repair addition).", None)


def _tx(name: str, category: str) -> Tuple[str, str, str]:
    return (name, category, f"{name} -- atomic treatment concept (coverage-repair addition).")


def _med(name: str) -> Tuple[str, str, str, str, str, str]:
    return (name, None, f"{name} -- atomic medication concept (coverage-repair addition).", None, None, None)


def _limit(name: str, category: str) -> Tuple[str, str, str, str, str]:
    return (
        name,
        category,
        f"{name} -- atomic treatment-limitation concept (coverage-repair addition).",
        None,
        None,
    )


def _endstage(name: str) -> Tuple[str, str, str, str, str]:
    return (
        name,
        f"{name} -- atomic end-stage finding concept (coverage-repair addition).",
        None,
        None,
        None,
    )


# ---------------------------------------------------------------------------
# STROKE
# ---------------------------------------------------------------------------

STROKE_SYMPTOMS = [
    # Splits of PR #34 compressed symptom records.
    _sym("Dysarthria"), _sym("Aphasia"), _sym("Ataxia"), _sym("Imbalance"),
    _sym("Confusion"), _sym("Altered Mental Status"), _sym("Hemiparesis"), _sym("Hemiplegia"),
    _sym("Vision Loss"), _sym("Hemianopia"), _sym("Sudden Vision Loss"), _sym("Visual Field Deficit"),
    # Manifest-approved additional atomic symptoms.
    _sym("Expressive Aphasia"), _sym("Receptive Aphasia"), _sym("Global Aphasia"),
    _sym("Facial Weakness"), _sym("Facial Numbness"), _sym("Unilateral Sensory Loss"),
    _sym("Homonymous Hemianopia"), _sym("Diplopia"), _sym("Gaze Disturbance"),
    _sym("Unilateral Neglect"), _sym("Vertigo"), _sym("Loss of Coordination"),
    _sym("Nausea"), _sym("Vomiting"), _sym("Seizure"), _sym("Difficulty Walking"),
]

STROKE_FINDINGS = [
    _finding("Facial Droop"), _finding("Pronator Drift"), _finding("Focal Motor Deficit"),
    _finding("Focal Sensory Deficit"), _finding("Graded Motor Weakness"), _finding("Babinski Sign"),
    _finding("Gaze Deviation"), _finding("Visual Field Deficit"), _finding("Limb Ataxia"),
    _finding("Abnormal Gait"), _finding("Impaired Protective Reflexes"), _finding("Impaired Gag Reflex"),
    _finding("Impaired Swallow Evaluation"), _finding("Reduced Level of Consciousness"),
    _finding("Absent Verbal Response"), _finding("Absent Withdrawal Response"),
    _finding("Abnormal Brainstem Response"),
]

STROKE_DIAGNOSTICS = [
    _dx("Diffusion-Weighted Brain MRI"), _dx("MR Angiography"), _dx("Carotid Duplex Ultrasound"),
    _dx("Cerebral Angiography"), _dx("Echocardiogram"), _dx("Electrocardiogram"),
    _dx("Cardiac Rhythm Monitoring"), _dx("Modified Barium Swallow Study"),
    _dx("Fiberoptic Endoscopic Evaluation of Swallowing"), _dx("Neurologic Examination"),
    _dx("NIH Stroke Scale Assessment"),
]

STROKE_LABS = [
    _lab("Complete Blood Count"), _lab("Comprehensive Metabolic Panel"), _lab("Serum Glucose"),
    _lab("Hemoglobin A1c"), _lab("Prothrombin Time"), _lab("INR"),
    _lab("Partial Thromboplastin Time"), _lab("Lipid Panel"), _lab("Cardiac Troponin"),
    _lab("Serum Creatinine"), _lab("Serum Albumin"),
]

STROKE_COMPLICATIONS = [
    _comp("Aphasia"), _comp("Dysarthria"), _comp("Dysphagia"), _comp("Recurrent Aspiration"),
    _comp("Pulmonary Embolism"), _comp("Deep Vein Thrombosis"), _comp("Malnutrition"), _comp("Dehydration"),
    _comp("Spasticity"), _comp("Shoulder Subluxation"), _comp("Hemorrhagic Transformation"),
    _comp("Cerebral Edema"), _comp("Obstructive Hydrocephalus"), _comp("Communication Impairment"),
    _comp("Cognitive Impairment"), _comp("Urinary Incontinence"), _comp("Bowel Incontinence"),
]

STROKE_PROGNOSTIC_INDICATORS = [
    _prog("Increasing NIH Stroke Scale Score"), _prog("Large Infarct Territory"),
    _prog("Bilateral Cerebral Involvement"), _prog("Large Anterior Infarction"),
    _prog("Cortical and Subcortical Involvement"), _prog("Basilar Artery Occlusion"),
    _prog("Bilateral Vertebral Artery Occlusion"), _prog("Large-Volume Intracranial Hemorrhage"),
    _prog("Intraventricular Hemorrhage Extension"), _prog("Midline Shift"),
    _prog("Obstructive Hydrocephalus"), _prog("Persistent Dysphagia"), _prog("Recurrent Aspiration"),
    _prog("Declining Level of Consciousness"), _prog("Severe Functional Dependence"),
    _prog("Continuing Weight Loss"), _prog("Inadequate Calorie Intake"), _prog("Inadequate Fluid Intake"),
    _prog("Low Serum Albumin When Documented"), _prog("Recurrent Serious Infection"),
    _prog("Refractory Pressure Injury"),
]

STROKE_TREATMENTS = [
    _tx("Physical Therapy", "SUPPORTIVE"), _tx("Occupational Therapy", "SUPPORTIVE"),
    _tx("Speech Therapy", "SUPPORTIVE"), _tx("Swallow Therapy", "SUPPORTIVE"),
    _tx("Thrombolytic Therapy", "DISEASE_DIRECTED"), _tx("Mechanical Thrombectomy", "DISEASE_DIRECTED"),
    _tx("Antiplatelet Therapy", "DISEASE_DIRECTED"),
    _tx("Anticoagulation for Documented Cardioembolic Indication", "DISEASE_DIRECTED"),
    _tx("Blood Pressure Management", "DISEASE_DIRECTED"), _tx("Statin Therapy", "DISEASE_DIRECTED"),
    _tx("Seizure Management", "DISEASE_DIRECTED"), _tx("Aspiration Precautions", "SUPPORTIVE"),
    _tx("Range-of-Motion Program", "SUPPORTIVE"), _tx("Spasticity Management", "SUPPORTIVE"),
    _tx("Assistive Communication Support", "SUPPORTIVE"), _tx("Texture-Modified Diet", "SUPPORTIVE"),
    _tx("Enteral Feeding Consideration", "SUPPORTIVE"),
]

STROKE_MEDICATIONS = [
    _med("Aspirin"), _med("Antiplatelet Therapy"), _med("Baclofen"), _med("Tizanidine"),
    _med("Clopidogrel"), _med("Alteplase"), _med("Tenecteplase"), _med("Atorvastatin"),
    _med("Anticoagulant Therapy for Documented Cardioembolic Indication"), _med("Botulinum Toxin"),
    _med("Antiseizure Medication for Documented Seizure"), _med("Analgesic Therapy for Documented Pain"),
]

STROKE_FUNCTIONAL_IMPACTS = [
    _func("Ambulation Dependence"), _func("Dressing Dependence"), _func("Bathing Dependence"),
    _func("Feeding Dependence"), _func("Toileting Dependence"), _func("Continence Dependence"),
    _func("Swallowing Dependence"), _func("Wheelchair Dependence"), _func("Loss of Dominant-Hand Function"),
    _func("Impaired Safety Awareness"), _func("Need for Continuous Supervision"), _func("Total ADL Dependence"),
]

STROKE_NUTRITIONAL_IMPACTS = [
    _nutr("Texture-Modified Diet"), _nutr("Thickened Liquid Requirement"),
    _nutr("Aspiration-Risk Nutrition Plan"), _nutr("Enteral Feeding Consideration"),
    _nutr("Inadequate Oral Intake"), _nutr("Inadequate Fluid Intake"), _nutr("Protein-Calorie Malnutrition"),
    _nutr("Low Serum Albumin When Documented"),
]

STROKE_TREATMENT_LIMITATIONS = [
    _limit("Thrombolysis Not a Candidate", "NOT_A_CANDIDATE"),
    _limit("Thrombectomy Not a Candidate", "NOT_A_CANDIDATE"),
    _limit("Anticoagulation Contraindicated", "TREATMENT_CONTRAINDICATED"),
    _limit("Anticoagulation Declined", "TREATMENT_DECLINED"),
    _limit("Artificial Nutrition Declined", "TREATMENT_DECLINED"),
    _limit("Hospital Transfer Declined", "TREATMENT_DECLINED"),
    _limit("Surgical Intervention Not a Candidate", "NOT_A_CANDIDATE"),
]

STROKE_END_STAGE_FINDINGS = [
    _endstage("Persistent Minimally Conscious State"), _endstage("Global Functional Dependence"),
    _endstage("Inability To Maintain Oral Nutrition"), _endstage("Inability To Maintain Hydration"),
    _endstage("Recurrent Aspiration Pneumonia"), _endstage("Severe Persistent Dysphagia"),
    _endstage("Progressive Loss of Consciousness"), _endstage("Bedbound With Total ADL Dependence"),
]

# ---------------------------------------------------------------------------
# HEMIPLEGIA
# ---------------------------------------------------------------------------

HEMIPLEGIA_SYMPTOMS = [
    _sym("Shoulder Pain"), _sym("Shoulder Subluxation Symptoms"), _sym("Painful Muscle Spasm"),
    _sym("Chronic Pain"),
]
HEMIPLEGIA_FINDINGS = [
    _finding("Zero of Five Motor Strength"), _finding("Flaccid Tone"), _finding("Spastic Tone"),
    _finding("Shoulder Subluxation"), _finding("Abnormal Limb Positioning"), _finding("Dependent Edema"),
]
HEMIPLEGIA_DIAGNOSTICS = [
    _dx("Tone Assessment"), _dx("Range-of-Motion Measurement"),
    _dx("Electromyography When Differential Diagnosis Requires It"),
    _dx("Nerve Conduction Study When Differential Diagnosis Requires It"),
]
HEMIPLEGIA_COMPLICATIONS = [
    _comp("Shoulder-Hand Syndrome"), _comp("Deep Vein Thrombosis"), _comp("Skin Breakdown"),
    _comp("Hygiene Difficulty"),
]
HEMIPLEGIA_TREATMENTS = [
    _tx("Physical Therapy", "SUPPORTIVE"), _tx("Occupational Therapy", "SUPPORTIVE"),
    _tx("Positioning Program", "SUPPORTIVE"), _tx("Passive Range-of-Motion Program", "SUPPORTIVE"),
    _tx("Splinting", "SUPPORTIVE"), _tx("Assistive Device Fitting", "SUPPORTIVE"),
    _tx("Spasticity Management", "SUPPORTIVE"), _tx("Shoulder Protection Program", "SUPPORTIVE"),
]
HEMIPLEGIA_MEDICATIONS = [
    _med("Tizanidine"), _med("Botulinum Toxin"), _med("Analgesic Therapy for Documented Pain"),
]
HEMIPLEGIA_FUNCTIONAL_IMPACTS = [
    _func("Wheelchair Dependence"), _func("Dressing Dependence"), _func("Bathing Dependence"),
    _func("Toileting Dependence"), _func("Impaired Bed Mobility"), _func("Loss of Functional Use of Affected Side"),
]
HEMIPLEGIA_TREATMENT_LIMITATIONS = [
    _limit("Spasticity Treatment Declined", "TREATMENT_DECLINED"),
    _limit("Splinting Not Tolerated", "TREATMENT_INTOLERANT"),
    _limit("Surgical Intervention Not a Candidate", "NOT_A_CANDIDATE"),
]

# ---------------------------------------------------------------------------
# HEMIPARESIS
# ---------------------------------------------------------------------------

HEMIPARESIS_SYMPTOMS = [
    _sym("Reduced Grip Strength"), _sym("Fatigability of Affected Limb"), _sym("Imbalance"),
]
HEMIPARESIS_FINDINGS = [_finding("Reflex Asymmetry"), _finding("Pronator Drift")]
HEMIPARESIS_DIAGNOSTICS = [
    _dx("Serial Motor Strength Assessment"), _dx("Gait Assessment"),
    _dx("Electromyography When Differential Diagnosis Requires It"),
    _dx("Nerve Conduction Study When Differential Diagnosis Requires It"),
]
HEMIPARESIS_COMPLICATIONS = [_comp("Progressive Spasticity"), _comp("Contracture"), _comp("Loss of Independence")]
HEMIPARESIS_TREATMENTS = [
    _tx("Strength and Mobility Program", "SUPPORTIVE"), _tx("Positioning Program", "SUPPORTIVE"),
    _tx("Range-of-Motion Program", "SUPPORTIVE"), _tx("Assistive Device Fitting", "SUPPORTIVE"),
    _tx("Ankle-Foot Orthosis Evaluation", "SUPPORTIVE"), _tx("Spasticity Management", "SUPPORTIVE"),
]
HEMIPARESIS_MEDICATIONS = [
    _med("Baclofen for Documented Spasticity"), _med("Tizanidine for Documented Spasticity"),
    _med("Botulinum Toxin for Documented Focal Spasticity"), _med("Analgesic Therapy for Documented Pain"),
]
HEMIPARESIS_FUNCTIONAL_IMPACTS = [_func("Reduced Dexterity"), _func("Reduced Functional Reach")]

# ---------------------------------------------------------------------------
# CONTRACTURE
# ---------------------------------------------------------------------------

CONTRACTURE_SYMPTOMS = [
    _sym("Visible Joint Deformity"), _sym("Positioning Discomfort"), _sym("Range-of-Motion Limited by Pain"),
]
CONTRACTURE_FINDINGS = [
    _finding("Joint Position Abnormality"), _finding("Skin-to-Skin Contact at Flexion Crease"),
    _finding("Pressure Area at Contracted Joint"),
]
CONTRACTURE_DIAGNOSTICS = [
    _dx("Goniometric Range-of-Motion Measurement"), _dx("Functional Positioning Assessment"),
    _dx("Imaging When Heterotopic Ossification Is Suspected"),
]
CONTRACTURE_COMPLICATIONS = [
    _comp("Hygiene-Related Infection Risk"), _comp("Further Mobility Loss"), _comp("Caregiver Handling Difficulty"),
]
CONTRACTURE_TREATMENTS = [
    _tx("Serial Casting", "SUPPORTIVE"), _tx("Passive Range-of-Motion Program", "SUPPORTIVE"),
    _tx("Surgical Release for Appropriate Candidates", "DISEASE_DIRECTED"),
    _tx("Comfort-Focused Positioning", "HOSPICE"),
]
CONTRACTURE_MEDICATIONS = [_med("Botulinum Toxin for Documented Spasticity")]
CONTRACTURE_TREATMENT_LIMITATIONS = [
    _limit("Surgical Release Not a Candidate", "NOT_A_CANDIDATE"),
    _limit("Splinting Declined", "TREATMENT_DECLINED"),
    _limit("Splinting Not Tolerated", "TREATMENT_INTOLERANT"),
    _limit("Serial Casting Not Tolerated", "TREATMENT_INTOLERANT"),
    _limit("Comfort-Focused Management Selected", "COMFORT_FOCUSED"),
]

# ---------------------------------------------------------------------------
# DEMENTIA DUE TO ALZHEIMER'S DISEASE
# ---------------------------------------------------------------------------

ALZ_SYMPTOMS = [
    _sym("Behavioral Symptoms"), _sym("Psychological Symptoms"),
    _sym("Short-Term Memory Loss"), _sym("Long-Term Memory Loss"), _sym("Disorientation to Time"),
    _sym("Disorientation to Place"), _sym("Disorientation to Person"), _sym("Word-Finding Difficulty"),
    _sym("Aphasia"), _sym("Apraxia"), _sym("Agnosia"), _sym("Impaired Executive Function"),
    _sym("Impaired Judgment"), _sym("Sundowning"), _sym("Delusion"), _sym("Hallucination"),
    _sym("Anxiety"), _sym("Apathy"), _sym("Loss of Meaningful Verbal Communication"), _sym("Dysphagia"),
    _sym("Feeding Difficulty"), _sym("Urinary Incontinence"), _sym("Fecal Incontinence"),
]
ALZ_FINDINGS = [
    _finding("Impaired Recent Memory"), _finding("Impaired Remote Memory"), _finding("Limited Intelligible Speech"),
    _finding("Loss of Independent Ambulation"), _finding("Loss of Decision-Making Capacity"),
]
ALZ_DIAGNOSTICS = [
    _dx("Functional Assessment Staging"), _dx("Mini-Mental State Examination When Available"),
    _dx("Montreal Cognitive Assessment When Available"), _dx("Brain CT Review"),
    _dx("Thyroid-Stimulating Hormone"), _dx("Vitamin B12"), _dx("Medication Review for Reversible Contributors"),
    _dx("Delirium Evaluation When Acute Change Is Present"),
]
ALZ_COMPLICATIONS = [
    _comp("Delirium Superimposed on Dementia"), _comp("Wandering-Related Injury"), _comp("Aspiration"),
    _comp("Dehydration"), _comp("Weight Loss"), _comp("Pyelonephritis"), _comp("Recurrent Fever After Antibiotics"),
    _comp("Caregiver Exhaustion"), _comp("Malnutrition"),
]
ALZ_PROGNOSTIC_INDICATORS = [_prog("Recurrent Infection"), _prog("Recurrent Aspiration")]
ALZ_TREATMENTS = [_tx("Behavioral Management", "SUPPORTIVE"), _tx("Environmental Management", "SUPPORTIVE")]
ALZ_MEDICATIONS = [
    _med("Rivastigmine"), _med("Galantamine"), _med("Analgesic Therapy for Documented Pain"),
    _med("Antipsychotic Therapy Only for Documented Indication and Review"), _med("Benzodiazepine Risk Review"),
    _med("Medication Burden Review"),
]
ALZ_FUNCTIONAL_IMPACTS = [
    _func("Ambulation Dependence"), _func("Transfer Dependence"), _func("Dressing Dependence"),
    _func("Bathing Dependence"), _func("Toileting Dependence"), _func("Feeding Dependence"),
    _func("Continence Dependence"), _func("Communication Dependence"), _func("Need for Continuous Supervision"),
    _func("Total Care Requirement"),
]
ALZ_NUTRITIONAL_IMPACTS = [
    _nutr("Feeding Dependence"), _nutr("Prolonged Mealtime"), _nutr("Reduced Food Intake"),
    _nutr("Reduced Fluid Intake"), _nutr("Dehydration"), _nutr("Protein-Calorie Malnutrition"),
    _nutr("Inability To Maintain Sufficient Calories"), _nutr("Inability To Maintain Sufficient Fluids"),
]
ALZ_TREATMENT_LIMITATIONS = [
    _limit("Artificial Hydration Declined", "TREATMENT_DECLINED"),
    _limit("Hospital Transfer Declined", "TREATMENT_DECLINED"),
    _limit("Disease-Directed Medication Discontinued", "TREATMENT_DISCONTINUED"),
    _limit("Rehabilitation Not Beneficial", "NOT_A_CANDIDATE"),
]
ALZ_END_STAGE_FINDINGS = [
    _endstage("Unable To Ambulate Without Assistance"), _endstage("Unable To Dress Without Assistance"),
    _endstage("Unable To Bathe Without Assistance"), _endstage("Urinary and Fecal Incontinence"),
    _endstage("Six or Fewer Intelligible Words"), _endstage("No Consistently Meaningful Communication"),
    _endstage("Severe Dysphagia"), _endstage("Recurrent Aspiration"), _endstage("Recurrent Serious Infection"),
    _endstage("Bedbound Status"), _endstage("Inability To Maintain Nutrition and Hydration"),
]

# ---------------------------------------------------------------------------
# SENILE DEGENERATION OF BRAIN
# ---------------------------------------------------------------------------

SDB_SYMPTOMS = [
    _sym("Memory Impairment"), _sym("Disorientation"), _sym("Impaired Judgment"),
    _sym("Impaired Executive Function"), _sym("Communication Decline"), _sym("Behavioral Change"),
    _sym("Feeding Difficulty"), _sym("Continence Decline"), _sym("Dysphagia"),
]
SDB_FINDINGS = [_finding("Objective Cognitive Impairment")]
SDB_DIAGNOSTICS = [
    _dx("Neurologic Examination"), _dx("Functional Assessment"), _dx("Evaluation for Reversible Contributors"),
]
SDB_COMPLICATIONS = [
    _comp("Falls"), _comp("Delirium"), _comp("Dehydration"), _comp("Aspiration"),
    _comp("Aspiration Pneumonia"), _comp("Pressure Injury"),
]
SDB_PROGNOSTIC_INDICATORS = [_prog("Progressive Functional Loss"), _prog("Progressive Cognitive Decline")]
SDB_TREATMENTS = [
    _tx("Safety Supervision", "SUPPORTIVE"), _tx("Behavioral Symptom Review", "SUPPORTIVE"),
    _tx("Medication Review", "SUPPORTIVE"), _tx("Nutrition and Hydration Support", "SUPPORTIVE"),
    _tx("Aspiration Precautions", "SUPPORTIVE"), _tx("Caregiver Education", "SUPPORTIVE"),
    _tx("Comfort-Focused Care", "HOSPICE"),
]
SDB_FUNCTIONAL_IMPACTS = [
    _func("Functional Dependence"), _func("Impaired Safety Awareness"), _func("Reduced Meaningful Communication"),
    _func("Increasing ADL Dependence"), _func("Loss of Ambulation"), _func("Communication Loss"),
    _func("Ambulation Dependence"), _func("Transfer Dependence"), _func("Dressing Dependence"),
    _func("Bathing Dependence"), _func("Toileting Dependence"), _func("Feeding Dependence"),
    _func("Communication Dependence"),
]
SDB_NUTRITIONAL_IMPACTS = [
    _nutr("Nutritional Decline"), _nutr("Reduced Oral Intake"), _nutr("Weight Loss"), _nutr("Dehydration Risk"),
]

# ---------------------------------------------------------------------------
# Per-domain rows-by-disease maps
# ---------------------------------------------------------------------------

SYMPTOMS = {
    STROKE: STROKE_SYMPTOMS, HEMIPLEGIA: HEMIPLEGIA_SYMPTOMS, HEMIPARESIS: HEMIPARESIS_SYMPTOMS,
    CONTRACTURE: CONTRACTURE_SYMPTOMS, ALZ: ALZ_SYMPTOMS, SDB: SDB_SYMPTOMS,
}
FINDINGS = {
    STROKE: STROKE_FINDINGS, HEMIPLEGIA: HEMIPLEGIA_FINDINGS, HEMIPARESIS: HEMIPARESIS_FINDINGS,
    CONTRACTURE: CONTRACTURE_FINDINGS, ALZ: ALZ_FINDINGS, SDB: SDB_FINDINGS,
}
LABS = {STROKE: STROKE_LABS}
DIAGNOSTICS = {
    STROKE: STROKE_DIAGNOSTICS, HEMIPLEGIA: HEMIPLEGIA_DIAGNOSTICS, HEMIPARESIS: HEMIPARESIS_DIAGNOSTICS,
    CONTRACTURE: CONTRACTURE_DIAGNOSTICS, ALZ: ALZ_DIAGNOSTICS, SDB: SDB_DIAGNOSTICS,
}
COMPLICATIONS = {
    STROKE: STROKE_COMPLICATIONS, HEMIPLEGIA: HEMIPLEGIA_COMPLICATIONS, HEMIPARESIS: HEMIPARESIS_COMPLICATIONS,
    CONTRACTURE: CONTRACTURE_COMPLICATIONS, ALZ: ALZ_COMPLICATIONS, SDB: SDB_COMPLICATIONS,
}
PROGNOSTIC_INDICATORS = {
    STROKE: STROKE_PROGNOSTIC_INDICATORS, ALZ: ALZ_PROGNOSTIC_INDICATORS, SDB: SDB_PROGNOSTIC_INDICATORS,
}
TREATMENTS = {
    STROKE: STROKE_TREATMENTS, HEMIPLEGIA: HEMIPLEGIA_TREATMENTS, HEMIPARESIS: HEMIPARESIS_TREATMENTS,
    CONTRACTURE: CONTRACTURE_TREATMENTS, ALZ: ALZ_TREATMENTS, SDB: SDB_TREATMENTS,
}
MEDICATIONS = {
    STROKE: STROKE_MEDICATIONS, HEMIPLEGIA: HEMIPLEGIA_MEDICATIONS, HEMIPARESIS: HEMIPARESIS_MEDICATIONS,
    CONTRACTURE: CONTRACTURE_MEDICATIONS, ALZ: ALZ_MEDICATIONS,
}
FUNCTIONAL_IMPACTS = {
    STROKE: STROKE_FUNCTIONAL_IMPACTS, HEMIPLEGIA: HEMIPLEGIA_FUNCTIONAL_IMPACTS,
    HEMIPARESIS: HEMIPARESIS_FUNCTIONAL_IMPACTS, ALZ: ALZ_FUNCTIONAL_IMPACTS, SDB: SDB_FUNCTIONAL_IMPACTS,
}
NUTRITIONAL_IMPACTS = {STROKE: STROKE_NUTRITIONAL_IMPACTS, ALZ: ALZ_NUTRITIONAL_IMPACTS, SDB: SDB_NUTRITIONAL_IMPACTS}
TREATMENT_LIMITATIONS = {
    STROKE: STROKE_TREATMENT_LIMITATIONS, HEMIPLEGIA: HEMIPLEGIA_TREATMENT_LIMITATIONS,
    CONTRACTURE: CONTRACTURE_TREATMENT_LIMITATIONS, ALZ: ALZ_TREATMENT_LIMITATIONS,
}
END_STAGE_FINDINGS = {STROKE: STROKE_END_STAGE_FINDINGS, ALZ: ALZ_END_STAGE_FINDINGS}

CONCEPT_DOMAINS = [
    (OntologyDiseaseSymptom, "SYMPTOM", "symptom_name"),
    (OntologyDiseaseFinding, "FINDING", "finding_name"),
    (OntologyDiseaseLab, "LAB", "lab_name"),
    (OntologyDiseaseDiagnosticTest, "DIAGNOSTIC_TEST", "test_name"),
    (OntologyDiseaseComplication, "COMPLICATION", "complication_name"),
    (OntologyDiseasePrognosticIndicator, "PROGNOSTIC_INDICATOR", "indicator_name"),
    (OntologyDiseaseTreatmentLimitation, "TREATMENT_LIMITATION", "limitation_name"),
    (OntologyDiseaseFunctionalImpact, "FUNCTIONAL_IMPACT", "impact_name"),
    (OntologyDiseaseNutritionalImpact, "NUTRITIONAL_IMPACT", "impact_name"),
    (OntologyDiseaseEndStageFinding, "END_STAGE_FINDING", "finding_name"),
    (OntologyDiseaseHospiceEligibilitySupport, "HOSPICE_ELIGIBILITY_SUPPORT", "indicator_name"),
    (OntologyDiseaseTreatment, "TREATMENT", "treatment_name"),
    (OntologyDiseaseMedication, "MEDICATION", "medication_name"),
    (OntologyDiseasePsychosocialConcern, "PSYCHOSOCIAL_CONCERN", "concern_name"),
    (OntologyDiseaseSpiritualConcern, "SPIRITUAL_CONCERN", "concern_name"),
]


def _resolve_diseases(db: Session) -> Dict[str, OntologyDisease]:
    """Resolve all six diseases strictly by existing name. Raises if any is
    missing -- this script never creates, renames, or re-families a
    disease, family, or body system."""
    resolved: Dict[str, OntologyDisease] = {}
    missing: List[str] = []
    for name in ALL_DISEASE_NAMES:
        disease = db.query(OntologyDisease).filter_by(disease_name=name).one_or_none()
        if disease is None:
            missing.append(name)
        else:
            resolved[name] = disease
    if missing:
        raise RuntimeError(
            "Neurologic Phase 2 coverage repair requires these diseases to already exist "
            f"and was unable to resolve: {missing}. Aborting without any writes."
        )
    return resolved


def _populate_simple_domain(db, model_cls, rows_by_disease, diseases, unique_attrs, field_names) -> int:
    inserted = 0
    for disease_name, rows in rows_by_disease.items():
        disease = diseases[disease_name]
        for values in rows:
            filter_kwargs = {"disease_id": disease.id}
            for attr, value in zip(unique_attrs, values[: len(unique_attrs)]):
                filter_kwargs[attr] = value
            existing = db.query(model_cls).filter_by(**filter_kwargs).one_or_none()
            if existing is not None:
                continue
            kwargs = {"id": uuid.uuid4(), "disease_id": disease.id}
            kwargs.update(dict(zip(field_names, values)))
            db.add(model_cls(**kwargs))
            inserted += 1
    db.flush()
    return inserted


def populate_symptoms(db, diseases) -> int:
    return _populate_simple_domain(
        db, OntologyDiseaseSymptom, SYMPTOMS, diseases,
        ["symptom_name"], ["symptom_name", "description", "hospice_relevance", "severity_scale"],
    )


def populate_findings(db, diseases) -> int:
    return _populate_simple_domain(
        db, OntologyDiseaseFinding, FINDINGS, diseases, ["finding_name"], ["finding_name", "finding_description"],
    )


def populate_labs(db, diseases) -> int:
    return _populate_simple_domain(
        db, OntologyDiseaseLab, LABS, diseases, ["lab_name"],
        ["lab_name", "normal_range", "expected_abnormal_range", "clinical_significance", "hospice_significance"],
    )


def populate_diagnostics(db, diseases) -> int:
    return _populate_simple_domain(
        db, OntologyDiseaseDiagnosticTest, DIAGNOSTICS, diseases,
        ["test_name"], ["test_name", "purpose", "expected_findings", "evidence_weight"],
    )


def populate_complications(db, diseases) -> int:
    return _populate_simple_domain(
        db, OntologyDiseaseComplication, COMPLICATIONS, diseases,
        ["complication_name"], ["complication_name", "description", "common_occurrence", "clinical_significance"],
    )


def populate_prognostic_indicators(db, diseases) -> int:
    return _populate_simple_domain(
        db, OntologyDiseasePrognosticIndicator, PROGNOSTIC_INDICATORS, diseases,
        ["indicator_name"], ["indicator_name", "description", "supporting_evidence"],
    )


def populate_treatments(db, diseases) -> int:
    return _populate_simple_domain(
        db, OntologyDiseaseTreatment, TREATMENTS, diseases,
        ["treatment_name", "treatment_category"], ["treatment_name", "treatment_category", "description"],
    )


def populate_medications(db, diseases) -> int:
    return _populate_simple_domain(
        db, OntologyDiseaseMedication, MEDICATIONS, diseases, ["medication_name"],
        ["medication_name", "drug_class", "purpose", "expected_benefits", "common_side_effects", "hospice_relevance"],
    )


def populate_functional_impacts(db, diseases) -> int:
    return _populate_simple_domain(
        db, OntologyDiseaseFunctionalImpact, FUNCTIONAL_IMPACTS, diseases,
        ["impact_name"], ["impact_name", "description", "severity"],
    )


def populate_nutritional_impacts(db, diseases) -> int:
    return _populate_simple_domain(
        db, OntologyDiseaseNutritionalImpact, NUTRITIONAL_IMPACTS, diseases,
        ["impact_name"], ["impact_name", "description", "clinical_significance"],
    )


def populate_treatment_limitations(db, diseases) -> int:
    inserted = 0
    for disease_name, rows in TREATMENT_LIMITATIONS.items():
        disease = diseases[disease_name]
        for name, category, desc, evidence_req, hospice_rel in rows:
            existing = (
                db.query(OntologyDiseaseTreatmentLimitation)
                .filter_by(disease_id=disease.id, limitation_name=name, limitation_category=category)
                .one_or_none()
            )
            if existing is not None:
                continue
            db.add(
                OntologyDiseaseTreatmentLimitation(
                    id=uuid.uuid4(), disease_id=disease.id, limitation_name=name, limitation_category=category,
                    description=desc, evidence_requirement=evidence_req, hospice_relevance=hospice_rel,
                )
            )
            inserted += 1
    db.flush()
    return inserted


def populate_end_stage_findings(db, diseases) -> int:
    inserted = 0
    for disease_name, rows in END_STAGE_FINDINGS.items():
        disease = diseases[disease_name]
        for name, desc, evidence_req, clinical_sig, hospice_rel in rows:
            existing = (
                db.query(OntologyDiseaseEndStageFinding)
                .filter_by(disease_id=disease.id, finding_name=name)
                .one_or_none()
            )
            if existing is not None:
                continue
            db.add(
                OntologyDiseaseEndStageFinding(
                    id=uuid.uuid4(), disease_id=disease.id, finding_name=name, description=desc,
                    evidence_requirement=evidence_req, clinical_significance=clinical_sig,
                    hospice_relevance=hospice_rel,
                )
            )
            inserted += 1
    db.flush()
    return inserted


def populate_evidence_rules(db, diseases) -> int:
    """J: one active evidence rule per active concept row for every concept
    domain in CONCEPT_DOMAINS, across all six diseases -- including rows
    that already existed before this script ran (e.g. from PR #34) but did
    not yet have an evidence rule attached. Never re-creates a rule for a
    concept that already has one."""
    inserted = 0
    disease_ids = {d.id for d in diseases.values()}
    for model_cls, concept_type, name_attr in CONCEPT_DOMAINS:
        rows = db.query(model_cls).filter(model_cls.disease_id.in_(disease_ids))
        if hasattr(model_cls, "active"):
            rows = rows.filter(model_cls.active.is_(True))
        rows = rows.all()
        for row in rows:
            existing = (
                db.query(OntologyEvidenceRule)
                .filter_by(concept_type=concept_type, concept_id=row.id)
                .one_or_none()
            )
            if existing is not None:
                continue
            disease_name = next((name for name, d in diseases.items() if d.id == row.disease_id), None)
            source_label = EVIDENCE_SOURCE_BY_DISEASE_NAME.get(disease_name)
            concept_name_display = getattr(row, name_attr)
            db.add(
                OntologyEvidenceRule(
                    id=uuid.uuid4(),
                    concept_type=concept_type,
                    concept_id=row.id,
                    evidence_source=source_label,
                    evidence_type=concept_type,
                    confidence="moderate",
                    review_trigger="RN_REVIEW",
                    patient_fact_requires_evidence=True,
                    notes=(
                        f"Atomic-concept coverage-repair evidence rule for {concept_type} concept "
                        f"'{concept_name_display}'; requires patient-record evidence before treated as "
                        "documented. General ontology knowledge never becomes a patient fact without "
                        "patient-record evidence."
                    ),
                )
            )
            inserted += 1
    db.flush()
    return inserted


def run(db: Session) -> Dict[str, int]:
    """Run the Neurologic Phase 2 atomic concept coverage repair against the
    given session. Does not commit -- the caller controls the transaction
    boundary. Safe to call repeatedly; returns the count of NEW rows
    inserted in this call for each domain (0 on a fully-idempotent
    re-run). Creates no disease, family, or body-system row; adds no
    schema, migration, model, or enum change; deletes/deactivates nothing."""
    diseases = _resolve_diseases(db)

    counts = {
        "symptoms_inserted": populate_symptoms(db, diseases),
        "findings_inserted": populate_findings(db, diseases),
        "labs_inserted": populate_labs(db, diseases),
        "diagnostics_inserted": populate_diagnostics(db, diseases),
        "complications_inserted": populate_complications(db, diseases),
        "prognostic_indicators_inserted": populate_prognostic_indicators(db, diseases),
        "treatments_inserted": populate_treatments(db, diseases),
        "medications_inserted": populate_medications(db, diseases),
        "functional_impacts_inserted": populate_functional_impacts(db, diseases),
        "nutritional_impacts_inserted": populate_nutritional_impacts(db, diseases),
        "treatment_limitations_inserted": populate_treatment_limitations(db, diseases),
        "end_stage_findings_inserted": populate_end_stage_findings(db, diseases),
        "evidence_rules_inserted": populate_evidence_rules(db, diseases),
    }
    return counts


def main() -> None:
    db = SessionLocal()
    try:
        counts = run(db)
        db.commit()
        for label, count in counts.items():
            print(f"{label}: {count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
