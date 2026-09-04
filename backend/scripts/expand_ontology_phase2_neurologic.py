# scripts/expand_ontology_phase2_neurologic.py
"""
Phase 2 Production-Knowledge expansion for the Neurologic System (A-K).

This script does NOT redesign the Neurologic hierarchy. It expands clinical
knowledge for six canonical diseases:

    Existing (resolved by name, never created/modified in family/system):
        - Stroke                                  (Cerebrovascular Disease)
        - Hemiplegia                               (Cerebrovascular Disease)
        - Hemiparesis                              (Cerebrovascular Disease)
        - Contracture                              (Cerebrovascular Disease)
        - Dementia Due To Alzheimer's Disease      (Dementia Disorders)

    New (the ONE approved new canonical disease for this phase):
        - Senile Degeneration of Brain
          System: Neurologic System (existing, resolved not recreated)
          Family: Degenerative Brain Disorders (new)

Senile Degeneration of Brain is a DISTINCT canonical disease. It is never
treated as an Alzheimer's alias, and Alzheimer-specific hospice/FAST
criteria are never copied onto it -- its Domain I (hospice eligibility
support) content is grounded only in the general decline/terminal-status
literature (backend/app/config/lcd/general_decline_terminal_status.json),
never in the Alzheimer's-specific LCD
(backend/app/config/lcd/dementia_alzheimers_senile_degeneration.json).

Stroke clinical subtype/variant knowledge (Ischemic, Thrombotic, Embolic,
Hemorrhagic Stroke, Intracerebral Hemorrhage, Subarachnoid Hemorrhage,
Brainstem Stroke, Cerebellar Stroke, Anterior/Posterior Circulation Stroke,
Recurrent Stroke, Residual Deficit Following Stroke) and common terminology
synonyms (CVA, Cerebrovascular Accident, Cerebral Infarct, Brain Attack,
Ischemic CVA, Hemorrhagic CVA) are stored as idempotent additions to the
existing Stroke disease's disease_description -- this is content, not a new
disease row, table, or hierarchy branch. The same idempotent pattern is used
to record Alzheimer's disease-severity subtype terminology (Mild, Moderate,
Severe, Early-Onset, Late-Onset, With Behavioral Disturbance, Without
Behavioral Disturbance) on the existing Alzheimer's disease_description.

A-K storage mapping used throughout this script (authoritative, approved):

    A Disease Identity              -> ontology_disease (disease_description)
    B Symptomology                  -> ontology_disease_symptom
    C Complications                 -> ontology_disease_complication
    D Prognostic Factors            -> ontology_disease_prognostic_indicator
    E Treatment Limitations         -> ontology_disease_treatment_limitation
    F Functional Decline            -> ontology_disease_functional_impact
    G Nutritional Decline           -> ontology_disease_nutritional_impact
    H End-Stage Findings            -> ontology_disease_end_stage_finding
    I Hospice Eligibility Support   -> ontology_disease_hospice_eligibility_support
    J Evidence Architecture         -> ontology_evidence_rule
    K Validation                    -> ontology_disease_validation_result

Supporting (non-letter) knowledge tables used within A-K: findings, labs,
diagnostic tests, treatments, medications, psychosocial concerns, spiritual
concerns, interdisciplinary triggers, and cross-concept relationships.

Source ownership:
    - A-H, general clinical knowledge: standard cerebrovascular-disease,
      hemiplegia/hemiparesis/contracture, and Alzheimer's-dementia clinical
      literature; standard general-decline/terminal-status literature for
      Senile Degeneration of Brain.
    - I (Hospice Eligibility Support):
        Stroke                                -> backend/app/config/lcd/stroke_coma.json
        Dementia Due To Alzheimer's Disease    -> backend/app/config/lcd/dementia_alzheimers_senile_degeneration.json
        Senile Degeneration of Brain           -> backend/app/config/lcd/general_decline_terminal_status.json
        Hemiplegia / Hemiparesis / Contracture -> general decline/terminal-status literature
          (no disease-specific LCD exists for these three; no LCD is
          fabricated for them).

No RT (Respiratory Therapy) discipline value is introduced or used anywhere
in this script -- the interdisciplinary discipline enum is never modified.
No PT/OT substitution is created in place of any other discipline. No
IS_NOT_AUTOMATICALLY_EQUIVALENT_TO relationship type is created (it does not
exist in the ontology); Senile Degeneration of Brain's non-equivalence to
Alzheimer's disease is enforced entirely through disease_description
language and dedicated tests, never through a relationship_type that would
have to be invented.

Every system/family/disease/concept row is resolved by stable name (never a
hardcoded UUID) and inserted only if a matching row does not already exist
by the table's existing unique constraint. Re-running this script is always
safe:

    - missing records are inserted
    - matching records are left unchanged
    - no records are ever deleted
    - no other body system, disease, or patient/staff table is touched
    - the five pre-existing diseases are never re-created and their
      family/system placement is never modified

Run with: .\\.venv\\Scripts\\python.exe scripts\\expand_ontology_phase2_neurologic.py
"""

from __future__ import annotations

import uuid
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.ontology.disease_family_ownership import (
    BASE_DISEASE_FAMILY,
    authoritative_family_name_for,
    get_or_create_authoritative_family,
    get_or_create_body_system,
    resolve_or_create_authoritative_disease,
)
from app.ontology.treatment_identity import (
    concept_identity_key,
    existing_rows_by_canonical_name,
    reconcile_category,
)

# See populate_ontology_ak_neuro_cardio.py for why this explicit import is
# needed before any query touches the full ORM mapper registry.
import app.models.poc  # noqa: F401
from app.models.ontology_disease_blueprint import (
    OntologyBodySystem,
    OntologyDisease,
    OntologyDiseaseComplication,
    OntologyDiseaseDiagnosticTest,
    OntologyDiseaseEndStageFinding,
    OntologyDiseaseFamily,
    OntologyDiseaseFinding,
    OntologyDiseaseFunctionalImpact,
    OntologyDiseaseHospiceEligibilitySupport,
    OntologyDiseaseInterdisciplinaryTrigger,
    OntologyDiseaseLab,
    OntologyDiseaseMedication,
    OntologyDiseaseNutritionalImpact,
    OntologyDiseasePrognosticIndicator,
    OntologyDiseasePsychosocialConcern,
    OntologyDiseaseSpiritualConcern,
    OntologyDiseaseSymptom,
    OntologyDiseaseTreatment,
    OntologyDiseaseTreatmentLimitation,
    OntologyDiseaseValidationResult,
    OntologyEvidenceRule,
    OntologyRelationship,
)

SYSTEM_NAME = "Neurologic System"
IMPORTER_NAME = "expand_ontology_phase2_neurologic"

STROKE = "Stroke"
HEMIPLEGIA = "Hemiplegia"
HEMIPARESIS = "Hemiparesis"
CONTRACTURE = "Contracture"
ALZ = "Dementia Due To Alzheimer's Disease"
SDB = "Senile Degeneration of Brain"

# The five diseases already resolved/existing -- never (re)created here.
EXISTING_DISEASE_NAMES = [STROKE, HEMIPLEGIA, HEMIPARESIS, CONTRACTURE, ALZ]
# The one new canonical disease approved for this phase.
NEW_DISEASE_NAME = SDB
NEW_FAMILY_NAME = authoritative_family_name_for(SDB)

ALL_DISEASE_NAMES = EXISTING_DISEASE_NAMES + [NEW_DISEASE_NAME]

CEREBROVASCULAR_SOURCE = (
    "General cerebrovascular-disease, hemiplegia/hemiparesis/contracture "
    "clinical literature (standard stroke, post-stroke deficit, and "
    "contracture-management knowledge)."
)
ALZ_SOURCE = "General Alzheimer's-dementia clinical literature (standard staging/decline knowledge)."
SDB_SOURCE = "General decline/terminal-status clinical literature (non-Alzheimer-specific)."

EVIDENCE_SOURCE_BY_DISEASE_NAME: Dict[str, str] = {
    STROKE: CEREBROVASCULAR_SOURCE,
    HEMIPLEGIA: CEREBROVASCULAR_SOURCE,
    HEMIPARESIS: CEREBROVASCULAR_SOURCE,
    CONTRACTURE: CEREBROVASCULAR_SOURCE,
    ALZ: ALZ_SOURCE,
    SDB: SDB_SOURCE,
}

LCD_SOURCE_BY_DISEASE_NAME: Dict[str, str] = {
    STROKE: "LCD Hospice Eligibility Determination \u2013 Stroke and Coma (stroke_coma.json)",
    ALZ: "LCD Hospice Eligibility Determination \u2013 Dementia due to Alzheimer's Disease "
    "(dementia_alzheimers_senile_degeneration.json)",
    SDB: "General Decline / Terminal Status guidance (general_decline_terminal_status.json) "
    "-- general-decline concepts only; NOT the Alzheimer's-specific LCD.",
    HEMIPLEGIA: "General Decline / Terminal Status guidance (general_decline_terminal_status.json) "
    "-- no disease-specific LCD exists for Hemiplegia; none fabricated.",
    HEMIPARESIS: "General Decline / Terminal Status guidance (general_decline_terminal_status.json) "
    "-- no disease-specific LCD exists for Hemiparesis; none fabricated.",
    CONTRACTURE: "General Decline / Terminal Status guidance (general_decline_terminal_status.json) "
    "-- no disease-specific LCD exists for Contracture; none fabricated.",
}

IMAGING_TEST_NAMES = {
    "ct head (non-contrast)", "ct head", "mri brain", "mri brain with diffusion-weighted imaging",
    "ct angiography head/neck",
}

# ---------------------------------------------------------------------------
# Idempotent disease_description content additions (subtype/terminology
# knowledge for existing diseases -- content only, no new disease rows).
# ---------------------------------------------------------------------------
STROKE_SUBTYPE_MARKER = "PHASE2_NEURO_STROKE_SUBTYPE_KNOWLEDGE_V1"
STROKE_SUBTYPE_APPENDIX = (
    "\n\n[" + STROKE_SUBTYPE_MARKER + "] Clinical subtype/variant knowledge (recorded as "
    "differentiating content on this existing Stroke disease -- these are not separate "
    "disease rows): Ischemic Stroke (thrombotic or embolic arterial occlusion causing "
    "cerebral infarction); Thrombotic Stroke (in-situ arterial thrombosis, often "
    "atherosclerosis-related); Embolic Stroke (distal occlusion by an embolus, commonly "
    "cardioembolic, e.g. atrial fibrillation); Hemorrhagic Stroke (bleeding into or around "
    "brain tissue); Intracerebral Hemorrhage (bleeding within brain parenchyma); "
    "Subarachnoid Hemorrhage (bleeding into the subarachnoid space, often aneurysmal); "
    "Brainstem Stroke (infarct/hemorrhage involving the brainstem, high risk for "
    "consciousness/respiratory/autonomic compromise); Cerebellar Stroke (infarct/hemorrhage "
    "involving the cerebellum, risk of mass effect/hydrocephalus); Anterior Circulation "
    "Stroke (carotid/MCA/ACA territory); Posterior Circulation Stroke "
    "(vertebrobasilar/PCA territory); Recurrent Stroke (a new stroke event in a patient "
    "with prior stroke history, associated with cumulative deficit and worse prognosis); "
    "Residual Deficit Following Stroke (persistent neurologic impairment after the acute "
    "event, e.g. hemiplegia, hemiparesis, dysphagia, aphasia, contracture). Terminology "
    "synonyms referring to this same Stroke disease: CVA, Cerebrovascular Accident, "
    "Cerebral Infarct, Brain Attack, Ischemic CVA, Hemorrhagic CVA."
)

ALZ_SUBTYPE_MARKER = "PHASE2_NEURO_ALZ_SUBTYPE_KNOWLEDGE_V1"
ALZ_SUBTYPE_APPENDIX = (
    "\n\n[" + ALZ_SUBTYPE_MARKER + "] Clinical severity/subtype terminology (recorded as "
    "differentiating content on this existing Alzheimer's disease -- not separate disease "
    "rows): Mild Alzheimer's Disease; Moderate Alzheimer's Disease; Severe Alzheimer's "
    "Disease; Early-Onset Alzheimer's Disease (onset before age 65); Late-Onset Alzheimer's "
    "Disease (onset at or after age 65); Alzheimer's Disease With Behavioral Disturbance "
    "(e.g. agitation, psychosis, wandering); Alzheimer's Disease Without Behavioral "
    "Disturbance. These terms differentiate presentation and severity of the same "
    "underlying Alzheimer's disease process; they do not represent Senile Degeneration of "
    "Brain, which is a distinct canonical disease in this ontology and is never treated as "
    "an Alzheimer's alias."
)

# Disease identity content for the new disease only.
# (disease_category, primary_organ, disease_type, disease_description, clinical_purpose, hospice_relevance)
SDB_IDENTITY: Tuple[str, str, str, str, str, str] = (
    "Neurologic",
    "Brain",
    "Degenerative",
    "Senile Degeneration of Brain: a distinct, canonical, non-Alzheimer's degenerative "
    "brain disease reflecting generalized, age-associated structural and functional brain "
    "decline (e.g. global cortical atrophy, generalized neuronal loss) that is not "
    "attributed to a specific diagnosed dementia etiology such as Alzheimer's disease, "
    "vascular dementia, or another named neurodegenerative disorder. Terminology variants "
    "referring to this same disease: Senile Degeneration of Brain, Senile Degeneration of "
    "the Brain, Senile Brain Degeneration. This disease is NOT an alias for, and is NOT "
    "automatically clinically equivalent to, Dementia Due To Alzheimer's Disease -- it is "
    "modeled as its own disease under its own family (Degenerative Brain Disorders) with "
    "its own general-decline evidence base, and Alzheimer's-specific staging tools (e.g. "
    "FAST) or the Alzheimer's-specific hospice LCD are never applied to it without "
    "independent patient-specific clinical documentation supporting that distinct "
    "diagnosis.",
    "Represents generalized age-associated brain degeneration not attributed to a specific "
    "named dementia etiology, for AI clinical-reasoning support distinct from Alzheimer's "
    "disease reasoning.",
    "Progressive global brain decline can independently support hospice-appropriateness "
    "review using general decline/terminal-status principles; disease-specific "
    "Alzheimer's hospice criteria are not substituted for this disease.",
)

# ---------------------------------------------------------------------------
# B: SYMPTOMS
# (symptom_name, description, hospice_relevance, severity_scale)
# ---------------------------------------------------------------------------
SYMPTOMS: Dict[str, List[Tuple[str, str, str, str]]] = {
    STROKE: [
        ("Sudden Unilateral Weakness", "Abrupt weakness of face, arm, and/or leg on one side of the body.",
         "Hallmark presenting symptom; severity correlates with infarct/hemorrhage size.", "Moderate-Severe"),
        ("Sudden Speech Disturbance", "Abrupt difficulty producing or understanding speech (aphasia/dysarthria).",
         "Associated with dominant-hemisphere involvement; affects communication capacity.", "Moderate-Severe"),
        ("Sudden Vision Loss/Field Cut", "Abrupt monocular or homonymous visual loss.",
         "Contributes to functional impairment and fall risk.", "Mild-Moderate"),
        ("Sudden Severe Headache", "Abrupt, often 'worst-ever' headache, classically with hemorrhagic stroke.",
         "Suggests hemorrhagic etiology; associated with worse prognosis.", "Severe"),
        ("Ataxia/Imbalance", "Sudden loss of coordination or balance.",
         "Associated with cerebellar/posterior-circulation involvement.", "Moderate"),
        ("Dysphagia", "Difficulty swallowing following the acute event.",
         "Aspiration risk; central to nutritional and functional decline.", "Moderate-Severe"),
        ("Altered Level of Consciousness", "Reduced alertness ranging from lethargy to coma.",
         "Reflects larger lesion burden, brainstem involvement, or increased intracranial pressure.", "Severe"),
    ],
    HEMIPLEGIA: [
        ("Complete Unilateral Paralysis", "Total loss of voluntary movement on one side of the body.",
         "Defines the disease; drives total dependence for mobility and self-care.", "Severe"),
        ("Unilateral Sensory Loss", "Diminished or absent sensation on the affected side.",
         "Increases risk of unnoticed skin breakdown and injury.", "Moderate-Severe"),
        ("Spasticity", "Increased muscle tone/velocity-dependent resistance on the affected side.",
         "Predisposes to pain and contracture formation.", "Moderate-Severe"),
        ("Facial Droop", "Weakness of facial musculature on the affected side.",
         "Contributes to dysphagia and drooling.", "Mild-Moderate"),
    ],
    HEMIPARESIS: [
        ("Partial Unilateral Weakness", "Incomplete weakness (not full paralysis) on one side of the body.",
         "Defines the disease; degree determines residual functional capacity.", "Mild-Moderate"),
        ("Gait Disturbance", "Asymmetric, weakness-related gait abnormality.",
         "Central driver of fall risk and mobility decline.", "Moderate"),
        ("Fine Motor Impairment", "Reduced dexterity of the affected hand/arm.",
         "Limits independence in self-care tasks.", "Mild-Moderate"),
        ("Fatigue With Exertion", "Increased fatigability of the weakened limb(s) with use.",
         "Limits sustained functional activity.", "Mild"),
    ],
    CONTRACTURE: [
        ("Fixed Joint Limitation", "Reduced passive range of motion at an affected joint.",
         "Defines the disease; progressive if unaddressed.", "Moderate-Severe"),
        ("Pain With Passive Movement", "Discomfort elicited when the affected joint is moved by a caregiver.",
         "Complicates repositioning and hygiene care.", "Moderate"),
        ("Muscle Shortening", "Palpable/visible shortening of muscle-tendon units around the joint.",
         "Reflects chronicity and predicts difficulty of reversal.", "Moderate"),
        ("Skin Fold Maceration", "Skin breakdown within a persistently flexed joint fold.",
         "Increases infection risk in advanced contracture.", "Mild-Moderate"),
    ],
    ALZ: [
        ("Progressive Memory Loss", "Worsening short-term and eventually long-term memory impairment.",
         "Core diagnostic feature; tracks disease stage.", "Mild-Severe"),
        ("Disorientation", "Impaired orientation to time, place, or person.",
         "Increases safety risk and caregiver burden.", "Moderate-Severe"),
        ("Language Decline (Aphasia)", "Progressive difficulty finding words or following conversation.",
         "Impairs ability to report symptoms/needs, complicating care.", "Moderate-Severe"),
        ("Apraxia", "Loss of ability to perform previously learned motor tasks.",
         "Drives loss of independence in ADLs.", "Moderate-Severe"),
        ("Agnosia", "Loss of ability to recognize familiar people, objects, or places.",
         "Increases distress and caregiver burden; safety risk.", "Moderate-Severe"),
        ("Behavioral/Psychological Symptoms", "Agitation, aggression, wandering, psychosis, or apathy.",
         "Major driver of caregiver burden and care-setting decisions.", "Variable"),
        ("Sleep-Wake Disturbance", "Disrupted sleep architecture, sundowning.",
         "Contributes to caregiver exhaustion and fall risk.", "Mild-Moderate"),
    ],
    SDB: [
        ("Global Cognitive Slowing", "Generalized, non-focal decline in cognitive processing speed.",
         "Reflects diffuse brain degeneration rather than a focal or named dementia syndrome.",
         "Mild-Moderate"),
        ("Progressive Forgetfulness", "General decline in memory not clearly localized to a specific dementia pattern.",
         "Supports general cognitive-decline tracking distinct from Alzheimer's-specific staging.",
         "Mild-Severe"),
        ("General Functional Slowing", "Diffuse slowing of purposeful activity and initiation.",
         "Reflects generalized rather than focal neurologic decline.", "Moderate"),
        ("Reduced Alertness/Arousal", "Progressively diminished spontaneous alertness.",
         "Advanced-stage finding supporting general decline assessment.", "Moderate-Severe"),
    ],
}

# ---------------------------------------------------------------------------
# Supporting: FINDINGS
# (finding_name, finding_description)
# ---------------------------------------------------------------------------
FINDINGS: Dict[str, List[Tuple[str, str]]] = {
    STROKE: [
        ("Focal Neurologic Deficit on Exam", "Objective unilateral weakness/sensory loss/visual field cut on exam."),
        ("NIH Stroke Scale Score", "Standardized quantification of stroke-related neurologic deficit severity."),
        ("Hemiparesis/Hemiplegia on Exam", "Documented unilateral motor deficit consistent with vascular territory."),
    ],
    HEMIPLEGIA: [
        ("Absent Voluntary Movement, Affected Side", "No voluntary motor activity elicited on the affected side."),
        ("Increased Deep Tendon Reflexes, Affected Side", "Hyperreflexia consistent with upper motor neuron lesion."),
    ],
    HEMIPARESIS: [
        ("Reduced Muscle Strength, Affected Side", "Graded strength deficit (e.g. 3/5-4/5) on manual muscle testing."),
        ("Asymmetric Gait Pattern", "Observed asymmetric weight-bearing/limb advancement during ambulation."),
    ],
    CONTRACTURE: [
        ("Reduced Passive Range of Motion", "Goniometric measurement below normal range at the affected joint."),
        ("Palpable Soft-Tissue Shortening", "Firm resistance to stretch on passive joint examination."),
    ],
    ALZ: [
        ("Abnormal Cognitive Screening Score", "MMSE/MoCA or similar screening score below normal threshold."),
        ("FAST Stage 1", "No cognitive decline; normal function (Functional Assessment Staging)."),
        ("FAST Stage 2", "Subjective forgetfulness; no objective deficit."),
        ("FAST Stage 3", "Mild objective deficits noticeable to close associates."),
        ("FAST Stage 4", "Deficits in complex tasks (e.g. finances, planning a meal)."),
        ("FAST Stage 5", "Requires assistance choosing proper clothing."),
        ("FAST Stage 6", "Requires assistance with ADLs (dressing, bathing, toileting); incontinence may emerge."),
        ("FAST Stage 7", "Loss of speech, ambulation, and ability to sit up independently (advanced/end-stage)."),
    ],
    SDB: [
        ("Diffuse Cognitive Impairment on Screening", "Generalized abnormal cognitive screening not localizing to a "
         "specific named dementia pattern."),
        ("Generalized Brain Atrophy on Imaging (if available)", "Non-focal global atrophy pattern, when imaging is "
         "available and documented; imaging is not required to support this general-decline disease."),
    ],
}

# ---------------------------------------------------------------------------
# Supporting: LABS
# (lab_name, normal_range, expected_abnormal_range, clinical_significance, hospice_significance)
# ---------------------------------------------------------------------------
LABS: Dict[str, List[Tuple[str, str, str, str, str]]] = {
    STROKE: [
        ("Coagulation Panel (PT/INR, aPTT)", "PT 11-13.5s / INR 0.8-1.1 / aPTT 25-35s",
         "Elevated INR/aPTT or supratherapeutic anticoagulation",
         "Informs hemorrhagic-conversion risk and treatment eligibility.",
         "Guides anticoagulation-related treatment-limitation decisions."),
    ],
    ALZ: [
        ("Serum Albumin", "3.5-5.0 g/dL", "Below 3.0 g/dL in advanced disease",
         "Reflects nutritional status as oral intake declines.",
         "Supports nutritional-decline/end-stage assessment."),
    ],
    SDB: [
        ("Serum Albumin", "3.5-5.0 g/dL", "Below 3.0 g/dL in advanced disease",
         "Reflects nutritional status as generalized decline progresses.",
         "Supports general-decline/end-stage assessment (non-Alzheimer-specific)."),
    ],
}

# ---------------------------------------------------------------------------
# Supporting: DIAGNOSTIC TESTS
# (test_name, purpose, expected_findings, evidence_weight)
# ---------------------------------------------------------------------------
DIAGNOSTICS: Dict[str, List[Tuple[str, str, str, str]]] = {
    STROKE: [
        ("CT Head (Non-Contrast)", "Distinguish ischemic vs. hemorrhagic stroke; assess lesion size/location.",
         "Hypodensity (ischemic) or hyperdensity (hemorrhagic) in the affected territory.", "High"),
        ("MRI Brain With Diffusion-Weighted Imaging", "Confirm acute infarct, define territory and size.",
         "Restricted diffusion in the affected vascular territory.", "High"),
        ("CT Angiography Head/Neck", "Identify large-vessel occlusion or aneurysmal source of hemorrhage.",
         "Vessel occlusion, stenosis, or aneurysm.", "Moderate"),
    ],
    ALZ: [
        ("Cognitive Screening (MMSE/MoCA)", "Quantify and stage cognitive impairment severity.",
         "Score below age/education-adjusted normal range.", "Moderate"),
        ("MRI Brain", "Characterize atrophy pattern to support the Alzheimer's diagnosis.",
         "Hippocampal/medial temporal atrophy pattern.", "Moderate"),
    ],
    SDB: [
        ("Cognitive Screening (General)", "Quantify generalized cognitive decline severity, without staging as "
         "Alzheimer's-specific.", "Diffuse, non-focal impairment pattern.", "Moderate"),
        ("MRI Brain", "Characterize generalized (non-focal) atrophy pattern when clinically obtained.",
         "Generalized/global atrophy without a specific localized dementia signature.", "Low"),
    ],
}

# ---------------------------------------------------------------------------
# C: COMPLICATIONS
# (complication_name, description, common_occurrence, clinical_significance)
# ---------------------------------------------------------------------------
COMPLICATIONS: Dict[str, List[Tuple[str, str, str, str]]] = {
    STROKE: [
        ("Aspiration Pneumonia", "Pulmonary infection from aspirated oropharyngeal contents due to dysphagia.",
         "Common", "Leading cause of post-stroke mortality; recurrent episodes suggest advanced decline."),
        ("Deep Vein Thrombosis/Pulmonary Embolism", "Venous thromboembolism from post-stroke immobility.",
         "Common", "Life-threatening; risk rises with prolonged immobility."),
        ("Post-Stroke Seizures", "New-onset seizures related to the cortical injury.",
         "Occasional", "May complicate management and reflect cortical involvement."),
        ("Recurrent Stroke", "A new cerebrovascular event in a patient with prior stroke.",
         "Occasional", "Associated with cumulative deficit burden and worse prognosis."),
        ("Post-Stroke Depression", "Mood disorder following stroke, related to lesion location and disability.",
         "Common", "Impairs rehabilitation participation and quality of life."),
    ],
    HEMIPLEGIA: [
        ("Pressure Injury", "Skin breakdown over bony prominences from immobility/sensory loss.",
         "Common", "Reflects impaired positioning capacity and skin-integrity risk."),
        ("Contracture Formation", "Joint range-of-motion loss from prolonged flaccidity/spasticity.",
         "Common", "Progressive complication if not addressed with positioning/therapy."),
        ("Falls", "Loss of balance/support from unilateral paralysis.",
         "Common", "Major injury risk given absent protective response on affected side."),
    ],
    HEMIPARESIS: [
        ("Falls", "Loss of balance from asymmetric weakness.",
         "Common", "Leading cause of fracture and further functional decline."),
        ("Overuse Injury of Unaffected Side", "Strain/injury from compensatory reliance on the stronger side.",
         "Occasional", "Can accelerate overall functional decline."),
    ],
    CONTRACTURE: [
        ("Skin Breakdown Within Joint Folds", "Maceration/pressure injury in a fixed-flexed position.",
         "Common", "Infection risk; complicates hygiene."),
        ("Pain With Care Activities", "Discomfort during required repositioning/hygiene.",
         "Common", "Impacts caregiving tolerance and comfort-focused planning."),
    ],
    ALZ: [
        ("Aspiration Pneumonia", "Pulmonary infection from dysphagia in advanced disease.",
         "Common (advanced stage)", "Leading terminal complication in advanced Alzheimer's."),
        ("Recurrent Infections (UTI, Skin, Pulmonary)", "Recurrent infections related to immobility, incontinence, "
         "and impaired self-care.", "Common (advanced stage)", "Reflects advanced functional decline."),
        ("Malnutrition/Dehydration", "Inadequate oral intake from progressive feeding difficulty.",
         "Common (advanced stage)", "Core end-stage indicator."),
        ("Falls With Injury", "Falls related to gait disturbance and impaired judgment.",
         "Common", "Major source of morbidity across disease course."),
    ],
    SDB: [
        ("Recurrent Infections", "Infections related to progressive immobility and self-care decline.",
         "Common (advanced stage)", "Reflects advanced generalized decline."),
        ("Malnutrition/Dehydration", "Inadequate oral intake from progressive generalized decline.",
         "Common (advanced stage)", "Core end-stage indicator, general-decline basis."),
        ("Falls With Injury", "Falls related to generalized functional slowing and impaired judgment.",
         "Common", "Major source of morbidity."),
    ],
}

# ---------------------------------------------------------------------------
# D: PROGNOSTIC INDICATORS
# (indicator_name, description, supporting_evidence)
# ---------------------------------------------------------------------------
PROGNOSTIC_INDICATORS: Dict[str, List[Tuple[str, str, str]]] = {
    STROKE: [
        ("Persistent Coma/Severely Depressed Consciousness", "Failure to regain consciousness beyond the acute period.",
         "Documented level-of-consciousness assessments over time."),
        ("Large Lesion Volume/Brainstem Involvement", "Large infarct/hemorrhage volume or brainstem location.",
         "Imaging report (CT/MRI)."),
        ("Absence of Functional Improvement", "No meaningful functional gain over a defined post-stroke period.",
         "Serial functional/PPS assessments."),
    ],
    HEMIPLEGIA: [
        ("Persistent Total Dependence", "Sustained complete dependence for all mobility/ADLs.",
         "Functional assessment over time."),
    ],
    HEMIPARESIS: [
        ("Plateau in Rehabilitation Gains", "No further functional improvement despite therapy.",
         "Therapy progress notes."),
    ],
    CONTRACTURE: [
        ("Progressive Multi-Joint Involvement", "Contracture spreading to additional joints despite intervention.",
         "Serial range-of-motion assessments."),
    ],
    ALZ: [
        ("FAST Stage 7 or Beyond", "Loss of speech, ambulation, and independent sitting.",
         "Functional Assessment Staging documentation."),
        ("Recurrent Infections/Aspiration", "Recurrent infection episodes despite treatment.",
         "Infection/hospitalization history."),
        ("Comorbidity Burden", "Presence of significant comorbid conditions compounding decline.",
         "Problem list/comorbidity documentation."),
    ],
    SDB: [
        ("Progressive Generalized Functional Decline", "Ongoing decline in overall function without a plateau, "
         "using general (non-Alzheimer-specific) decline measures.", "Serial functional/PPS assessments."),
        ("Recurrent Infections", "Recurrent infection episodes reflecting advanced generalized decline.",
         "Infection/hospitalization history."),
    ],
}

# ---------------------------------------------------------------------------
# E: TREATMENT LIMITATIONS
# (limitation_name, limitation_category, description, evidence_requirement, hospice_relevance)
# ---------------------------------------------------------------------------
TREATMENT_LIMITATIONS: Dict[str, List[Tuple[str, str, str, str, str]]] = {
    STROKE: [
        ("Not A Thrombolysis/Thrombectomy Candidate", "NOT_A_CANDIDATE",
         "Patient falls outside the eligible window or has contraindications for acute reperfusion therapy.",
         "Physician/stroke-team documentation.", "Supports terminal-prognosis review under LCD Stroke and Coma."),
        ("Rehabilitation Not Tolerated", "TREATMENT_INTOLERANT",
         "Patient unable to participate in or tolerate rehabilitation therapy.",
         "Therapy/nursing documentation.", "Supports functional-decline picture."),
        ("Aggressive Care Declined", "TREATMENT_DECLINED",
         "Patient/family elects comfort-focused care over aggressive intervention.",
         "Documented goals-of-care discussion.", "Core hospice transition marker."),
    ],
    ALZ: [
        ("Disease-Modifying Therapy Not Pursued", "TREATMENT_DECLINED",
         "Patient/family elects not to pursue disease-modifying Alzheimer's therapy.",
         "Documented goals-of-care discussion.", "Supports terminal-prognosis review."),
        ("Not A Candidate For Aggressive Intervention", "NOT_A_CANDIDATE",
         "Advanced dementia stage precludes benefit from aggressive medical intervention.",
         "Physician assessment documented in the record.",
         "Supports terminal-prognosis review under LCD Dementia due to Alzheimer's Disease."),
        ("Artificial Nutrition Declined", "TREATMENT_DECLINED",
         "Patient/family elects not to pursue tube feeding for declining oral intake.",
         "Documented goals-of-care discussion.", "Core hospice transition marker."),
    ],
    SDB: [
        ("Not A Candidate For Aggressive Intervention", "NOT_A_CANDIDATE",
         "Advanced generalized brain decline precludes benefit from aggressive medical intervention.",
         "Physician assessment documented in the record.",
         "Supports terminal-prognosis review using general decline/terminal-status principles."),
        ("Artificial Nutrition Declined", "TREATMENT_DECLINED",
         "Patient/family elects not to pursue tube feeding for declining oral intake.",
         "Documented goals-of-care discussion.", "Core hospice transition marker."),
    ],
}

# ---------------------------------------------------------------------------
# F: FUNCTIONAL IMPACTS
# (impact_name, description, severity)
# ---------------------------------------------------------------------------
FUNCTIONAL_IMPACTS: Dict[str, List[Tuple[str, str, str]]] = {
    STROKE: [
        ("Impaired Mobility", "Reduced or absent ability to ambulate independently after the acute event.", "Moderate-Severe"),
        ("Impaired Communication", "Reduced ability to express or understand language.", "Moderate-Severe"),
        ("Dependence in ADLs", "Requires assistance with bathing, dressing, toileting, feeding.", "Moderate-Severe"),
    ],
    HEMIPLEGIA: [
        ("Total Dependence for Mobility", "Complete reliance on others/devices for all transfers and ambulation.", "Severe"),
        ("Total Dependence for Affected-Side Self-Care", "Unable to use the affected side for any self-care task.", "Severe"),
    ],
    HEMIPARESIS: [
        ("Partial Dependence for Mobility", "Requires assistance or assistive device for ambulation.", "Moderate"),
        ("Reduced Fine-Motor Independence", "Requires assistance with tasks needing affected-hand dexterity.", "Mild-Moderate"),
    ],
    CONTRACTURE: [
        ("Impaired Positioning Tolerance", "Reduced ability to be positioned comfortably for care/comfort.", "Moderate"),
        ("Dependence for Hygiene Within Affected Joint", "Requires caregiver assistance to access/clean the joint area.", "Moderate"),
    ],
    ALZ: [
        ("Progressive Dependence in ADLs", "Escalating need for assistance with bathing, dressing, toileting, feeding.", "Mild-Severe"),
        ("Loss of Independent Ambulation (Advanced Stage)", "Progression to inability to walk without assistance.", "Severe"),
        ("Loss of Independent Communication (Advanced Stage)", "Progression to minimal/absent expressive language.", "Severe"),
    ],
    SDB: [
        ("Progressive Generalized Dependence in ADLs", "Escalating need for assistance across all ADLs from generalized decline.", "Mild-Severe"),
        ("Generalized Functional Slowing", "Diffuse slowing affecting initiation and completion of tasks.", "Moderate"),
    ],
}

# ---------------------------------------------------------------------------
# G: NUTRITIONAL IMPACTS
# (impact_name, description, clinical_significance)
# ---------------------------------------------------------------------------
NUTRITIONAL_IMPACTS: Dict[str, List[Tuple[str, str, str]]] = {
    STROKE: [
        ("Dysphagia-Related Intake Reduction", "Reduced oral intake due to post-stroke swallowing impairment.",
         "Increases aspiration and malnutrition risk; central to nutritional-decline assessment."),
    ],
    ALZ: [
        ("Progressive Feeding Difficulty", "Declining ability to recognize, initiate, or complete oral feeding.",
         "Core marker of advanced-stage nutritional decline."),
        ("Unintentional Weight Loss", "Ongoing weight loss despite available oral intake support.",
         "Supports terminal-prognosis review."),
    ],
    SDB: [
        ("Progressive Feeding Difficulty", "Declining ability to initiate or complete oral feeding from generalized decline.",
         "Core marker of advanced-stage nutritional decline (general-decline basis)."),
        ("Unintentional Weight Loss", "Ongoing weight loss despite available oral intake support.",
         "Supports terminal-prognosis review."),
    ],
}

# ---------------------------------------------------------------------------
# H: END-STAGE FINDINGS
# (finding_name, description, evidence_requirement, clinical_significance, hospice_relevance)
# ---------------------------------------------------------------------------
END_STAGE_FINDINGS: Dict[str, List[Tuple[str, str, str, str, str]]] = {
    STROKE: [
        ("Persistent Vegetative State/Coma Beyond Acute Period", "Sustained unresponsiveness beyond the expected acute recovery window.",
         "Serial neurologic assessments.", "Reflects irreversible severe brain injury.",
         "Core end-stage indicator supporting LCD Stroke and Coma review."),
        ("Medical Complication of Immobility", "Recurrent aspiration, pressure injury, or infection from prolonged immobility.",
         "Clinical/infection documentation.", "Reflects advanced functional decline.",
         "Supports terminal-prognosis review under LCD Stroke and Coma."),
    ],
    ALZ: [
        ("FAST Stage 7c or Beyond", "Loss of speech, ambulation, and ability to sit up independently.",
         "Functional Assessment Staging documentation.", "Defines the advanced/end-stage dementia threshold.",
         "Core end-stage indicator supporting LCD Dementia due to Alzheimer's Disease review."),
        ("Inability to Maintain Adequate Oral Intake", "Sustained inability to eat/drink enough to maintain nutrition.",
         "Weight and intake documentation.", "Reflects terminal decline.",
         "End-stage indicator supporting LCD review."),
    ],
    SDB: [
        ("Advanced Generalized Functional Decline", "Profound, near-total functional dependence from generalized brain decline "
         "(non-Alzheimer-specific staging).", "Functional/PPS assessment.",
         "Reflects end-stage generalized decline.", "Supports terminal-prognosis review using general decline/"
         "terminal-status principles, NOT Alzheimer's-specific FAST criteria."),
        ("Inability to Maintain Adequate Oral Intake", "Sustained inability to eat/drink enough to maintain nutrition.",
         "Weight and intake documentation.", "Reflects terminal decline.",
         "Supports terminal-prognosis review using general decline principles."),
    ],
}

# ---------------------------------------------------------------------------
# I: HOSPICE ELIGIBILITY SUPPORT
# (indicator_name, description, supporting_evidence, lcd_reference)
# ---------------------------------------------------------------------------
HOSPICE_ELIGIBILITY_SUPPORT: Dict[str, List[Tuple[str, str, str, str]]] = {
    STROKE: [
        ("Karnofsky/PPS 40 or Below After Acute Stroke", "Severe functional impairment persisting after the acute event.",
         "Documented KPS/PPS assessment.", "LCD Hospice Eligibility Determination \u2013 Stroke and Coma"),
        ("Coma or Persistent Vegetative State", "Sustained coma/unresponsiveness beyond the acute period.",
         "Serial neurologic assessments.", "LCD Hospice Eligibility Determination \u2013 Stroke and Coma"),
        ("Medical Complications Documented Within First Days", "Aspiration pneumonia, sepsis, or comparable "
         "complication documented in the relevant clinical window.", "Clinical/infection documentation.",
         "LCD Hospice Eligibility Determination \u2013 Stroke and Coma"),
    ],
    ALZ: [
        ("FAST Stage 7a or Beyond", "Loss of ability to speak more than a few intelligible words.",
         "Functional Assessment Staging documentation.",
         "LCD Hospice Eligibility Determination \u2013 Dementia due to Alzheimer's Disease"),
        ("Comorbidity Supporting Limited Prognosis", "Documented comorbidity (e.g. aspiration pneumonia, "
         "pyelonephritis, sepsis, pressure ulcers, recurrent fever) consistent with limited prognosis.",
         "Comorbidity/problem-list documentation.",
         "LCD Hospice Eligibility Determination \u2013 Dementia due to Alzheimer's Disease"),
        ("ADL Dependence Consistent With Advanced Dementia", "Dependence in all basic ADLs consistent with advanced stage.",
         "Functional/ADL assessment.",
         "LCD Hospice Eligibility Determination \u2013 Dementia due to Alzheimer's Disease"),
    ],
    SDB: [
        ("Progressive Generalized Functional Decline (General Decline Principles)", "Ongoing, non-plateauing decline "
         "in overall function assessed with general (non-Alzheimer-specific) decline principles.",
         "Serial functional/PPS assessment.",
         "General Decline / Terminal Status guidance (general_decline_terminal_status.json)"),
        ("Progressive Nutritional Decline (General Decline Principles)", "Ongoing weight loss/reduced intake assessed "
         "with general decline principles.", "Weight and intake documentation.",
         "General Decline / Terminal Status guidance (general_decline_terminal_status.json)"),
        ("Recurrent Medical Complications (General Decline Principles)", "Recurrent infection or comparable "
         "complication reflecting advanced generalized decline.", "Clinical/infection documentation.",
         "General Decline / Terminal Status guidance (general_decline_terminal_status.json)"),
    ],
    HEMIPLEGIA: [
        ("Persistent Total Dependence (General Decline Principles)", "Sustained complete functional dependence "
         "assessed with general decline principles.", "Functional assessment over time.",
         "General Decline / Terminal Status guidance (general_decline_terminal_status.json)"),
    ],
    HEMIPARESIS: [
        ("Progressive Functional Decline (General Decline Principles)", "Ongoing decline in function despite "
         "therapy, assessed with general decline principles.", "Serial functional/therapy assessment.",
         "General Decline / Terminal Status guidance (general_decline_terminal_status.json)"),
    ],
    CONTRACTURE: [
        ("Advanced Multi-Joint Contracture With Functional Decline", "Progressive multi-joint involvement "
         "associated with generalized functional decline.", "Serial range-of-motion and functional assessment.",
         "General Decline / Terminal Status guidance (general_decline_terminal_status.json)"),
    ],
}

# ---------------------------------------------------------------------------
# Supporting: TREATMENTS
# (treatment_name, treatment_category, description)
# ---------------------------------------------------------------------------
TREATMENTS: Dict[str, List[Tuple[str, str, str]]] = {
    STROKE: [
        ("Swallow Evaluation and Dysphagia Management", "SUPPORTIVE",
         "Assessment and management of swallowing safety to reduce aspiration risk."),
        ("Positioning and Skin-Integrity Care", "SUPPORTIVE",
         "Repositioning and pressure-injury prevention for immobile post-stroke patients."),
    ],
    HEMIPLEGIA: [
        ("Range-of-Motion Program", "SUPPORTIVE", "Passive/active-assisted range-of-motion to reduce contracture risk."),
    ],
    HEMIPARESIS: [
        ("Gait and Balance Support", "SUPPORTIVE", "Assistive-device and safety strategies to reduce fall risk."),
    ],
    CONTRACTURE: [
        ("Splinting/Positioning Program", "SUPPORTIVE", "Splinting and positioning aimed at maintaining/improving joint range."),
    ],
    ALZ: [
        ("Behavioral Management Strategies", "SUPPORTIVE", "Non-pharmacologic strategies to reduce agitation/behavioral disturbance."),
        ("Feeding Assistance", "SUPPORTIVE", "Hand-feeding and adaptive strategies to support oral intake."),
    ],
    SDB: [
        ("Feeding Assistance", "SUPPORTIVE", "Hand-feeding and adaptive strategies to support oral intake in generalized decline."),
        ("Comfort-Focused Positioning and Care", "SUPPORTIVE", "Positioning and care strategies focused on comfort given "
         "generalized functional decline."),
    ],
}

# ---------------------------------------------------------------------------
# Supporting: MEDICATIONS
# (medication_name, drug_class, purpose, expected_benefits, common_side_effects, hospice_relevance)
# ---------------------------------------------------------------------------
MEDICATIONS: Dict[str, List[Tuple[str, str, str, str, str, str]]] = {
    STROKE: [
        ("Antiplatelet Therapy (e.g. Aspirin)", "Antiplatelet", "Secondary stroke prevention.",
         "Reduces recurrent ischemic stroke risk.", "Bleeding risk, GI upset.",
         "May be discontinued when goals of care shift to comfort-focused management."),
    ],
    ALZ: [
        ("Cholinesterase Inhibitor (e.g. Donepezil)", "Cholinesterase Inhibitor",
         "Symptomatic cognitive support in mild-moderate disease.",
         "May modestly slow symptomatic decline.", "GI upset, bradycardia.",
         "Benefit diminishes in advanced disease; often discontinued as goals shift to comfort."),
    ],
    SDB: [
        ("Symptomatic/Comfort Medication Management", "Supportive/Comfort",
         "Symptom-directed management (e.g. pain, agitation) rather than disease-modifying therapy.",
         "Supports comfort in generalized decline.", "Varies by agent used.",
         "Central to comfort-focused management as generalized decline advances."),
    ],
}

# ---------------------------------------------------------------------------
# Supporting: PSYCHOSOCIAL CONCERNS
# (concern_name, description)
# ---------------------------------------------------------------------------
PSYCHOSOCIAL_CONCERNS: Dict[str, List[Tuple[str, str]]] = {
    STROKE: [
        ("Loss of Independence", "Distress related to sudden loss of prior functional independence."),
        ("Caregiver Burden", "Strain on family/caregivers managing new post-stroke care needs."),
    ],
    HEMIPLEGIA: [("Body Image Distress", "Distress related to visible unilateral paralysis and dependence.")],
    HEMIPARESIS: [("Fear of Falling", "Anxiety related to gait instability and fall risk.")],
    CONTRACTURE: [("Distress With Care Activities", "Discomfort/distress associated with required repositioning and hygiene.")],
    ALZ: [
        ("Caregiver Burden", "Substantial strain on family caregivers managing progressive dependence and behavioral symptoms."),
        ("Patient Distress From Disorientation", "Distress/agitation related to disorientation and unfamiliar environments."),
    ],
    SDB: [
        ("Caregiver Burden", "Strain on family caregivers managing progressive generalized decline."),
        ("Family Distress Over Uncertain Trajectory", "Distress related to a non-specific, generalized decline course."),
    ],
}

# ---------------------------------------------------------------------------
# Supporting: SPIRITUAL CONCERNS
# (concern_name, description)
# ---------------------------------------------------------------------------
SPIRITUAL_CONCERNS: Dict[str, List[Tuple[str, str]]] = {
    STROKE: [("Sudden Loss of Function/Meaning", "Existential distress related to the abrupt, unexpected nature of stroke-related loss.")],
    ALZ: [("Loss of Personhood Concerns", "Family/patient distress related to progressive loss of identity and recognition.")],
    SDB: [("Loss of Personhood Concerns", "Family distress related to progressive generalized loss of identity and function.")],
}

# ---------------------------------------------------------------------------
# Supporting: INTERDISCIPLINARY TRIGGERS
# (discipline, trigger_condition) -- discipline values only from the
# existing approved enum; RT is never used, and PT/OT are never
# substituted for another discipline.
# ---------------------------------------------------------------------------
INTERDISCIPLINARY_TRIGGERS: Dict[str, List[Tuple[str, str]]] = {
    STROKE: [
        ("MSW", "New post-stroke dependence requiring care-planning/resource support."),
        ("DIETICIAN", "Documented dysphagia affecting nutritional intake."),
    ],
    ALZ: [
        ("MSW", "Escalating caregiver burden requiring psychosocial support/resource planning."),
        ("CHAPLAIN", "Family distress related to progressive loss of personhood."),
    ],
    SDB: [
        ("MSW", "Escalating caregiver burden from generalized decline requiring psychosocial support."),
        ("DIETICIAN", "Progressive feeding difficulty affecting nutritional intake."),
    ],
}

CONCEPT_DOMAINS = [
    (OntologyDiseaseSymptom, "SYMPTOM", "symptom_name", True),
    (OntologyDiseaseFinding, "FINDING", "finding_name", False),
    (OntologyDiseaseLab, "LAB", "lab_name", False),
    (OntologyDiseaseDiagnosticTest, "DIAGNOSTIC_TEST", "test_name", False),
    (OntologyDiseaseComplication, "COMPLICATION", "complication_name", True),
    (OntologyDiseasePrognosticIndicator, "PROGNOSTIC_INDICATOR", "indicator_name", True),
    (OntologyDiseaseTreatmentLimitation, "TREATMENT_LIMITATION", "limitation_name", False),
    (OntologyDiseaseFunctionalImpact, "FUNCTIONAL_IMPACT", "impact_name", True),
    (OntologyDiseaseNutritionalImpact, "NUTRITIONAL_IMPACT", "impact_name", False),
    (OntologyDiseaseEndStageFinding, "END_STAGE_FINDING", "finding_name", False),
    (OntologyDiseaseHospiceEligibilitySupport, "HOSPICE_ELIGIBILITY_SUPPORT", "indicator_name", True),
    (OntologyDiseaseTreatment, "TREATMENT", "treatment_name", False),
    (OntologyDiseaseMedication, "MEDICATION", "medication_name", False),
    (OntologyDiseasePsychosocialConcern, "PSYCHOSOCIAL_CONCERN", "concern_name", False),
    (OntologyDiseaseSpiritualConcern, "SPIRITUAL_CONCERN", "concern_name", False),
]

REQUIRED_VALIDATION_TYPES = [
    "DUPLICATE",
    "ORPHAN",
    "HIERARCHY",
    "DOMAIN_COMPLETENESS",
    "EVIDENCE_COVERAGE",
    "RELATIONSHIP_INTEGRITY",
    "SOURCE_PROVENANCE",
]

# ---------------------------------------------------------------------------
# RELATIONSHIPS -- approved, minimal. No IS_NOT_AUTOMATICALLY_EQUIVALENT_TO
# relationship type is created (it does not exist in the ontology); the
# non-equivalence of Senile Degeneration of Brain to Alzheimer's disease is
# enforced solely via disease_description content and tests, not via a
# relationship row.
# ---------------------------------------------------------------------------
DISEASE_TO_DISEASE_RELATIONSHIPS: List[Tuple[str, str, str]] = [
    (STROKE, "MAY_CAUSE", HEMIPLEGIA),
    (STROKE, "MAY_CAUSE", HEMIPARESIS),
    (HEMIPLEGIA, "MAY_CONTRIBUTE_TO", CONTRACTURE),
    (HEMIPARESIS, "MAY_CONTRIBUTE_TO", CONTRACTURE),
]


def _active_rows(db: Session, model_cls, disease_id) -> List:
    query = db.query(model_cls).filter_by(disease_id=disease_id)
    if hasattr(model_cls, "active"):
        query = query.filter(model_cls.active.is_(True))
    return query.all()


def _get_or_create_system(db: Session) -> OntologyBodySystem:
    return get_or_create_body_system(db, system_name=SYSTEM_NAME)


def _get_or_create_new_family(db: Session, system: OntologyBodySystem) -> OntologyDiseaseFamily:
    """Get-or-create ONLY the new 'Degenerative Brain Disorders' family for
    Senile Degeneration of Brain. Never touches the existing
    'Cerebrovascular Disease' or 'Dementia Disorders' families."""
    return get_or_create_authoritative_family(
        db,
        disease_name=SDB,
        importer_name=IMPORTER_NAME,
        source_manifest=__file__,
        system_name=system.system_name,
    )


def _resolve_existing_diseases(db: Session) -> Dict[str, OntologyDisease]:
    """Resolve the five pre-existing diseases by name only. Raises if any is
    missing -- this script must never create, rename, or re-family them."""
    resolved: Dict[str, OntologyDisease] = {}
    for name in EXISTING_DISEASE_NAMES:
        try:
            resolved[name] = resolve_or_create_authoritative_disease(
                db,
                disease_name=name,
                importer_name=IMPORTER_NAME,
                source_manifest=__file__,
                system_name=SYSTEM_NAME,
                create_if_missing=False,
            )
        except RuntimeError as exc:
            raise RuntimeError(
                "Phase 2 Neurologic expansion requires these pre-existing diseases to already "
                f"exist and was unable to resolve: {name!r}. Aborting without any writes."
            ) from exc
    return resolved


def _canonical_concept_rows(db: Session, model_cls, disease_id, name_attr: str, domain: str, category_attr: str):
    return existing_rows_by_canonical_name(
        db.query(model_cls).filter_by(disease_id=disease_id).all(),
        domain=domain,
        table_name=model_cls.__tablename__,
        disease_id=disease_id,
        importer_name=IMPORTER_NAME,
        name_attr=name_attr,
        category_attr=category_attr,
    )


def _reconcile_canonical_concept_category(
    row,
    *,
    domain: str,
    name_attr: str,
    category_attr: str,
    incoming_name: str,
    incoming_category: str,
) -> None:
    result = reconcile_category(
        domain=domain,
        disease_id=row.disease_id,
        normalized_name=row.normalized_name,
        existing_row_id=row.id,
        existing_display_name=getattr(row, name_attr),
        existing_category=getattr(row, category_attr),
        incoming_display_name=incoming_name,
        incoming_category=incoming_category,
        importer_name=IMPORTER_NAME,
    )
    if result.changed:
        setattr(row, category_attr, result.category)


def _get_or_create_sdb(db: Session, family: OntologyDiseaseFamily) -> OntologyDisease:
    del family
    category, organ, dtype, desc, purpose, hospice_rel = SDB_IDENTITY
    return resolve_or_create_authoritative_disease(
        db,
        disease_name=SDB,
        importer_name=IMPORTER_NAME,
        source_manifest=__file__,
        system_name=SYSTEM_NAME,
        create_if_missing=True,
        create_kwargs={
            "disease_category": category,
            "primary_organ": organ,
            "disease_type": dtype,
            "disease_description": desc,
            "clinical_purpose": purpose,
            "hospice_relevance": hospice_rel,
        },
    )


def _apply_description_appendix(db: Session, disease: OntologyDisease, marker: str, appendix: str) -> int:
    """Idempotently append subtype/terminology knowledge to an existing
    disease's disease_description. Returns 1 if appended, 0 if the marker
    was already present (no-op)."""
    current = disease.disease_description or ""
    if marker in current:
        return 0
    disease.disease_description = current + appendix
    db.flush()
    return 1


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
        db, OntologyDiseaseFinding, FINDINGS, diseases,
        ["finding_name"], ["finding_name", "finding_description"],
    )


def populate_labs(db, diseases) -> int:
    return _populate_simple_domain(
        db, OntologyDiseaseLab, LABS, diseases,
        ["lab_name"],
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
        ["complication_name"],
        ["complication_name", "description", "common_occurrence", "clinical_significance"],
    )


def populate_prognostic_indicators(db, diseases) -> int:
    return _populate_simple_domain(
        db, OntologyDiseasePrognosticIndicator, PROGNOSTIC_INDICATORS, diseases,
        ["indicator_name"], ["indicator_name", "description", "supporting_evidence"],
    )


def populate_hospice_eligibility_support(db, diseases) -> int:
    return _populate_simple_domain(
        db, OntologyDiseaseHospiceEligibilitySupport, HOSPICE_ELIGIBILITY_SUPPORT, diseases,
        ["indicator_name"], ["indicator_name", "description", "supporting_evidence", "lcd_reference"],
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


def populate_treatments(db, diseases) -> int:
    inserted = 0
    for disease_name, rows in TREATMENTS.items():
        disease = diseases[disease_name]
        existing_rows = _canonical_concept_rows(
            db, OntologyDiseaseTreatment, disease.id, "treatment_name", "TREATMENT", "treatment_category"
        )
        for name, category, desc in rows:
            normalized_name = concept_identity_key("TREATMENT", name)
            existing = existing_rows.get(normalized_name)
            if existing is not None:
                _reconcile_canonical_concept_category(
                    existing,
                    domain="TREATMENT",
                    name_attr="treatment_name",
                    category_attr="treatment_category",
                    incoming_name=name,
                    incoming_category=category,
                )
                continue
            new_row = OntologyDiseaseTreatment(
                id=uuid.uuid4(),
                disease_id=disease.id,
                treatment_name=name,
                normalized_name=normalized_name,
                treatment_category=category,
                description=desc,
            )
            db.add(new_row)
            db.flush()
            existing_rows[normalized_name] = new_row
            inserted += 1
    db.flush()
    return inserted


def populate_medications(db, diseases) -> int:
    return _populate_simple_domain(
        db, OntologyDiseaseMedication, MEDICATIONS, diseases,
        ["medication_name"],
        ["medication_name", "drug_class", "purpose", "expected_benefits", "common_side_effects", "hospice_relevance"],
    )


def populate_psychosocial_concerns(db, diseases) -> int:
    return _populate_simple_domain(
        db, OntologyDiseasePsychosocialConcern, PSYCHOSOCIAL_CONCERNS, diseases,
        ["concern_name"], ["concern_name", "description"],
    )


def populate_spiritual_concerns(db, diseases) -> int:
    return _populate_simple_domain(
        db, OntologyDiseaseSpiritualConcern, SPIRITUAL_CONCERNS, diseases,
        ["concern_name"], ["concern_name", "description"],
    )


def populate_interdisciplinary_triggers(db, diseases) -> int:
    inserted = 0
    for disease_name, rows in INTERDISCIPLINARY_TRIGGERS.items():
        disease = diseases[disease_name]
        for discipline, trigger_condition in rows:
            existing = (
                db.query(OntologyDiseaseInterdisciplinaryTrigger)
                .filter_by(disease_id=disease.id, discipline=discipline, trigger_condition=trigger_condition)
                .one_or_none()
            )
            if existing is not None:
                continue
            db.add(
                OntologyDiseaseInterdisciplinaryTrigger(
                    id=uuid.uuid4(),
                    disease_id=disease.id,
                    discipline=discipline,
                    trigger_condition=trigger_condition,
                )
            )
            inserted += 1
    db.flush()
    return inserted


def populate_treatment_limitations(db, diseases) -> int:
    inserted = 0
    for disease_name, rows in TREATMENT_LIMITATIONS.items():
        disease = diseases[disease_name]
        existing_rows = _canonical_concept_rows(
            db,
            OntologyDiseaseTreatmentLimitation,
            disease.id,
            "limitation_name",
            "TREATMENT_LIMITATION",
            "limitation_category",
        )
        for name, category, desc, evidence_req, hospice_rel in rows:
            normalized_name = concept_identity_key("TREATMENT_LIMITATION", name)
            existing = existing_rows.get(normalized_name)
            if existing is not None:
                _reconcile_canonical_concept_category(
                    existing,
                    domain="TREATMENT_LIMITATION",
                    name_attr="limitation_name",
                    category_attr="limitation_category",
                    incoming_name=name,
                    incoming_category=category,
                )
                continue
            row = OntologyDiseaseTreatmentLimitation(
                id=uuid.uuid4(),
                disease_id=disease.id,
                limitation_name=name,
                normalized_name=normalized_name,
                limitation_category=category,
                description=desc,
                evidence_requirement=evidence_req,
                hospice_relevance=hospice_rel,
            )
            db.add(row)
            db.flush()
            existing_rows[normalized_name] = row
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
                    id=uuid.uuid4(),
                    disease_id=disease.id,
                    finding_name=name,
                    description=desc,
                    evidence_requirement=evidence_req,
                    clinical_significance=clinical_sig,
                    hospice_relevance=hospice_rel,
                )
            )
            inserted += 1
    db.flush()
    return inserted


def populate_description_appendices(db, diseases) -> int:
    """Idempotently record Stroke subtype/terminology knowledge and
    Alzheimer's severity/subtype terminology on the existing disease
    descriptions. Returns the number of diseases whose description was
    appended in this call (0 on re-run)."""
    inserted = 0
    inserted += _apply_description_appendix(db, diseases[STROKE], STROKE_SUBTYPE_MARKER, STROKE_SUBTYPE_APPENDIX)
    inserted += _apply_description_appendix(db, diseases[ALZ], ALZ_SUBTYPE_MARKER, ALZ_SUBTYPE_APPENDIX)
    return inserted


def populate_evidence_rules(db, diseases) -> int:
    """J: one active evidence rule per active concept row, for every concept
    domain in CONCEPT_DOMAINS, across all six diseases. Hospice-eligibility-
    support concepts cite the disease-specific LCD (or the general decline
    guidance where no disease-specific LCD exists); all other concept types
    cite the general clinical-knowledge source for that disease."""
    inserted = 0
    disease_ids = {d.id for d in diseases.values()}
    for model_cls, concept_type, name_attr, _required in CONCEPT_DOMAINS:
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
            if concept_type == "HOSPICE_ELIGIBILITY_SUPPORT":
                source_label = LCD_SOURCE_BY_DISEASE_NAME.get(
                    disease_name, EVIDENCE_SOURCE_BY_DISEASE_NAME.get(disease_name)
                )
            else:
                source_label = EVIDENCE_SOURCE_BY_DISEASE_NAME.get(disease_name)
            evidence_type = concept_type
            if concept_type == "DIAGNOSTIC_TEST":
                concept_name = (getattr(row, name_attr) or "").strip().lower()
                evidence_type = "IMAGING" if concept_name in IMAGING_TEST_NAMES else "DIAGNOSTIC_TEST"
            concept_name_display = getattr(row, name_attr)
            db.add(
                OntologyEvidenceRule(
                    id=uuid.uuid4(),
                    concept_type=concept_type,
                    concept_id=row.id,
                    evidence_source=source_label,
                    evidence_type=evidence_type,
                    confidence="moderate",
                    review_trigger="RN_REVIEW",
                    patient_fact_requires_evidence=True,
                    notes=(
                        f"Evidence rule for {concept_type} concept '{concept_name_display}'; "
                        "requires patient-record evidence before treated as documented. General ontology "
                        "knowledge never becomes a patient fact without patient-record evidence "
                        "(DOCUMENTED / DOCUMENTED_ABSENT / HISTORICAL / ACTIVE / RESOLVED / CONFLICTING / "
                        "MISSING classification happens at the patient-evidence layer, not here)."
                    ),
                )
            )
            inserted += 1
    db.flush()
    return inserted


def populate_relationships(db, diseases) -> int:
    inserted = 0

    def _upsert(source_type, source_id, rel_type, target_type, target_id, description):
        nonlocal inserted
        existing = (
            db.query(OntologyRelationship)
            .filter_by(
                source_concept_type=source_type,
                source_concept_id=source_id,
                relationship_type=rel_type,
                target_concept_type=target_type,
                target_concept_id=target_id,
            )
            .one_or_none()
        )
        if existing is not None:
            return
        db.add(
            OntologyRelationship(
                id=uuid.uuid4(),
                source_concept_type=source_type,
                source_concept_id=source_id,
                relationship_type=rel_type,
                target_concept_type=target_type,
                target_concept_id=target_id,
                description=description,
            )
        )
        inserted += 1

    for source_name, rel_type, target_name in DISEASE_TO_DISEASE_RELATIONSHIPS:
        source = diseases.get(source_name)
        target = diseases.get(target_name)
        if source is None or target is None:
            continue
        _upsert(
            "DISEASE", source.id, rel_type, "DISEASE", target.id,
            f"{source_name} {rel_type} {target_name}.",
        )

    db.flush()
    return inserted


def _run_validation_checks(db, disease: OntologyDisease) -> List[Tuple[str, str, str, int, int]]:
    checks: List[Tuple[str, str, str, int, int]] = []
    disease_id = disease.id

    # 1. DUPLICATE
    dup_errors = 0
    dup_detail: List[str] = []
    for model_cls, _ct, name_attr, _req in CONCEPT_DOMAINS:
        rows = db.query(model_cls).filter_by(disease_id=disease_id).all()
        seen: Dict[str, int] = {}
        for row in rows:
            key = (getattr(row, name_attr) or "").strip().lower()
            seen[key] = seen.get(key, 0) + 1
        dups = {k: v for k, v in seen.items() if v > 1}
        if dups:
            dup_errors += len(dups)
            dup_detail.append(f"{model_cls.__tablename__}: {dups}")
    status = "FAIL" if dup_errors else "PASS"
    checks.append((
        "DUPLICATE", status,
        "; ".join(dup_detail) or "No duplicate concept names found in any domain table for this disease.",
        dup_errors, 0,
    ))

    # 2. ORPHAN
    orphan_errors = 0
    orphan_detail: List[str] = []
    if disease.disease_family is None or disease.disease_family.body_system is None:
        orphan_errors += 1
        orphan_detail.append("Disease has no resolvable disease_family/body_system chain.")
    for model_cls, _ct, _name_attr, _req in CONCEPT_DOMAINS:
        rows = db.query(model_cls).filter_by(disease_id=disease_id).all()
        for row in rows:
            if row.disease is None:
                orphan_errors += 1
                orphan_detail.append(f"{model_cls.__tablename__}: orphaned row {row.id}")
    status = "FAIL" if orphan_errors else "PASS"
    checks.append((
        "ORPHAN", status,
        "; ".join(orphan_detail) or "No orphaned domain rows; disease resolves to family and body system.",
        orphan_errors, 0,
    ))

    # 3. HIERARCHY
    hier_errors = 0
    hier_detail: List[str] = []
    family = disease.disease_family
    system = family.body_system if family else None
    if not (disease.disease_name and family and family.family_name and system and system.system_name):
        hier_errors += 1
        hier_detail.append("Hierarchy row incomplete.")
    elif not (disease.active and family.active and system.active):
        hier_errors += 1
        hier_detail.append("Hierarchy row inactive at some level.")
    status = "FAIL" if hier_errors else "PASS"
    detail = "; ".join(hier_detail) or (
        f"3-tier hierarchy intact: {disease.disease_name} -> {family.family_name} -> "
        f"{system.system_name} (all active)."
    )
    checks.append(("HIERARCHY", status, detail, hier_errors, 0))

    # 4. DOMAIN_COMPLETENESS
    completeness_warnings = 0
    completeness_detail: List[str] = []
    for model_cls, _ct, _name_attr, required in CONCEPT_DOMAINS:
        if not required:
            continue
        cnt = db.query(model_cls).filter_by(disease_id=disease_id).count()
        if cnt == 0:
            completeness_warnings += 1
            completeness_detail.append(f"{model_cls.__tablename__}: 0 rows")
    status = "WARNING" if completeness_warnings else "PASS"
    checks.append((
        "DOMAIN_COMPLETENESS", status,
        "; ".join(completeness_detail) or "All required A-K domains have at least one row for this disease.",
        0, completeness_warnings,
    ))

    # 5. EVIDENCE_COVERAGE
    total_concepts = 0
    covered = 0
    for model_cls, concept_type, _name_attr, _req in CONCEPT_DOMAINS:
        rows = _active_rows(db, model_cls, disease_id)
        total_concepts += len(rows)
        for row in rows:
            has_rule = (
                db.query(OntologyEvidenceRule)
                .filter_by(concept_type=concept_type, concept_id=row.id)
                .one_or_none()
            )
            if has_rule is not None:
                covered += 1
    uncovered = total_concepts - covered
    pct = (covered / total_concepts * 100.0) if total_concepts else 0.0
    status = "PASS" if uncovered == 0 else "WARNING"
    checks.append((
        "EVIDENCE_COVERAGE", status,
        f"{covered}/{total_concepts} concept rows have a disease-specific evidence rule ({pct:.1f}%).",
        0, uncovered,
    ))

    # 6. RELATIONSHIP_INTEGRITY
    rel_rows = (
        db.query(OntologyRelationship)
        .filter(
            (OntologyRelationship.source_concept_id == disease_id)
            | (OntologyRelationship.target_concept_id == disease_id)
        )
        .all()
    )
    rel_errors = 0
    rel_detail: List[str] = []
    for rr in rel_rows:
        if rr.source_concept_type == "DISEASE":
            if db.query(OntologyDisease).filter_by(id=rr.source_concept_id).one_or_none() is None:
                rel_errors += 1
                rel_detail.append(f"dangling source {rr.source_concept_id}")
        if rr.target_concept_type == "DISEASE":
            if db.query(OntologyDisease).filter_by(id=rr.target_concept_id).one_or_none() is None:
                rel_errors += 1
                rel_detail.append(f"dangling target {rr.target_concept_id}")
    status = "FAIL" if rel_errors else "PASS"
    checks.append((
        "RELATIONSHIP_INTEGRITY", status,
        "; ".join(rel_detail) or f"{len(rel_rows)} relationship row(s) touching this disease resolve correctly.",
        rel_errors, 0,
    ))

    # 7. SOURCE_PROVENANCE
    prov_missing = 0
    for model_cls, concept_type, _name_attr, _req in CONCEPT_DOMAINS:
        rows = db.query(model_cls).filter_by(disease_id=disease_id).all()
        for row in rows:
            rule = (
                db.query(OntologyEvidenceRule)
                .filter_by(concept_type=concept_type, concept_id=row.id)
                .one_or_none()
            )
            if rule is not None and not rule.evidence_source:
                prov_missing += 1
    status = "FAIL" if prov_missing else "PASS"
    checks.append((
        "SOURCE_PROVENANCE", status,
        "All evidence rules for this disease carry a non-null evidence_source."
        if not prov_missing else f"{prov_missing} evidence rule(s) missing evidence_source.",
        prov_missing, 0,
    ))

    return checks


def populate_validation_results(db, diseases) -> int:
    inserted = 0
    for disease in diseases.values():
        checks = _run_validation_checks(db, disease)
        for validation_type, status, details, error_count, warning_count in checks:
            existing = (
                db.query(OntologyDiseaseValidationResult)
                .filter_by(disease_id=disease.id, validation_type=validation_type)
                .one_or_none()
            )
            if existing is not None:
                existing.validation_status = status
                existing.details = details
                existing.error_count = error_count
                existing.warning_count = warning_count
                existing.validator_version = "phase2-v1"
                continue
            db.add(
                OntologyDiseaseValidationResult(
                    id=uuid.uuid4(),
                    disease_id=disease.id,
                    validation_type=validation_type,
                    validation_status=status,
                    details=details,
                    error_count=error_count,
                    warning_count=warning_count,
                    validator_version="phase2-v1",
                )
            )
            inserted += 1
    db.flush()
    return inserted


def run(db: Session) -> Dict[str, int]:
    """Run the full Phase 2 Neurologic knowledge expansion against the given
    session. Does not commit -- the caller controls the transaction
    boundary. Safe to call repeatedly; returns the count of NEW rows
    inserted in this call for each domain (0 on a fully-idempotent
    re-run)."""
    system = _get_or_create_system(db)
    new_family = _get_or_create_new_family(db, system)

    diseases = _resolve_existing_diseases(db)
    diseases[SDB] = _get_or_create_sdb(db, new_family)

    counts = {
        "description_appendices_applied": populate_description_appendices(db, diseases),
        "symptoms_inserted": populate_symptoms(db, diseases),
        "findings_inserted": populate_findings(db, diseases),
        "labs_inserted": populate_labs(db, diseases),
        "diagnostics_inserted": populate_diagnostics(db, diseases),
        "complications_inserted": populate_complications(db, diseases),
        "prognostic_indicators_inserted": populate_prognostic_indicators(db, diseases),
        "hospice_eligibility_support_inserted": populate_hospice_eligibility_support(db, diseases),
        "functional_impacts_inserted": populate_functional_impacts(db, diseases),
        "nutritional_impacts_inserted": populate_nutritional_impacts(db, diseases),
        "treatments_inserted": populate_treatments(db, diseases),
        "medications_inserted": populate_medications(db, diseases),
        "psychosocial_concerns_inserted": populate_psychosocial_concerns(db, diseases),
        "spiritual_concerns_inserted": populate_spiritual_concerns(db, diseases),
        "interdisciplinary_triggers_inserted": populate_interdisciplinary_triggers(db, diseases),
        "treatment_limitations_inserted": populate_treatment_limitations(db, diseases),
        "end_stage_findings_inserted": populate_end_stage_findings(db, diseases),
        "evidence_rules_inserted": populate_evidence_rules(db, diseases),
        "relationships_inserted": populate_relationships(db, diseases),
        "validation_results_inserted": populate_validation_results(db, diseases),
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
