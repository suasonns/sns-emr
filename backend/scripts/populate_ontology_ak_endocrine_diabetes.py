# scripts/populate_ontology_ak_endocrine_diabetes.py
"""
Idempotent population script for the Endocrine System (A-K, all domains):

    System:  Endocrine System
    Family:  Diabetes Mellitus and Related Disorders
    Diseases:
        - Type 1 Diabetes Mellitus (autoimmune, absolute insulin deficiency)
        - Type 2 Diabetes Mellitus (insulin resistance, relative deficiency)
        - Gestational Diabetes Mellitus (pregnancy-onset glucose intolerance)
        - Other Specified Diabetes Mellitus (pancreatogenic/Type 3c,
          monogenic/MODY, drug- or chemical-induced)
        - Diabetes Insipidus (ADH/water-regulation disorder -- NOT a
          glucose-metabolism disorder; modeled separately and never treated
          as interchangeable with the four Diabetes Mellitus variants above)

Source ownership:
    - A, B, C, D, F, G, J, K, and Treatment Limitations (E) / End-Stage
      Findings (H): general endocrinology clinical knowledge (ADA/WHO
      diabetes classification framework; standard diabetes-complication and
      posterior-pituitary/ADH physiology literature). No disease-specific
      hospice LCD exists in this repository for any diabetes variant, and
      none is fabricated here.
    - I (Hospice Eligibility Support) only: the existing, generic,
      non-disease-specific general-decline guidance already present at
      backend/app/config/lcd/general_decline_terminal_status.json (CMS LCD
      L33393, "Determining Terminal Status", Part I & Part II). This is
      explicitly generic decline criteria (KPS/PPS < 70, weight loss >= 10%
      in 6 months, ADL dependency, documented functional decline) -- it is
      not a diabetes-specific LCD and is never labeled as one.

Every system/family/disease/concept row is resolved by stable name (never a
hardcoded UUID) and inserted only if a matching row does not already exist
by the table's existing unique constraint. Re-running this script is always
safe:

    - missing records are inserted
    - matching records are left unchanged
    - no records are ever deleted
    - no other body system, disease, or patient/staff table is touched

Run with: .\\.venv\\Scripts\\python.exe scripts\\populate_ontology_ak_endocrine_diabetes.py
"""

from __future__ import annotations

import uuid
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from app.core.database import SessionLocal

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

SYSTEM_NAME = "Endocrine System"
FAMILY_NAME = "Diabetes Mellitus and Related Disorders"

T1DM = "Type 1 Diabetes Mellitus"
T2DM = "Type 2 Diabetes Mellitus"
GDM = "Gestational Diabetes Mellitus"
OSDM = "Other Specified Diabetes Mellitus"
DI = "Diabetes Insipidus"
APPROVED_DISEASE_NAMES = [T1DM, T2DM, GDM, OSDM, DI]

ENDO_SOURCE = (
    "General endocrinology clinical knowledge (ADA/WHO diabetes "
    "classification and diagnostic framework; standard diabetes-"
    "complication literature)"
)
DI_SOURCE = (
    "General endocrinology clinical knowledge (posterior pituitary/ADH "
    "physiology; central vs. nephrogenic Diabetes Insipidus "
    "differentiation literature)"
)
GENERAL_DECLINE_SOURCE = (
    "CMS LCD L33393 - Hospice Determining Terminal Status, General "
    "Decline Guidelines (Part I & Part II); non-disease-specific "
    "(backend/app/config/lcd/general_decline_terminal_status.json). Not a "
    "diabetes-specific LCD -- no such document exists in this repository."
)
# Short form for the 255-char lcd_reference column; full context lives in
# GENERAL_DECLINE_SOURCE (used for the description/notes text only).
GENERAL_DECLINE_LCD_REFERENCE = (
    "CMS LCD L33393 - General Decline Guidelines (non-disease-specific; "
    "not a diabetes-specific LCD)"
)
# Short form (<=255 chars) for the evidence_source column (String(255));
# GENERAL_DECLINE_SOURCE above is used only in longer free-text (Text)
# fields such as OntologyEvidenceRule.notes.
GENERAL_DECLINE_EVIDENCE_SOURCE = (
    "CMS LCD L33393 - General Decline Guidelines, non-disease-specific "
    "(general_decline_terminal_status.json); not a diabetes-specific LCD."
)

EVIDENCE_SOURCE_BY_DISEASE_NAME: Dict[str, str] = {
    T1DM: ENDO_SOURCE,
    T2DM: ENDO_SOURCE,
    GDM: ENDO_SOURCE,
    OSDM: ENDO_SOURCE,
    DI: DI_SOURCE,
}
# Domain I (Hospice Eligibility Support) always cites GENERAL_DECLINE_SOURCE
# regardless of which disease it is attached to -- handled explicitly in
# populate_evidence_rules below, not via this generic per-disease map.

# ---------------------------------------------------------------------------
# A: DISEASE IDENTITY
# (disease_category, primary_organ, disease_type, disease_description,
#  clinical_purpose, hospice_relevance)
# ---------------------------------------------------------------------------
DISEASE_IDENTITY: Dict[str, Tuple[str, str, str, str, str, str]] = {
    T1DM: (
        "Endocrine",
        "Pancreas (Islet Beta Cells)",
        "Autoimmune Insulin-Deficient Diabetes",
        "Autoimmune destruction of pancreatic beta cells resulting in "
        "absolute insulin deficiency. Onset is typically in childhood or "
        "young adulthood but can occur at any age (including latent "
        "autoimmune diabetes in adults). Exogenous insulin is required for "
        "survival; this distinguishes Type 1 from Type 2 Diabetes Mellitus, "
        "which involves relative, not absolute, insulin deficiency.",
        "Differentiates absolute insulin deficiency (Type 1) from insulin "
        "resistance with relative deficiency (Type 2) so that AI clinical "
        "reasoning about glycemic management, complication risk, and "
        "treatment-limitation review is phenotype-specific rather than "
        "generic 'diabetes' reasoning.",
        "Advanced Type 1 Diabetes Mellitus with recurrent severe "
        "hypoglycemia, hypoglycemia unawareness, and progressive end-organ "
        "complications (renal, cardiovascular, neuropathic) may support "
        "terminal-prognosis review in combination with documented general "
        "functional decline.",
    ),
    T2DM: (
        "Endocrine",
        "Pancreas (Islet Beta Cells) / Peripheral Insulin-Target Tissue",
        "Insulin-Resistant Diabetes with Relative Insulin Deficiency",
        "Progressive peripheral insulin resistance combined with relative "
        "(not absolute) insulin deficiency from age- and metabolic-"
        "syndrome-related beta-cell decline. The most common diabetes "
        "phenotype; strongly associated with obesity, metabolic syndrome, "
        "and family history.",
        "Differentiates insulin resistance (Type 2) from autoimmune "
        "absolute insulin deficiency (Type 1) so AI reasoning about "
        "expected treatment progression (lifestyle -> oral agents -> "
        "insulin) and complication timelines is phenotype-specific.",
        "Advanced Type 2 Diabetes Mellitus with recurrent hospitalization "
        "for hyperglycemic crises or hypoglycemia, progressive diabetic "
        "nephropathy toward Chronic Kidney Disease/End Stage Renal "
        "Disease, and declining functional status may support terminal-"
        "prognosis review in combination with documented general decline.",
    ),
    GDM: (
        "Endocrine",
        "Pancreas (Pregnancy-Induced Insulin Resistance)",
        "Pregnancy-Onset Glucose Intolerance",
        "Glucose intolerance with onset or first recognition during "
        "pregnancy, driven by placental-hormone-induced insulin "
        "resistance. Typically resolves postpartum but confers markedly "
        "elevated lifetime risk of progression to overt Type 2 Diabetes "
        "Mellitus.",
        "Differentiates a typically self-limited, pregnancy-bounded "
        "glucose-intolerance state from the chronic Diabetes Mellitus "
        "phenotypes, while preserving the documented risk of postpartum "
        "progression to Type 2 Diabetes Mellitus as prognostic knowledge.",
        "Gestational Diabetes Mellitus is not itself a terminal or "
        "hospice-relevant condition. Hospice relevance applies only if "
        "progression to overt postpartum Type 2 Diabetes Mellitus is "
        "separately documented as an ongoing diagnosis, or if an unrelated "
        "terminal condition co-exists.",
    ),
    OSDM: (
        "Endocrine",
        "Pancreas (Secondary, Genetic, or Drug-Induced)",
        "Secondary or Genetically-Defined Diabetes",
        "Diabetes due to an identifiable cause distinct from typical Type "
        "1 or Type 2 Diabetes Mellitus, including pancreatogenic diabetes "
        "(Type 3c, e.g. following chronic pancreatitis or pancreatectomy), "
        "monogenic diabetes (e.g. MODY), and drug- or chemical-induced "
        "diabetes (e.g. glucocorticoid-induced hyperglycemia).",
        "Differentiates diabetes with an identifiable secondary/genetic/"
        "drug-related cause from idiopathic Type 1/Type 2 phenotypes, so "
        "AI reasoning can account for the underlying driver rather than "
        "treating all diabetes as one undifferentiated disease.",
        "Hospice relevance depends primarily on the severity and "
        "prognosis of the underlying cause (e.g. pancreatic cancer, "
        "chronic pancreatitis, extensive pancreatectomy) rather than on "
        "the diabetes itself; documented general decline principles apply "
        "when present.",
    ),
    DI: (
        "Endocrine",
        "Hypothalamus / Posterior Pituitary / Kidney (ADH Axis)",
        "ADH/Water-Regulation Disorder (Not a Glucose-Metabolism Disorder)",
        "A disorder of antidiuretic hormone (ADH/vasopressin) production "
        "(central Diabetes Insipidus) or renal response to ADH "
        "(nephrogenic Diabetes Insipidus), resulting in impaired urine "
        "concentration, polyuria, and polydipsia. Pathophysiologically and "
        "clinically distinct from Type 1, Type 2, Gestational, and Other "
        "Specified Diabetes Mellitus despite the shared 'diabetes' name -- "
        "there is no shared glucose-metabolism pathology, and Diabetes "
        "Insipidus does not involve hyperglycemia, insulin, or pancreatic "
        "beta-cell function.",
        "Ensures AI clinical reasoning never conflates Diabetes Insipidus "
        "with any glucose-metabolism Diabetes Mellitus variant purely on "
        "the basis of shared naming.",
        "Severe, uncontrolled Diabetes Insipidus with resulting "
        "hypernatremic dehydration may support terminal-prognosis review, "
        "but typically only in the context of an underlying terminal "
        "condition (e.g. CNS malignancy, severe traumatic brain injury) "
        "driving central Diabetes Insipidus.",
    ),
}

# ---------------------------------------------------------------------------
# B: SYMPTOMS
# (symptom_name, description, hospice_relevance, severity_scale)
# ---------------------------------------------------------------------------
SYMPTOMS: Dict[str, List[Tuple[str, str, str, str]]] = {
    T1DM: [
        ("Polyuria", "Excessive urination from osmotic diuresis due to hyperglycemia.",
         "Tracks glycemic control trend.", "Mild to severe"),
        ("Polydipsia", "Excessive thirst driven by osmotic fluid loss.",
         "Tracks glycemic control trend.", "Mild to severe"),
        ("Unintentional Weight Loss with Polyphagia", "Weight loss despite increased appetite from absolute insulin deficiency.",
         "Supports uncontrolled/undiagnosed disease or treatment failure.", "Moderate to severe"),
        ("Fatigue", "Generalized tiredness from cellular glucose underutilization.",
         "Contributes to functional decline assessment.", "Mild to severe"),
        ("Blurred Vision", "Osmotic lens changes from fluctuating glucose levels.",
         "May precede or accompany retinopathy.", "Mild to moderate"),
        ("Nausea and Vomiting", "Common presenting/associated symptom of diabetic ketoacidosis.",
         "Direct DKA warning sign requiring urgent evaluation.", "Moderate to severe"),
    ],
    T2DM: [
        ("Polyuria", "Excessive urination from osmotic diuresis due to hyperglycemia.",
         "Tracks glycemic control trend.", "Mild to severe"),
        ("Polydipsia", "Excessive thirst driven by osmotic fluid loss.",
         "Tracks glycemic control trend.", "Mild to severe"),
        ("Fatigue", "Generalized tiredness from insulin resistance and hyperglycemia.",
         "Contributes to functional decline assessment.", "Mild to severe"),
        ("Blurred Vision", "Osmotic lens changes from fluctuating glucose levels.",
         "May precede or accompany retinopathy.", "Mild to moderate"),
        ("Slow-Healing Wounds", "Impaired wound healing from microvascular disease and hyperglycemia.",
         "Early marker of vascular/neuropathic complications.", "Mild to severe"),
        ("Peripheral Numbness or Tingling", "Sensory symptom of early diabetic peripheral neuropathy.",
         "Marker of neuropathic complication onset.", "Mild to severe"),
    ],
    GDM: [
        ("Increased Thirst and Urination", "Often mild or subclinical; frequently detected via routine screening rather than symptoms.",
         "Usually not itself hospice-relevant.", "Mild"),
        ("Fatigue", "Common in pregnancy generally; nonspecific for Gestational Diabetes Mellitus.",
         "Nonspecific; not independently hospice-relevant.", "Mild"),
    ],
    OSDM: [
        ("Polyuria", "Excessive urination from osmotic diuresis; presentation varies with underlying cause.",
         "Tracks glycemic control trend.", "Mild to severe"),
        ("Polydipsia", "Excessive thirst driven by osmotic fluid loss.",
         "Tracks glycemic control trend.", "Mild to severe"),
        ("Unexplained Weight Loss", "Common in pancreatogenic (Type 3c) diabetes, often reflecting exocrine pancreatic insufficiency.",
         "May reflect underlying pancreatic disease severity.", "Moderate to severe"),
    ],
    DI: [
        ("Marked Polyuria", "Large-volume, dilute urine output disproportionate to fluid intake.",
         "Hallmark presenting symptom; distinguishes from Diabetes Mellitus polyuria.", "Moderate to severe"),
        ("Intense Polydipsia", "Compensatory thirst, often with a preference for cold or iced water.",
         "Reflects attempt to compensate for free-water loss.", "Moderate to severe"),
        ("Nocturia", "Nighttime urinary frequency from persistent free-water diuresis.",
         "Contributes to sleep disruption and functional decline.", "Mild to moderate"),
        ("Signs of Dehydration", "Dry mucous membranes, poor skin turgor when fluid intake cannot keep pace with losses.",
         "Warning sign for hypernatremic dehydration.", "Moderate to severe"),
    ],
}

# ---------------------------------------------------------------------------
# C: COMPLICATIONS
# (complication_name, description, common_occurrence, clinical_significance)
# ---------------------------------------------------------------------------
COMPLICATIONS: Dict[str, List[Tuple[str, str, str, str]]] = {
    T1DM: [
        ("Diabetic Ketoacidosis", "Acute, life-threatening complication from absolute insulin deficiency causing ketone accumulation and acidosis.",
         "uncommon", "Medical emergency; recurrent episodes signal poor control or nonadherence."),
        ("Diabetic Nephropathy", "Progressive kidney damage from chronic hyperglycemia; may progress to Chronic Kidney Disease.",
         "common", "Target of MAY_CONTRIBUTE_TO relationship to Chronic Kidney Disease."),
        ("Diabetic Retinopathy", "Progressive retinal microvascular damage; leading cause of adult-onset blindness.",
         "common", "Marker of long-standing microvascular disease burden."),
        ("Diabetic Peripheral Neuropathy", "Progressive sensorimotor nerve damage, typically distal and symmetric.",
         "common", "Contributes to foot ulceration, falls, and functional decline risk."),
        ("Hypoglycemia Unawareness", "Loss of the ability to sense falling blood glucose, from recurrent hypoglycemia or autonomic neuropathy.",
         "uncommon", "Limits ability to safely intensify glycemic control; treatment-limitation relevant."),
        ("Cardiovascular Disease", "Accelerated atherosclerosis from chronic hyperglycemia and associated risk factors.",
         "common", "Major driver of morbidity and mortality in long-standing disease."),
    ],
    T2DM: [
        ("Hyperosmolar Hyperglycemic State", "Acute, life-threatening complication of severe hyperglycemia without significant ketosis, typically in relative insulin deficiency.",
         "uncommon", "Medical emergency; higher mortality than diabetic ketoacidosis in this population."),
        ("Diabetic Nephropathy", "Progressive kidney damage from chronic hyperglycemia; may progress to Chronic Kidney Disease.",
         "common", "Target of MAY_CONTRIBUTE_TO relationship to Chronic Kidney Disease."),
        ("Diabetic Retinopathy", "Progressive retinal microvascular damage; leading cause of adult-onset blindness.",
         "common", "Marker of long-standing microvascular disease burden."),
        ("Diabetic Peripheral Neuropathy", "Progressive sensorimotor nerve damage, typically distal and symmetric.",
         "common", "Contributes to foot ulceration, falls, and functional decline risk."),
        ("Peripheral Arterial Disease with Diabetic Foot Ulcer", "Macrovascular disease combined with neuropathy leading to non-healing foot ulceration.",
         "common", "Major driver of amputation risk and functional decline."),
        ("Cardiovascular Disease", "Accelerated atherosclerosis from chronic hyperglycemia, hypertension, and dyslipidemia.",
         "common", "Leading cause of death in this population."),
    ],
    GDM: [
        ("Preeclampsia", "Pregnancy-specific hypertensive complication with increased incidence in Gestational Diabetes Mellitus.",
         "uncommon", "Maternal complication requiring obstetric management; not independently hospice-relevant."),
        ("Fetal Macrosomia", "Excess fetal growth from maternal hyperglycemia exposure.",
         "common", "Obstetric/neonatal complication; not a maternal hospice-relevant finding."),
        ("Postpartum Progression to Type 2 Diabetes Mellitus", "Well-documented elevated lifetime risk of developing overt Type 2 Diabetes Mellitus after a Gestational Diabetes Mellitus pregnancy.",
         "common", "Prognostic bridge to the Type 2 Diabetes Mellitus disease record; not itself a complication of pregnancy."),
    ],
    OSDM: [
        ("Exocrine Pancreatic Insufficiency", "Impaired digestive enzyme production, most characteristic of pancreatogenic (Type 3c) diabetes.",
         "common", "Drives malnutrition risk distinct from typical Type 1/Type 2 Diabetes Mellitus."),
        ("Malnutrition Secondary to Underlying Pancreatic Disease", "Combined endocrine and exocrine pancreatic failure impairing nutrient absorption and glycemic stability.",
         "common", "Reflects underlying disease severity more than glycemic control alone."),
        ("Brittle Glycemic Control", "Unpredictable glucose swings from loss of both insulin and counter-regulatory glucagon secretion.",
         "common", "Complicates safe treatment intensification; treatment-limitation relevant."),
    ],
    DI: [
        ("Severe Hypernatremia", "Elevated serum sodium from free-water loss exceeding intake.",
         "uncommon", "Medical emergency if severe or rapid; can impair mental status."),
        ("Dehydration", "Volume depletion from persistent free-water diuresis.",
         "common", "Compounds functional decline if fluid access is limited."),
        ("Hypovolemic Shock", "Severe volume depletion when free-water losses are extreme and unreplaced.",
         "uncommon", "Life-threatening if fluid access is impaired (e.g. altered consciousness, immobility)."),
    ],
}

# ---------------------------------------------------------------------------
# Findings (optional domain)
# (finding_name, finding_description)
# ---------------------------------------------------------------------------
FINDINGS: Dict[str, List[Tuple[str, str]]] = {
    T1DM: [
        ("Kussmaul Respirations", "Deep, labored breathing pattern seen in diabetic ketoacidosis as respiratory compensation for metabolic acidosis."),
        ("Fruity Breath Odor", "Acetone breath odor associated with ketosis in diabetic ketoacidosis."),
    ],
    T2DM: [
        ("Acanthosis Nigricans", "Velvety hyperpigmented skin, typically at the neck/axillae, marking significant insulin resistance."),
    ],
    GDM: [],
    OSDM: [
        ("Steatorrhea", "Fatty, foul-smelling stool reflecting exocrine pancreatic insufficiency in pancreatogenic (Type 3c) diabetes."),
    ],
    DI: [
        ("Large-Volume Dilute Urine Output", "Urine output disproportionately large and dilute relative to fluid intake and hydration status."),
    ],
}

# ---------------------------------------------------------------------------
# Labs (optional domain)
# (lab_name, normal_range, expected_abnormal_range, clinical_significance,
#  hospice_significance)
# ---------------------------------------------------------------------------
LABS: Dict[str, List[Tuple[str, str, str, str, str]]] = {
    T1DM: [
        ("Hemoglobin A1c", "<5.7%", ">=6.5% (diagnostic); trend used for control assessment",
         "Reflects average glycemic control over ~3 months.", "Persistently poor or unmeasurable control supports declining self-management capacity."),
        ("C-Peptide", "Detectable, proportional to endogenous insulin production", "Low or undetectable",
         "Confirms absolute insulin deficiency (endogenous insulin production is low/absent).", "Not independently hospice-relevant."),
        ("Islet Autoantibodies (e.g. GAD65)", "Negative", "Positive",
         "Confirms autoimmune etiology distinguishing Type 1 from Type 2 Diabetes Mellitus.", "Not independently hospice-relevant."),
    ],
    T2DM: [
        ("Hemoglobin A1c", "<5.7%", ">=6.5% (diagnostic); trend used for control assessment",
         "Reflects average glycemic control over ~3 months.", "Persistently poor or unmeasurable control supports declining self-management capacity."),
        ("Fasting Plasma Glucose", "70-99 mg/dL", ">=126 mg/dL (diagnostic)",
         "Confirms hyperglycemia and tracks control.", "Recurrent extremes (high or low) support functional decline."),
    ],
    GDM: [
        ("Oral Glucose Tolerance Test (1-Hour/2-Hour Glucose)", "Below pregnancy-specific diagnostic thresholds", "Meets or exceeds pregnancy-specific diagnostic thresholds",
         "Primary diagnostic test for Gestational Diabetes Mellitus.", "Not hospice-relevant."),
    ],
    OSDM: [
        ("Hemoglobin A1c", "<5.7%", ">=6.5% (diagnostic); trend used for control assessment",
         "Reflects average glycemic control over ~3 months.", "Persistently poor control supports declining self-management capacity."),
        ("Fecal Elastase", "Normal", "Low",
         "Confirms exocrine pancreatic insufficiency in pancreatogenic (Type 3c) diabetes.", "Supports malnutrition risk assessment."),
    ],
    DI: [
        ("Serum Sodium", "135-145 mEq/L", ">145 mEq/L (hypernatremia)",
         "Reflects free-water deficit severity.", "Marked, worsening hypernatremia supports terminal-prognosis review when paired with an underlying terminal condition."),
        ("Serum and Urine Osmolality", "Serum 275-295 mOsm/kg; urine concentrated relative to serum", "Serum elevated with inappropriately dilute urine",
         "Confirms impaired urine-concentrating ability characteristic of Diabetes Insipidus.", "Tracks disease severity and treatment response."),
    ],
}

# ---------------------------------------------------------------------------
# Diagnostics (optional domain)
# (test_name, purpose, expected_findings, evidence_weight)
# ---------------------------------------------------------------------------
DIAGNOSTICS: Dict[str, List[Tuple[str, str, str, str]]] = {
    T1DM: [
        ("Autoantibody Panel", "Confirm autoimmune etiology.", "Positive islet autoantibodies (e.g. GAD65, IA-2, ZnT8).", "high"),
    ],
    T2DM: [],
    GDM: [
        ("Oral Glucose Tolerance Test", "Diagnose Gestational Diabetes Mellitus per pregnancy-specific thresholds.", "One or more glucose values meeting or exceeding diagnostic thresholds.", "high"),
    ],
    OSDM: [
        ("Pancreatic Imaging and/or Genetic Testing", "Identify underlying pancreatogenic, genetic (e.g. MODY), or drug-related cause.", "Structural pancreatic disease, genetic mutation, or exposure history consistent with a secondary cause.", "moderate"),
    ],
    DI: [
        ("Water Deprivation Test with Desmopressin Response", "Differentiate central from nephrogenic Diabetes Insipidus and confirm diagnosis.", "Failure to concentrate urine during deprivation; central DI responds to desmopressin, nephrogenic DI does not.", "high"),
    ],
}

# ---------------------------------------------------------------------------
# D: PROGNOSTIC INDICATORS
# (indicator_name, description, supporting_evidence)
# ---------------------------------------------------------------------------
PROGNOSTIC_INDICATORS: Dict[str, List[Tuple[str, str, str]]] = {
    T1DM: [
        ("Disease Duration", "Longer duration is associated with increasing microvascular/macrovascular complication burden.", "Documented diagnosis date/history."),
        ("Hemoglobin A1c Trend", "Sustained poor control accelerates complication onset; sudden improvement/instability may reflect declining self-management.", "Serial HbA1c values."),
        ("Presence of Nephropathy or Retinopathy", "Marks advancing microvascular disease burden.", "Lab/imaging/exam findings."),
        ("Frequency of Severe Hypoglycemic Episodes", "Recurrent severe hypoglycemia reflects hypoglycemia unawareness and treatment-limitation relevance.", "Hospitalization/EMS-call history."),
    ],
    T2DM: [
        ("Disease Duration", "Longer duration is associated with increasing complication burden.", "Documented diagnosis date/history."),
        ("Hemoglobin A1c Trend", "Sustained poor control accelerates complication onset.", "Serial HbA1c values."),
        ("Renal Function Trend", "Progressive decline supports advancing diabetic nephropathy toward Chronic Kidney Disease.", "Serial creatinine/eGFR."),
        ("Cardiovascular Comorbidity Burden", "Coexisting cardiovascular disease markedly worsens overall prognosis.", "Documented cardiovascular diagnoses."),
    ],
    GDM: [
        ("Pre-Pregnancy Body Mass Index", "Higher pre-pregnancy BMI increases risk of postpartum progression to Type 2 Diabetes Mellitus.", "Documented pre-pregnancy weight/BMI."),
        ("Postpartum Glucose Tolerance Test Result", "Persistent abnormality indicates progression to overt Type 2 Diabetes Mellitus.", "Postpartum oral glucose tolerance test."),
    ],
    OSDM: [
        ("Severity of Underlying Etiology", "Prognosis is driven primarily by the underlying cause (e.g. pancreatic cancer, chronic pancreatitis, extent of pancreatectomy).", "Underlying-disease diagnosis and staging."),
        ("Degree of Exocrine Pancreatic Insufficiency", "Greater insufficiency worsens nutritional and glycemic prognosis.", "Fecal elastase / malabsorption workup."),
    ],
    DI: [
        ("Underlying Central Nervous System Lesion Prognosis", "For central Diabetes Insipidus, overall prognosis is driven by the underlying hypothalamic/pituitary condition.", "Neuroimaging and underlying-diagnosis findings."),
        ("Serum Sodium Trend", "Worsening or refractory hypernatremia despite treatment indicates poor control.", "Serial serum sodium."),
        ("Response to Desmopressin/Fluid Management", "Poor or diminishing response suggests advancing disease or reduced physiologic reserve.", "Treatment-response documentation."),
    ],
}

# ---------------------------------------------------------------------------
# F: FUNCTIONAL IMPACTS
# (impact_name, description, severity)
# ---------------------------------------------------------------------------
FUNCTIONAL_IMPACTS: Dict[str, List[Tuple[str, str, str]]] = {
    T1DM: [
        ("Activity Limitation from Hypoglycemia Risk", "Fear of or actual hypoglycemic episodes limiting independent activity.", "mild to severe"),
        ("Visual Impairment from Retinopathy", "Progressive vision loss limiting independent function.", "mild to severe"),
        ("Mobility Limitation from Neuropathy", "Sensory/motor deficits impairing gait and balance.", "mild to severe"),
    ],
    T2DM: [
        ("Activity Limitation from Hypoglycemia Risk", "Fear of or actual hypoglycemic episodes limiting independent activity.", "mild to severe"),
        ("Mobility Limitation from Neuropathy or Amputation", "Sensory/motor deficits or limb loss impairing gait and independence.", "moderate to severe"),
        ("Visual Impairment from Retinopathy", "Progressive vision loss limiting independent function.", "mild to severe"),
    ],
    GDM: [
        ("Pregnancy-Associated Fatigue", "General fatigue common in pregnancy, not independently disabling.", "mild"),
    ],
    OSDM: [
        ("Functional Limitation from Underlying Pancreatic Disease", "Functional status is generally driven more by the underlying cause than by glycemic control alone.", "variable"),
    ],
    DI: [
        ("Sleep Disruption from Nocturia", "Frequent nighttime urination impairing rest.", "mild to moderate"),
        ("Activity Limitation from Need for Constant Fluid Access", "Dependence on frequent fluid intake limits activities where access is restricted.", "mild to severe"),
    ],
}

# ---------------------------------------------------------------------------
# G: NUTRITIONAL IMPACTS
# (impact_name, description, clinical_significance)
# ---------------------------------------------------------------------------
NUTRITIONAL_IMPACTS: Dict[str, List[Tuple[str, str, str]]] = {
    T1DM: [
        ("Carbohydrate-Counting Dietary Management", "Requires ongoing carbohydrate intake matching to insulin dosing.", "Central to safe glycemic management."),
        ("Weight Loss from Untreated Insulin Deficiency", "Catabolic weight loss occurs when insulin therapy is inadequate.", "Reflects treatment adequacy."),
    ],
    T2DM: [
        ("Obesity-Associated Nutritional Risk", "Excess adiposity contributes to insulin resistance and cardiometabolic risk.", "Central to disease management strategy."),
        ("Dietary Carbohydrate Restriction", "Structured carbohydrate management supports glycemic control.", "Standard first-line management component."),
    ],
    GDM: [
        ("Gestational Dietary Modification", "Structured meal planning to control maternal glucose without compromising fetal nutrition.", "First-line management; often sufficient alone."),
    ],
    OSDM: [
        ("Malnutrition from Exocrine Pancreatic Insufficiency", "Impaired fat and nutrient absorption in pancreatogenic (Type 3c) diabetes.", "Requires nutritional support distinct from typical Type 1/Type 2 management."),
    ],
    DI: [
        ("Risk of Dehydration and Electrolyte Imbalance from Inadequate Fluid Intake", "Nutritional/fluid intake must keep pace with ongoing free-water losses.", "Central safety consideration in care planning."),
    ],
}

# ---------------------------------------------------------------------------
# Treatments (optional domain, Section 10)
# (treatment_name, treatment_category, description)
# ---------------------------------------------------------------------------
TREATMENTS: Dict[str, List[Tuple[str, str, str]]] = {
    T1DM: [
        ("Basal-Bolus Insulin Therapy", "DISEASE_DIRECTED", "Required lifelong exogenous insulin replacement for absolute insulin deficiency."),
        ("Continuous Glucose Monitoring", "SUPPORTIVE", "Ongoing glucose-trend monitoring to reduce hypoglycemia/hyperglycemia risk."),
        ("Comfort-Focused Glycemic Management", "HOSPICE", "Symptom-focused glucose management when tight control is no longer the goal."),
    ],
    T2DM: [
        ("Oral Antidiabetic Therapy", "DISEASE_DIRECTED", "First-line pharmacologic therapy (e.g. metformin) for insulin resistance."),
        ("Insulin Therapy", "DISEASE_DIRECTED", "Added when oral therapy and lifestyle measures are insufficient."),
        ("Lifestyle and Weight Management", "SUPPORTIVE", "Diet and activity modification to reduce insulin resistance."),
        ("Comfort-Focused Glycemic Management", "HOSPICE", "Symptom-focused glucose management when tight control is no longer the goal."),
    ],
    GDM: [
        ("Medical Nutrition Therapy", "DISEASE_DIRECTED", "First-line management of Gestational Diabetes Mellitus."),
        ("Insulin Therapy During Pregnancy", "DISEASE_DIRECTED", "Added when medical nutrition therapy alone is insufficient for glycemic targets."),
        ("Postpartum Glucose Tolerance Follow-Up", "SUPPORTIVE", "Monitors for progression to overt Type 2 Diabetes Mellitus after delivery."),
    ],
    OSDM: [
        ("Treatment of Underlying Cause", "DISEASE_DIRECTED", "Addresses the identifiable secondary/genetic/drug-related driver of diabetes."),
        ("Pancreatic Enzyme Replacement Therapy", "SUPPORTIVE", "Addresses exocrine pancreatic insufficiency in pancreatogenic (Type 3c) diabetes."),
        ("Comfort-Focused Management", "HOSPICE", "Symptom-focused management when driven by an advanced underlying terminal condition."),
    ],
    DI: [
        ("Desmopressin (DDAVP) Therapy", "DISEASE_DIRECTED", "First-line therapy for central Diabetes Insipidus, replacing deficient ADH."),
        ("Free Water Replacement", "SUPPORTIVE", "Ongoing fluid intake to match free-water losses."),
        ("Comfort-Focused Fluid Management", "HOSPICE", "Symptom-focused fluid/electrolyte management in the context of an underlying terminal condition."),
    ],
}

# ---------------------------------------------------------------------------
# Medications (optional domain, Section 11)
# (medication_name, drug_class, purpose, expected_benefits,
#  common_side_effects, hospice_relevance)
# ---------------------------------------------------------------------------
MEDICATIONS: Dict[str, List[Tuple[str, str, str, str, str, str]]] = {
    T1DM: [
        ("Insulin (Basal/Bolus)", "Hormone Replacement", "Replace absent endogenous insulin.",
         "Glycemic control, prevention of ketoacidosis.", "Hypoglycemia, weight gain.",
         "Discontinuation/dose reduction may be appropriate in comfort-focused care given hypoglycemia risk."),
    ],
    T2DM: [
        ("Metformin", "Biguanide", "Reduce hepatic glucose production and improve insulin sensitivity.",
         "Glycemic control without significant hypoglycemia risk as monotherapy.", "GI upset, rare lactic acidosis (renal impairment).",
         "May be discontinued with declining renal function or oral intake."),
        ("Insulin", "Hormone Replacement", "Supplement or replace endogenous insulin when oral therapy is insufficient.",
         "Glycemic control.", "Hypoglycemia, weight gain.",
         "Discontinuation/dose reduction may be appropriate in comfort-focused care given hypoglycemia risk."),
    ],
    GDM: [
        ("Insulin", "Hormone Replacement", "First-line pharmacologic therapy in pregnancy when medical nutrition therapy is insufficient.",
         "Glycemic control without crossing the placenta.", "Hypoglycemia.",
         "Not applicable; Gestational Diabetes Mellitus is not a hospice-relevant condition."),
    ],
    OSDM: [
        ("Pancreatic Enzyme Replacement", "Digestive Enzyme Supplement", "Replace deficient exocrine pancreatic enzymes.",
         "Improved fat/nutrient absorption, reduced steatorrhea.", "GI upset.",
         "Continued as tolerated for comfort even when disease-directed glycemic goals are relaxed."),
    ],
    DI: [
        ("Desmopressin (DDAVP)", "Synthetic ADH Analog", "Replace deficient antidiuretic hormone in central Diabetes Insipidus.",
         "Reduced polyuria/polydipsia, improved serum sodium control.", "Hyponatremia if fluid intake not adjusted.",
         "May be discontinued or dose-adjusted in comfort-focused care to balance symptom control against hyponatremia risk."),
    ],
}

# ---------------------------------------------------------------------------
# Psychosocial concerns (optional domain)
# (concern_name, description)
# ---------------------------------------------------------------------------
PSYCHOSOCIAL_CONCERNS: Dict[str, List[Tuple[str, str]]] = {
    T1DM: [
        ("Diabetes Distress/Burnout", "Chronic emotional burden of lifelong intensive self-management."),
    ],
    T2DM: [
        ("Diabetes Distress/Burnout", "Chronic emotional burden of lifelong self-management, often compounded by obesity-related stigma."),
    ],
    GDM: [
        ("Anxiety About Maternal/Fetal Outcomes", "Pregnancy-specific anxiety related to glycemic control and delivery outcomes."),
    ],
    OSDM: [
        ("Distress Related to Underlying Disease", "Psychosocial burden often driven more by the underlying condition (e.g. malignancy) than by the diabetes itself."),
    ],
    DI: [
        ("Distress from Constant Thirst and Fluid-Seeking Behavior", "Persistent, disruptive need to seek and consume fluids affecting daily life and social participation."),
    ],
}

# ---------------------------------------------------------------------------
# Spiritual concerns (optional domain)
# (concern_name, description)
# ---------------------------------------------------------------------------
SPIRITUAL_CONCERNS: Dict[str, List[Tuple[str, str]]] = {
    T1DM: [
        ("Meaning-Making Around Lifelong Chronic Illness", "Existential reflection tied to a lifelong, incurable condition diagnosed early in life."),
    ],
    T2DM: [
        ("Meaning-Making Around Declining Independence", "Existential reflection tied to progressive complications and loss of independence."),
    ],
    GDM: [],
    OSDM: [
        ("Existential Distress Tied to Underlying Terminal Disease", "Spiritual distress driven primarily by the underlying condition causing secondary diabetes."),
    ],
    DI: [
        ("Existential Distress Tied to Underlying Neurologic Condition", "Spiritual distress driven primarily by an underlying CNS condition causing central Diabetes Insipidus."),
    ],
}

# ---------------------------------------------------------------------------
# Interdisciplinary Triggers (Section 14)
# (discipline, trigger_condition)
# ---------------------------------------------------------------------------
INTERDISCIPLINARY_TRIGGERS: Dict[str, List[Tuple[str, str]]] = {
    T1DM: [
        ("RN", "Glycemic monitoring and hypoglycemia/hyperglycemia risk assessment."),
        ("DIETICIAN", "Carbohydrate-counting and nutritional management support."),
    ],
    T2DM: [
        ("RN", "Glycemic monitoring and complication-progression care coordination."),
        ("DIETICIAN", "Dietary/weight-management support."),
    ],
    GDM: [
        ("DIETICIAN", "Gestational dietary management support."),
    ],
    OSDM: [
        ("RN", "Glycemic monitoring in the context of an underlying pancreatic or systemic condition."),
        ("DIETICIAN", "Nutritional support for exocrine pancreatic insufficiency."),
    ],
    DI: [
        ("RN", "Fluid balance and serum sodium monitoring."),
        ("PHYSICIAN", "Desmopressin dose titration and underlying-cause management."),
    ],
}

# ---------------------------------------------------------------------------
# E: TREATMENT LIMITATIONS
# (limitation_name, limitation_category, description, evidence_requirement,
#  hospice_relevance)
# Allowed limitation_category values (CHECK constraint):
#   OPTIMALLY_TREATED, TREATMENT_FAILED, TREATMENT_INTOLERANT,
#   NOT_A_CANDIDATE, TREATMENT_DECLINED, TREATMENT_DISCONTINUED,
#   TREATMENT_CONTRAINDICATED, COMFORT_FOCUSED
# ---------------------------------------------------------------------------
TREATMENT_LIMITATIONS: Dict[str, List[Tuple[str, str, str, str, str]]] = {
    T1DM: [
        ("Insulin Therapy Declined", "TREATMENT_DECLINED",
         "Patient declines exogenous insulin therapy despite absolute insulin deficiency.",
         "Requires documented discussion of risks and patient/surrogate decision.",
         "Represents a significant treatment-limitation decision given insulin is required for survival."),
        ("Insulin Therapy Discontinued", "TREATMENT_DISCONTINUED",
         "Previously initiated insulin therapy is stopped.",
         "Requires documented clinical/goals-of-care rationale.",
         "May reflect a shift toward comfort-focused care."),
        ("Intensive Glycemic Control Not a Candidate Due to Hypoglycemia Unawareness", "NOT_A_CANDIDATE",
         "Tight glycemic targets are unsafe given documented hypoglycemia unawareness.",
         "Requires documented hypoglycemia unawareness history.",
         "Supports relaxed glycemic targets rather than intensive control."),
        ("Comfort-Focused Glycemic Management", "COMFORT_FOCUSED",
         "Glycemic management goals shift from tight control to symptom prevention only.",
         "Requires documented goals-of-care discussion.",
         "Directly supports hospice/comfort-care transition."),
    ],
    T2DM: [
        ("Oral Antidiabetic Therapy Failed", "TREATMENT_FAILED",
         "Oral antidiabetic therapy does not achieve adequate glycemic control despite adherence.",
         "Requires documented trial and glycemic response data.",
         "Supports escalation decisions or, alternatively, comfort-focused reassessment."),
        ("Insulin Therapy Declined", "TREATMENT_DECLINED",
         "Patient declines insulin therapy despite clinical indication.",
         "Requires documented discussion of risks and patient/surrogate decision.",
         "Represents a significant treatment-limitation decision."),
        ("Insulin Therapy Discontinued", "TREATMENT_DISCONTINUED",
         "Previously initiated insulin therapy is stopped.",
         "Requires documented clinical/goals-of-care rationale.",
         "May reflect a shift toward comfort-focused care."),
        ("Comfort-Focused Glycemic Management", "COMFORT_FOCUSED",
         "Glycemic management goals shift from tight control to symptom prevention only.",
         "Requires documented goals-of-care discussion.",
         "Directly supports hospice/comfort-care transition."),
    ],
    GDM: [
        ("Medical Nutrition Therapy Alone Insufficient for Glycemic Control", "TREATMENT_FAILED",
         "Dietary management alone fails to achieve pregnancy-specific glycemic targets.",
         "Requires documented dietary trial and glucose monitoring data.",
         "Not hospice-relevant; supports escalation to pharmacologic therapy during pregnancy."),
        ("Insulin Therapy During Pregnancy Declined", "TREATMENT_DECLINED",
         "Patient declines insulin therapy during pregnancy despite clinical indication.",
         "Requires documented discussion of maternal/fetal risks and patient decision.",
         "Not hospice-relevant; a pregnancy-specific treatment decision."),
    ],
    OSDM: [
        ("Pancreatic Enzyme Replacement Therapy Declined", "TREATMENT_DECLINED",
         "Patient declines enzyme replacement despite documented exocrine pancreatic insufficiency.",
         "Requires documented malabsorption evidence and patient decision.",
         "May worsen nutritional decline if declined."),
        ("Insulin Therapy Discontinued", "TREATMENT_DISCONTINUED",
         "Previously initiated insulin therapy is stopped.",
         "Requires documented clinical/goals-of-care rationale.",
         "May reflect a shift toward comfort-focused care driven by the underlying disease."),
        ("Comfort-Focused Management When Driven by Terminal Underlying Disease", "COMFORT_FOCUSED",
         "Glycemic/nutritional management goals shift to comfort only when the underlying cause (e.g. pancreatic cancer) is terminal.",
         "Requires documented goals-of-care discussion and underlying terminal diagnosis.",
         "Directly supports hospice/comfort-care transition driven by the underlying disease."),
    ],
    DI: [
        ("Desmopressin Therapy Declined", "TREATMENT_DECLINED",
         "Patient declines desmopressin therapy despite clinical indication.",
         "Requires documented discussion of risks (dehydration/hypernatremia) and patient/surrogate decision.",
         "Increases risk of dehydration and hypernatremia."),
        ("Desmopressin Therapy Discontinued", "TREATMENT_DISCONTINUED",
         "Previously initiated desmopressin therapy is stopped.",
         "Requires documented clinical/goals-of-care rationale.",
         "May reflect a shift toward comfort-focused care."),
        ("Fluid Replacement Not a Candidate Due to Fluid Overload Risk", "NOT_A_CANDIDATE",
         "Aggressive free-water replacement is unsafe given documented risk of fluid overload (e.g. cardiac/renal comorbidity).",
         "Requires documented comorbidity supporting fluid-overload risk.",
         "Requires balancing dehydration risk against fluid-overload risk."),
        ("Comfort-Focused Management in Setting of Terminal Underlying Condition", "COMFORT_FOCUSED",
         "Fluid/electrolyte management goals shift to comfort only, in the context of an underlying terminal CNS condition.",
         "Requires documented goals-of-care discussion and underlying terminal diagnosis.",
         "Directly supports hospice/comfort-care transition driven by the underlying disease."),
    ],
}

# ---------------------------------------------------------------------------
# H: END-STAGE FINDINGS
# (finding_name, description, evidence_requirement, clinical_significance,
#  hospice_relevance)
# ---------------------------------------------------------------------------
END_STAGE_FINDINGS: Dict[str, List[Tuple[str, str, str, str, str]]] = {
    T1DM: [
        ("Recurrent Severe Hypoglycemia with Loss of Awareness", "Repeated severe hypoglycemic episodes without warning symptoms.",
         "Requires documented episode history (frequency, severity, EMS/hospitalization involvement).",
         "Reflects advanced autonomic dysfunction and limits safe treatment intensification.",
         "Supports terminal-prognosis review in combination with general decline."),
        ("Advanced Diabetic Retinopathy with Blindness", "Severe, vision-threatening or blinding retinal disease.",
         "Requires documented ophthalmologic evaluation.",
         "Reflects long-standing, severe microvascular disease burden.",
         "Contributes to functional decline supporting terminal-prognosis review."),
        ("Diabetic Gastroparesis with Refractory Nutritional Failure", "Severe delayed gastric emptying causing refractory nausea/vomiting and nutritional compromise.",
         "Requires documented gastric-emptying study or refractory symptom history.",
         "Reflects advanced autonomic neuropathy.",
         "Directly supports nutritional decline and terminal-prognosis review."),
    ],
    T2DM: [
        ("Recurrent Severe Hypoglycemia or Hyperglycemic Crisis", "Repeated severe glycemic extremes requiring emergency intervention.",
         "Requires documented episode/hospitalization history.",
         "Reflects declining physiologic reserve and self-management capacity.",
         "Supports terminal-prognosis review in combination with general decline."),
        ("Advanced Diabetic Nephropathy Approaching End Stage Renal Disease", "Progressive renal decline nearing end-stage; see the Chronic Kidney Disease/End Stage Renal Disease disease records for renal-specific end-stage criteria.",
         "Requires documented renal function trend (creatinine/eGFR).",
         "Reflects convergence of diabetic and renal end-stage disease.",
         "Supports terminal-prognosis review together with renal end-stage findings."),
        ("Major Lower-Extremity Amputation", "Amputation from advanced peripheral arterial disease/diabetic foot complications.",
         "Requires documented surgical history.",
         "Reflects severe macrovascular/neuropathic disease burden.",
         "Directly supports functional decline and terminal-prognosis review."),
    ],
    GDM: [
        ("Persistent Postpartum Hyperglycemia", "Glucose intolerance persisting beyond the expected postpartum resolution window.",
         "Requires documented postpartum glucose testing.",
         "Indicates progression from Gestational Diabetes Mellitus to overt Type 2 Diabetes Mellitus rather than an end-stage finding of Gestational Diabetes Mellitus itself.",
         "Not hospice-relevant for Gestational Diabetes Mellitus; relevant only if overt Type 2 Diabetes Mellitus is separately diagnosed and progresses."),
    ],
    OSDM: [
        ("End-Stage Exocrine and Endocrine Pancreatic Failure", "Combined severe exocrine insufficiency and glycemic instability from advanced underlying pancreatic disease.",
         "Requires documented malabsorption and glycemic-control failure.",
         "Reflects near-total pancreatic failure.",
         "Supports terminal-prognosis review together with the underlying disease's own prognosis."),
        ("Refractory Glycemic Instability Related to Advanced Underlying Disease", "Uncontrollable glucose swings despite maximal appropriate therapy.",
         "Requires documented treatment-response history.",
         "Reflects advancing underlying disease rather than diabetes management failure alone.",
         "Supports terminal-prognosis review in the context of the underlying terminal condition."),
    ],
    DI: [
        ("Severe Hypernatremic Dehydration with Altered Mental Status", "Marked hypernatremia causing confusion, lethargy, or coma.",
         "Requires documented serum sodium and mental-status findings.",
         "Reflects severe, uncompensated free-water deficit.",
         "Supports terminal-prognosis review, typically in the context of an underlying terminal CNS condition."),
        ("Uncontrolled Free Water Deficit Despite Maximal Desmopressin Therapy", "Persistent polyuria/hypernatremia despite optimized desmopressin dosing.",
         "Requires documented treatment-response history.",
         "Reflects treatment-refractory disease or profound underlying pathology.",
         "Supports terminal-prognosis review together with the underlying condition's prognosis."),
    ],
}

# ---------------------------------------------------------------------------
# I: HOSPICE ELIGIBILITY SUPPORT -- generic, non-disease-specific general
# decline guidance only (CMS LCD L33393). No diabetes-specific LCD exists
# and none is fabricated. Identical content is used across all five
# diseases because the source criteria are explicitly non-disease-specific.
# (indicator_name, description, supporting_evidence, lcd_reference)
# ---------------------------------------------------------------------------
_GENERAL_DECLINE_ROWS: List[Tuple[str, str, str, str]] = [
    ("Karnofsky/Palliative Performance Score Below 70%", "General functional-status decline threshold from non-disease-specific hospice guidance.",
     "Documented KPS/PPS score.", GENERAL_DECLINE_LCD_REFERENCE),
    ("Weight Loss of at Least 10% in Prior 6 Months", "General non-disease-specific decline indicator.",
     "Documented weight trend.", GENERAL_DECLINE_LCD_REFERENCE),
    ("Dependence in 2 or More Activities of Daily Living", "General non-disease-specific functional-decline indicator.",
     "Documented ADL assessment.", GENERAL_DECLINE_LCD_REFERENCE),
    ("Documented Decline in KPS/PPS Due to Disease Progression", "General non-disease-specific indicator of progressive decline from any underlying disease process.",
     "Serial KPS/PPS assessments.", GENERAL_DECLINE_LCD_REFERENCE),
]

HOSPICE_ELIGIBILITY_SUPPORT: Dict[str, List[Tuple[str, str, str, str]]] = {
    T1DM: list(_GENERAL_DECLINE_ROWS),
    T2DM: list(_GENERAL_DECLINE_ROWS),
    GDM: list(_GENERAL_DECLINE_ROWS),
    OSDM: list(_GENERAL_DECLINE_ROWS),
    DI: list(_GENERAL_DECLINE_ROWS),
}

# ---------------------------------------------------------------------------
# CONCEPT_DOMAINS: (model_cls, concept_type, name_attr, required)
# ---------------------------------------------------------------------------
CONCEPT_DOMAINS = [
    (OntologyDiseaseSymptom, "SYMPTOM", "symptom_name", True),
    (OntologyDiseaseFinding, "FINDING", "finding_name", False),
    (OntologyDiseaseLab, "LAB", "lab_name", False),
    (OntologyDiseaseDiagnosticTest, "DIAGNOSTIC_TEST", "test_name", False),
    (OntologyDiseaseComplication, "COMPLICATION", "complication_name", True),
    (OntologyDiseaseFunctionalImpact, "FUNCTIONAL_IMPACT", "impact_name", True),
    (OntologyDiseaseNutritionalImpact, "NUTRITIONAL_IMPACT", "impact_name", True),
    (OntologyDiseaseHospiceEligibilitySupport, "HOSPICE_ELIGIBILITY_SUPPORT", "indicator_name", True),
    (OntologyDiseaseTreatmentLimitation, "TREATMENT_LIMITATION", "limitation_name", True),
    (OntologyDiseaseEndStageFinding, "END_STAGE_FINDING", "finding_name", True),
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
# RELATIONSHIPS
# Only Type 1 and Type 2 Diabetes Mellitus are approved to carry the
# MAY_CONTRIBUTE_TO Chronic Kidney Disease relationship. Gestational
# Diabetes Mellitus, Other Specified Diabetes Mellitus, and Diabetes
# Insipidus are explicitly excluded per change-control decision.
# (source_disease_name, relationship_type, target_disease_name)
# ---------------------------------------------------------------------------
DISEASE_TO_DISEASE_RELATIONSHIPS: List[Tuple[str, str, str]] = [
    (T1DM, "MAY_CONTRIBUTE_TO", "Chronic Kidney Disease"),
    (T2DM, "MAY_CONTRIBUTE_TO", "Chronic Kidney Disease"),
]

# No disease-to-concept relationships were requested for this task.
DISEASE_TO_CONCEPT_RELATIONSHIPS: List[Tuple[str, str, str, str, str]] = []

# No relationships to diseases outside the existing ontology were
# requested; none were skipped (Chronic Kidney Disease already exists from
# PR #27).
SKIPPED_RELATIONSHIPS_MISSING_TARGET: List[Tuple[str, str, str]] = []


def _active_rows(db: Session, model_cls, disease_id) -> List:
    """Return rows for this disease, filtered to active=True only when the
    model actually has an `active` column."""
    query = db.query(model_cls).filter_by(disease_id=disease_id)
    if hasattr(model_cls, "active"):
        query = query.filter(model_cls.active.is_(True))
    return query.all()


def _get_or_create_system(db: Session) -> OntologyBodySystem:
    system = db.query(OntologyBodySystem).filter_by(system_name=SYSTEM_NAME).one_or_none()
    if system is None:
        system = OntologyBodySystem(id=uuid.uuid4(), system_name=SYSTEM_NAME)
        db.add(system)
        db.flush()
    return system


def _get_or_create_family(db: Session, system: OntologyBodySystem) -> OntologyDiseaseFamily:
    family = (
        db.query(OntologyDiseaseFamily)
        .filter_by(body_system_id=system.id, family_name=FAMILY_NAME)
        .one_or_none()
    )
    if family is None:
        family = OntologyDiseaseFamily(id=uuid.uuid4(), body_system_id=system.id, family_name=FAMILY_NAME)
        db.add(family)
        db.flush()
    return family


def _get_or_create_diseases(db: Session, family: OntologyDiseaseFamily) -> Dict[str, OntologyDisease]:
    diseases: Dict[str, OntologyDisease] = {}
    for name in APPROVED_DISEASE_NAMES:
        disease = db.query(OntologyDisease).filter_by(disease_name=name).one_or_none()
        if disease is None:
            category, organ, dtype, desc, purpose, hospice_rel = DISEASE_IDENTITY[name]
            disease = OntologyDisease(
                id=uuid.uuid4(),
                disease_family_id=family.id,
                disease_name=name,
                disease_category=category,
                primary_organ=organ,
                disease_type=dtype,
                disease_description=desc,
                clinical_purpose=purpose,
                hospice_relevance=hospice_rel,
            )
            db.add(disease)
            db.flush()
        diseases[name] = disease
    return diseases


def _populate_simple_domain(db, model_cls, rows_by_disease, diseases, unique_attrs, field_names) -> int:
    """Generic get-or-create populator for domain tables keyed by
    (disease_id, *unique_attrs)."""
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
    return _populate_simple_domain(
        db, OntologyDiseaseTreatment, TREATMENTS, diseases,
        ["treatment_name", "treatment_category"], ["treatment_name", "treatment_category", "description"],
    )


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
                    id=uuid.uuid4(),
                    disease_id=disease.id,
                    limitation_name=name,
                    limitation_category=category,
                    description=desc,
                    evidence_requirement=evidence_req,
                    hospice_relevance=hospice_rel,
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


def populate_evidence_rules(db, diseases) -> int:
    """J: one active evidence rule per active concept row, for every concept
    domain in CONCEPT_DOMAINS, for all five Endocrine System diseases.
    Hospice-eligibility-support concepts always cite the generic general-
    decline source (GENERAL_DECLINE_SOURCE) regardless of source disease;
    all other concept types cite the disease-specific general
    endocrinology-knowledge source."""
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
                source_label = GENERAL_DECLINE_EVIDENCE_SOURCE
            else:
                source_label = EVIDENCE_SOURCE_BY_DISEASE_NAME.get(disease_name, ENDO_SOURCE)
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
    """Add only supported, non-duplicative cross-disease relationships
    using existing OntologyRelationship rows. Skips any relationship whose
    source or target concept does not exist in the ontology (see
    SKIPPED_RELATIONSHIPS_MISSING_TARGET)."""
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
        source = diseases.get(source_name) or (
            db.query(OntologyDisease).filter_by(disease_name=source_name).one_or_none()
        )
        target = diseases.get(target_name) or (
            db.query(OntologyDisease).filter_by(disease_name=target_name).one_or_none()
        )
        if source is None or target is None:
            continue
        _upsert(
            "DISEASE", source.id, rel_type, "DISEASE", target.id,
            f"{source_name} {rel_type} {target_name}.",
        )

    for source_name, rel_type, target_concept_type, target_disease_name, target_concept_name in (
        DISEASE_TO_CONCEPT_RELATIONSHIPS
    ):
        source = diseases.get(source_name)
        if source is None:
            continue
        target_disease = diseases.get(target_disease_name)
        if target_disease is None:
            continue
        model_cls = next((m for m, ct, _n, _r in CONCEPT_DOMAINS if ct == target_concept_type), None)
        if model_cls is None:
            continue
        name_attr = next(n for _m, ct, n, _r in CONCEPT_DOMAINS if ct == target_concept_type)
        target_row = (
            db.query(model_cls)
            .filter_by(disease_id=target_disease.id, **{name_attr: target_concept_name})
            .one_or_none()
        )
        if target_row is None:
            continue
        _upsert(
            "DISEASE", source.id, rel_type, target_concept_type, target_row.id,
            f"{source_name} {rel_type} {target_concept_name}.",
        )

    db.flush()
    return inserted


def _run_validation_checks(db, disease: OntologyDisease) -> List[Tuple[str, str, str, int, int]]:
    """Compute the seven K validation checks for one disease. Returns
    (validation_type, status, details, error_count, warning_count) tuples."""
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
    disease_rule = (
        db.query(OntologyEvidenceRule)
        .filter_by(concept_type="DISEASE", concept_id=disease_id)
        .one_or_none()
    )
    if disease_rule is not None and not disease_rule.evidence_source:
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
                existing.validator_version = "v1"
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
                    validator_version="v1",
                )
            )
            inserted += 1
    db.flush()
    return inserted


def run(db: Session) -> Dict[str, int]:
    """Run the full A-K population for the Endocrine System (Type 1/Type 2/
    Gestational/Other Specified Diabetes Mellitus + Diabetes Insipidus)
    against the given session. Does not commit -- the caller controls the
    transaction boundary. Safe to call repeatedly; returns the count of NEW
    rows inserted in this call for each domain (0 on a fully-idempotent
    re-run)."""
    system = _get_or_create_system(db)
    family = _get_or_create_family(db, system)
    diseases = _get_or_create_diseases(db, family)

    counts = {
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
