# scripts/populate_ontology_ak_renal_ckd_esrd.py
"""
Idempotent population script for the Renal System (A-K, all domains):

    System:  Renal System
    Family:  Chronic Kidney Disease
    Diseases:
        - Chronic Kidney Disease (primary; general CKD identity, staging,
          chronicity, symptoms, complications, prognosis, functional and
          nutritional decline)
        - End Stage Renal Disease (advanced/end-stage state of CKD G5;
          dialysis/transplant treatment limitations, end-stage findings,
          and hospice eligibility support)

End Stage Renal Disease is linked to Chronic Kidney Disease via a
MAY_PROGRESS_TO relationship -- it is not a separate body system or
family, and Acute Kidney Injury / Acute Renal Failure are not created by
this script. Aliases (CKD, Chronic Renal Disease, Chronic Renal
Insufficiency, ESRD, ESKD, End-Stage Renal Disease, End Stage Kidney
Disease, CKD Stage 5, CKD G5, Terminal Renal Disease) are documented in
each disease's disease_description, never as duplicate disease rows.

Source ownership:
    - A, B, C, D, E, F, G, H, J, K: general Chronic Kidney Disease clinical
      knowledge (KDIGO CKD staging G1-G5 / albuminuria A1-A3, standard
      CKD/ESRD complication and hospice-decline literature).
    - I (Hospice Eligibility Support) only: backend/app/config/lcd/
      esrd_kidney_disease.json ("LCD Hospice Eligibility Determination -
      Kidney Disease (ESRD)"). The LCD does not define the rest of the
      renal ontology.

Every system/family/disease/concept row is resolved by stable name (never
a hardcoded UUID) and inserted only if a matching row does not already
exist by the table's existing unique constraint. Re-running this script is
always safe:

    - missing records are inserted
    - matching records are left unchanged
    - no records are ever deleted
    - no other body system, disease, or patient/staff table is touched

Run with: .\\.venv\\Scripts\\python.exe scripts\\populate_ontology_ak_renal_ckd_esrd.py
"""

from __future__ import annotations

import uuid
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
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

SYSTEM_NAME = "Renal System"
IMPORTER_NAME = "populate_ontology_ak_renal_ckd_esrd"
FAMILY_NAME = "Chronic Kidney Disease"
CKD = "Chronic Kidney Disease"
ESRD = "End Stage Renal Disease"
APPROVED_DISEASE_NAMES = [CKD, ESRD]

CKD_SOURCE = (
    "General Chronic Kidney Disease clinical knowledge (KDIGO CKD G1-G5 / "
    "A1-A3 staging framework; standard CKD/ESRD hospice-decline literature)"
)
LCD_SOURCE = "LCD Hospice Eligibility Determination \u2013 Kidney Disease (ESRD.pdf)"

EVIDENCE_SOURCE_BY_DISEASE_NAME: Dict[str, str] = {
    CKD: CKD_SOURCE,
    ESRD: CKD_SOURCE,
}
# Domain I (hospice eligibility support) always cites the LCD regardless of
# which disease it is attached to -- handled explicitly in
# populate_evidence_rules below, not via this generic per-disease map.

IMAGING_TEST_NAMES = {"renal ultrasound"}

# ---------------------------------------------------------------------------
# A: DISEASE IDENTITY
# (disease_category, primary_organ, disease_type, disease_description,
#  clinical_purpose, hospice_relevance)
# ---------------------------------------------------------------------------
DISEASE_IDENTITY: Dict[str, Tuple[str, str, str, str, str, str]] = {
    CKD: (
        "Renal",
        "Kidney",
        "Chronic",
        "Chronic Kidney Disease (CKD): documented kidney damage (structural "
        "or functional, e.g. proteinuria/albuminuria, imaging or biopsy "
        "abnormality) or an estimated GFR below 60 mL/min/1.73m2, persisting "
        "for at least 3 months. A single abnormal creatinine or eGFR result "
        "does not establish CKD -- chronicity must be documented from prior "
        "labs, imaging, or clinical history; when chronicity is not "
        "documented, acute kidney injury (AKI) remains a differential and "
        "chronicity evidence is marked missing rather than inferred. "
        "Staged by KDIGO GFR category (G1 >=90, G2 60-89, G3a 45-59, "
        "G3b 30-44, G4 15-29, G5 <15 or on dialysis) and albuminuria "
        "category (A1 ACR <30 mg/g, A2 30-299 mg/g, A3 >=300 mg/g). "
        "Etiologic groupings include pre-renal, intrinsic renal, and "
        "post-renal causes. Progresses, in advanced/G5 disease, to End "
        "Stage Renal Disease (see MAY_PROGRESS_TO relationship). "
        "Aliases (documentation synonyms, not separate diseases): CKD, "
        "Chronic Renal Disease, Chronic Renal Insufficiency, ESRD, ESKD, "
        "End Stage Renal Disease, End-Stage Renal Disease, End Stage "
        "Kidney Disease, CKD Stage 5, CKD G5, Terminal Renal Disease.",
        "Identify expected findings, staging, decline patterns, and "
        "differentiation from acute kidney injury for chronic kidney "
        "disease across all KDIGO stages.",
        "Advanced CKD (G5) approaching or meeting End Stage Renal Disease "
        "criteria supports terminal-prognosis review; see the End Stage "
        "Renal Disease disease record for LCD-specific hospice eligibility "
        "support criteria.",
    ),
    ESRD: (
        "Renal",
        "Kidney",
        "Chronic (CKD G5/ESRD)",
        "End Stage Renal Disease (ESRD): the advanced/end-stage state of "
        "Chronic Kidney Disease corresponding to CKD stage G5 (GFR below "
        "15 mL/min/1.73m2) or established dialysis dependence, whether or "
        "not dialysis is initiated. Represented as the advanced concept "
        "within the Chronic Kidney Disease hierarchy (see MAY_PROGRESS_TO "
        "relationship from Chronic Kidney Disease), not as a separate body "
        "system or family. Aliases (documentation synonyms, not separate "
        "diseases): ESRD, End-Stage Renal Disease, End Stage Kidney "
        "Disease, ESKD, CKD Stage 5, CKD G5, Terminal Renal Disease.",
        "Identify treatment-limitation, end-stage, and hospice-eligibility "
        "relevant indicators for end stage renal disease per LCD Hospice "
        "Eligibility Determination - Kidney Disease (ESRD).",
        "When the patient has been ruled out as a transplant candidate and "
        "is not seeking dialysis (or is on dialysis for comfort only, or is "
        "discontinuing dialysis), and meets creatinine clearance/serum "
        "creatinine/GFR criteria, supports terminal-prognosis review under "
        "LCD Renal Disease (ESRD) criteria. These are review-support "
        "criteria only; they do not automatically determine eligibility, "
        "prognosis, or patient-specific presence -- physician judgment and "
        "patient-specific documentation remain required.",
    ),
}

# ---------------------------------------------------------------------------
# B: SYMPTOMOLOGY
# (symptom_name, description, hospice_relevance, severity_scale)
# ---------------------------------------------------------------------------
SYMPTOMS: Dict[str, List[Tuple[str, str, str, str]]] = {
    CKD: [
        ("Nausea/Vomiting", "Uremic gastrointestinal symptoms from declining renal clearance.",
         "Contributes to nutritional decline assessment.", "Mild to intractable"),
        ("Anorexia/Loss of Appetite", "Reduced appetite from accumulating uremic toxins.",
         "Contributes to nutritional decline assessment.", "Mild to severe"),
        ("Fatigue/Weakness", "Generalized tiredness, often anemia- and uremia-related.",
         "Contributes to functional decline assessment.", "Mild to profound"),
        ("Sleep Disturbance", "Uremic toxin accumulation and restless legs disrupt sleep.",
         "Contributes to overall decline and quality-of-life burden.", "Mild to severe"),
        ("Oliguria", "Reduced urine output as GFR declines.",
         "Supports advancing-stage assessment; a required LCD indicator at end stage.",
         "Mild reduction to anuria"),
        ("Decreased Mental Sharpness", "Uremic-toxin-related cognitive slowing.",
         "May progress to uremic encephalopathy at end stage.", "Mild confusion to coma"),
        ("Muscle Cramps", "Electrolyte-disturbance-related cramping.",
         "Common in advancing CKD.", "Mild to severe"),
        ("Peripheral Edema/Swelling", "Volume retention from impaired excretion.",
         "May progress to intractable fluid overload at end stage.", "Mild to refractory"),
        ("Pruritus", "Uremic itching from toxin accumulation.",
         "Common comfort-focused symptom-management target.", "Mild to severe"),
        ("Chest Discomfort (Uremic Pericarditis)", "Chest discomfort associated with uremic pericardial inflammation.",
         "Uremic pericarditis is a required LCD indicator at end stage.", "Mild to severe"),
        ("Dyspnea (Fluid Overload/Pulmonary Edema)", "Breathlessness from volume overload or pulmonary edema.",
         "Intractable fluid overload is a required LCD indicator at end stage.", "Mild to severe"),
    ],
    ESRD: [
        ("Uremic Malaise/Fatigue", "Profound generalized weakness from accumulated uremic toxins.",
         "Reflects advanced uremic burden.", "Moderate to profound"),
        ("Oliguria/Anuria", "Markedly reduced or absent urine output.",
         "Oliguria is a direct LCD supporting indicator.", "Moderate reduction to anuria"),
        ("Pruritus", "Uremic itching from toxin accumulation, often refractory at end stage.",
         "Common comfort-focused symptom-management target.", "Moderate to severe"),
    ],
}

# ---------------------------------------------------------------------------
# Clinical Findings (Section 3) -- includes CKD staging concepts
# (finding_name, finding_description)
# ---------------------------------------------------------------------------
FINDINGS: Dict[str, List[Tuple[str, str]]] = {
    CKD: [
        ("CKD Stage G1", "GFR 90 mL/min/1.73m2 or greater, with documented evidence of kidney damage."),
        ("CKD Stage G2", "GFR 60-89 mL/min/1.73m2, with documented evidence of kidney damage."),
        ("CKD Stage G3a", "GFR 45-59 mL/min/1.73m2."),
        ("CKD Stage G3b", "GFR 30-44 mL/min/1.73m2."),
        ("CKD Stage G4", "GFR 15-29 mL/min/1.73m2."),
        ("CKD Stage G5", "GFR below 15 mL/min/1.73m2, or treatment by dialysis; corresponds to End Stage Renal Disease."),
        ("Albuminuria Category A1", "Urine albumin-to-creatinine ratio (ACR) below 30 mg/g."),
        ("Albuminuria Category A2", "Urine albumin-to-creatinine ratio (ACR) 30-299 mg/g."),
        ("Albuminuria Category A3", "Urine albumin-to-creatinine ratio (ACR) 300 mg/g or greater."),
        ("Elevated BUN/Creatinine", "Rising nitrogenous waste products from reduced clearance."),
        ("Small/Echogenic Kidneys on Imaging", "Reduced kidney size with increased echogenicity, consistent with chronicity."),
        ("Cortical Thinning", "Thinned renal cortex on imaging, supporting chronic rather than acute disease."),
        ("Renal Scarring", "Structural scarring on imaging or biopsy, supporting chronicity."),
        ("Anemia", "Reduced erythropoietin production from declining renal mass."),
    ],
    ESRD: [
        ("Chronically Elevated Creatinine/BUN at End Stage", "Sustained, markedly elevated nitrogenous waste products."),
        ("Pericardial Friction Rub", "Sign of uremic pericarditis."),
        ("Asterixis", "Flapping tremor of uremic encephalopathy."),
    ],
}

# ---------------------------------------------------------------------------
# Labs (Section 4)
# (lab_name, normal_range, expected_abnormal_range, clinical_significance, hospice_significance)
# ---------------------------------------------------------------------------
LABS: Dict[str, List[Tuple[str, str, str, str, str]]] = {
    CKD: [
        ("Estimated GFR (eGFR)", ">=90 mL/min/1.73m2", "<60 mL/min/1.73m2 (staging G1-G5)",
         "Primary marker of chronic kidney function and staging.",
         "Sustained decline below 60 for 3+ months establishes CKD chronicity."),
        ("Serum Creatinine", "0.6-1.3 mg/dL", "Progressively rising with declining GFR",
         "Reflects glomerular filtration.", "Serial trend supports chronicity and staging."),
        ("Creatinine Clearance", ">=90 cc/min", "Progressively declining with CKD stage",
         "Reflects kidney filtration capacity.", "Supports staging and end-stage assessment."),
        ("Urine Albumin-to-Creatinine Ratio (ACR)", "<30 mg/g", ">=30 mg/g (A2/A3)",
         "Reflects albuminuria category.", "Higher albuminuria category worsens prognosis."),
        ("Urine Protein (Proteinuria)", "Trace or negative", "Elevated, quantifiable on 24-hr collection",
         "Reflects glomerular damage.", "Progressive proteinuria supports prognostic decline."),
    ],
    ESRD: [
        ("Serum Creatinine", "0.6-1.3 mg/dL", ">8.0 mg/dL (>6.0 mg/dL diabetic)",
         "Reflects glomerular filtration at end stage.", "LCD Renal Disease serum-creatinine threshold."),
        ("Estimated GFR (eGFR)", ">=90 mL/min/1.73m2", "<10 mL/min (<15 diabetic w/ CHF)",
         "Reflects overall kidney function at end stage.", "LCD Renal Disease GFR threshold."),
        ("Potassium", "3.5-5.0 mEq/L", ">7.0 mEq/L", "Risk of cardiac arrhythmia.",
         "Intractable hyperkalemia is a direct LCD supporting indicator."),
    ],
}

# ---------------------------------------------------------------------------
# Diagnostic Tests (Section 5)
# (test_name, purpose, expected_findings, evidence_weight)
# ---------------------------------------------------------------------------
DIAGNOSTICS: Dict[str, List[Tuple[str, str, str, str]]] = {
    CKD: [
        ("Renal Ultrasound", "Assess kidney size, echogenicity, cortical thickness, scarring, cystic disease, and obstruction.",
         "Small, echogenic kidneys with cortical thinning support chronicity; may show cysts or obstruction by etiology.",
         "moderate"),
        ("24-Hour Urine Protein", "Quantify proteinuria/albuminuria category.",
         "Elevated protein excretion in progressive CKD.", "moderate"),
        ("Basic Metabolic Panel", "Assess electrolytes, BUN, creatinine trend.",
         "Progressively rising creatinine/BUN, declining eGFR.", "high"),
        ("Urinalysis with Sediment", "Assess for casts, proteinuria, hematuria, urine sediment.",
         "Variable findings by etiology; supports differentiation of intrinsic renal causes.", "moderate"),
        ("Renal Biopsy (when documented)", "Histologic confirmation of chronic structural kidney damage.",
         "Chronic scarring/fibrosis when performed and documented.", "high"),
    ],
}

# ---------------------------------------------------------------------------
# Complications (Section 6)
# (complication_name, description, common_occurrence, clinical_significance)
# ---------------------------------------------------------------------------
COMPLICATIONS: Dict[str, List[Tuple[str, str, str, str]]] = {
    CKD: [
        ("Hypertension", "Volume- and renin-mediated blood pressure elevation.", "common",
         "Accelerates CKD progression; a key prognostic factor."),
        ("Fluid Overload", "Volume retention from impaired excretion.", "common", "Contributes to overall decline."),
        ("Pulmonary Edema", "Fluid accumulation in the lungs from volume overload.", "uncommon",
         "Reflects advancing cardiorenal burden."),
        ("Hyperkalemia", "Elevated serum potassium from reduced excretion.", "common",
         "Risk of fatal arrhythmia."),
        ("Metabolic Acidosis", "Impaired renal acid excretion.", "common", "Contributes to overall decline."),
        ("Hyperphosphatemia", "Impaired phosphate excretion.", "common", "Contributes to mineral bone disease."),
        ("Secondary Hyperparathyroidism", "Compensatory PTH elevation from phosphate/calcium/vitamin-D dysregulation.",
         "common", "Contributes to CKD mineral and bone disorder."),
        ("CKD Mineral and Bone Disorder", "Disordered calcium/phosphate/PTH/vitamin-D metabolism affecting bone and vessels.",
         "common", "Contributes to functional decline and fracture risk."),
        ("Anemia of CKD", "Reduced erythropoietin production.", "common", "Contributes to fatigue and functional decline."),
        ("Uremia", "Accumulation of nitrogenous waste products from reduced clearance.", "common",
         "Core marker of declining renal function; progresses toward end-stage burden."),
        ("Uremic Pericarditis", "Pericardial inflammation from uremic toxins.", "uncommon",
         "Direct LCD supporting indicator at end stage; risk of tamponade."),
        ("Uremic Encephalopathy", "Altered mental status from uremic toxin accumulation.", "uncommon",
         "Reflects advanced uremic burden."),
        ("Uremic Neuropathy", "Peripheral nerve dysfunction from chronic uremic toxin exposure.", "uncommon",
         "Contributes to functional decline (weakness, sensory changes)."),
        ("Uremic Bleeding Dysfunction", "Platelet dysfunction from uremic toxin accumulation.", "uncommon",
         "Increases bleeding risk; supports overall decline picture."),
        ("Malnutrition", "Protein-energy wasting from chronic uremia and dietary restriction.", "common",
         "Recognized CKD/ESRD prognostic marker."),
        ("Cardiovascular Burden", "Accelerated cardiovascular disease risk from CKD-related vascular and metabolic changes.",
         "common", "Comorbid condition supporting terminal-prognosis review."),
    ],
    ESRD: [
        ("Uremia", "Accumulation of nitrogenous waste products at end-stage severity.", "common",
         "Core end-stage marker; target of MAY_CAUSE relationship from End Stage Renal Disease."),
        ("Intractable Hyperkalemia", "Elevated serum potassium refractory to treatment.", "common",
         "Direct LCD supporting indicator; target of MAY_CAUSE relationship."),
        ("Uremic Pericarditis", "Pericardial inflammation from uremic toxins.", "uncommon",
         "Direct LCD supporting indicator; target of MAY_CAUSE relationship; risk of tamponade."),
        ("Hepatorenal Syndrome", "Renal failure in the setting of advanced liver disease.", "uncommon",
         "Direct LCD supporting indicator."),
        ("Intractable Fluid Overload", "Volume overload unresponsive to diuretic/dialysis treatment.", "common",
         "Direct LCD supporting indicator; target of MAY_CAUSE relationship."),
        ("Refractory Metabolic Abnormalities", "Electrolyte/acid-base disturbances unresponsive to treatment.",
         "common", "Reflects loss of homeostatic regulation at end stage."),
    ],
}

# ---------------------------------------------------------------------------
# Prognostic Indicators (Section 9 / D)
# (indicator_name, description, supporting_evidence)
# ---------------------------------------------------------------------------
PROGNOSTIC_INDICATORS: Dict[str, List[Tuple[str, str, str]]] = {
    CKD: [
        ("Progressive GFR Decline", "Sustained downward trend in kidney function across stages.",
         "Serial eGFR/creatinine-clearance trend."),
        ("Increasing Albuminuria/Proteinuria", "Worsening albuminuria category (A1->A2->A3) or proteinuria.",
         "Serial urine ACR/24-hr protein trend."),
        ("Documented Comorbid Diabetes", "Diabetic nephropathy accelerates decline, when documented.",
         "HbA1c and renal function trend."),
        ("Documented Comorbid Hypertension", "Poorly controlled hypertension accelerates decline, when documented.",
         "Blood pressure trend and antihypertensive regimen."),
        ("Documented Comorbid Cardiovascular Disease", "Concurrent cardiovascular disease worsens prognosis, when documented.",
         "Cardiology records."),
        ("Recurrent Hospitalization", "Frequent admissions for volume/electrolyte management.",
         "Hospitalization history."),
        ("Progressive Uremic Symptoms", "Worsening uremic symptom burden over time.", "Serial symptom assessment."),
        ("Refractory Electrolyte Abnormalities", "Persistent hyperkalemia/acidosis despite treatment.",
         "Laboratory trend plus treatment response."),
        ("Declining Functional Status", "Progressive ADL dependence.", "Functional/PPS assessment."),
        ("Nutritional Decline", "Progressive weight loss/malnutrition markers.", "Weight and albumin trend."),
        ("Hypoalbuminemia", "Serum albumin <2.5 g/dL, when documented.", "Laboratory trend."),
        ("Documented Comorbid Dementia or Peripheral Vascular Disease", "Concurrent dementia/PVD worsens prognosis, when documented.",
         "Diagnosis history."),
    ],
}

# ---------------------------------------------------------------------------
# Hospice Eligibility Support (Section 9B / I) -- LCD-sourced only
# (indicator_name, description, supporting_evidence, lcd_reference)
# ---------------------------------------------------------------------------
HOSPICE_ELIGIBILITY_SUPPORT: Dict[str, List[Tuple[str, str, str, str]]] = {
    ESRD: [
        ("Not Seeking Dialysis or Renal Transplant",
         "Patient ruled out as a transplant candidate and not seeking dialysis, or on dialysis for comfort "
         "only with unaltered prognosis.",
         "Documented goals-of-care discussion (LCD criterion 1a/1b).", "LCD Renal Disease (ESRD.pdf)"),
        ("Dialysis Discontinued", "Renal replacement therapy stopped after initiation.",
         "Documented discontinuation order and goals-of-care discussion.", "LCD Renal Disease (ESRD.pdf)"),
        ("GFR or Creatinine Clearance Below 15 mL/min", "Severely reduced clearance/filtration rate.",
         "Laboratory result (LCD criteria 2a/4a).", "LCD Renal Disease (ESRD.pdf)"),
        ("Serum Creatinine Above 8.0 mg/dL", "Markedly elevated creatinine.",
         "Laboratory result (LCD criterion 3a).", "LCD Renal Disease (ESRD.pdf)"),
        ("Serum Creatinine Above 6.0 mg/dL (Diabetic)", "Markedly elevated creatinine in a patient with diabetes.",
         "Laboratory result (LCD criterion 3a diabetic threshold).", "LCD Renal Disease (ESRD.pdf)"),
        ("Uremia", "Documented uremic toxin accumulation.",
         "Clinical and laboratory correlation.", "LCD Renal Disease (ESRD.pdf)"),
        ("Oliguria", "Markedly reduced urine output.", "Intake/output records.", "LCD Renal Disease (ESRD.pdf)"),
        ("Intractable Hyperkalemia Above 7.0 Not Responsive to Treatment", "Refractory elevated potassium.",
         "Laboratory result plus treatment response (LCD criterion 5a).", "LCD Renal Disease (ESRD.pdf)"),
        ("Uremic Pericarditis", "Pericardial inflammation from uremic toxins.",
         "Clinical exam/echo (LCD criterion 5).", "LCD Renal Disease (ESRD.pdf)"),
        ("Hepatorenal Syndrome", "Renal failure in the setting of advanced liver disease.",
         "Clinical and laboratory correlation (LCD criterion 5f).", "LCD Renal Disease (ESRD.pdf)"),
        ("Intractable Fluid Overload Not Responsive to Treatment", "Volume overload unresponsive to treatment.",
         "Clinical exam and treatment response (LCD criterion 5).", "LCD Renal Disease (ESRD.pdf)"),
        ("KPS or PPS Below 70 (When Documented)", "Documented functional performance score below 70.",
         "KPS/PPS assessment, when documented.", "LCD Renal Disease (ESRD.pdf)"),
        ("Dependence in Two or More ADLs (When Documented)", "Documented dependence in two or more activities of daily living.",
         "Functional/ADL assessment, when documented.", "LCD Renal Disease (ESRD.pdf)"),
        ("Relevant Documented Comorbidities", "Mechanical ventilation, autoimmune disease, cancer, digestive disease, "
         "heart disease, liver disease, or pulmonary disease present.",
         "Diagnosis history (LCD criteria 5a-5g).", "LCD Renal Disease (ESRD.pdf)"),
    ],
}

# ---------------------------------------------------------------------------
# Functional Impact (Section 7 / F)
# (impact_name, description, severity)
# ---------------------------------------------------------------------------
FUNCTIONAL_IMPACTS: Dict[str, List[Tuple[str, str, str]]] = {
    CKD: [
        ("Weakness", "Uremia- and anemia-related weakness.", "mild to severe"),
        ("Activity Intolerance", "Reduced exercise/activity tolerance from fatigue and volume status.", "mild to severe"),
        ("Mobility Decline", "Progressive reduction in ambulation ability.", "mild to severe"),
        ("Increasing ADL Dependence", "Progressive dependence in feeding, ambulation, continence, transfer, "
         "bathing, and dressing.", "mild to severe"),
        ("Cognitive/Mental-Status Decline (Uremia-Related)", "Uremic-toxin-related cognitive slowing or confusion.",
         "mild to severe"),
    ],
    ESRD: [
        ("Advanced ADL Dependence", "Complete or near-complete dependence in feeding, ambulation, continence, "
         "transfer, bathing, and dressing.", "severe"),
        ("Advanced Cognitive/Mental-Status Decline", "Severe uremic encephalopathy-related cognitive impairment.",
         "severe"),
    ],
}

# ---------------------------------------------------------------------------
# Nutritional Impact (Section 8 / G)
# (impact_name, description, clinical_significance)
# ---------------------------------------------------------------------------
NUTRITIONAL_IMPACTS: Dict[str, List[Tuple[str, str, str]]] = {
    CKD: [
        ("Anorexia/Poor Intake", "Reduced appetite and oral intake from uremic toxin burden.",
         "Contributes to overall decline."),
        ("Persistent Nausea and Vomiting", "Uremic gastrointestinal symptoms limiting intake.",
         "Contributes to weight and nutritional decline."),
        ("Unintentional Weight Loss", "Weight loss not explained by fluid status.",
         "Recognized CKD prognostic marker."),
        ("Protein-Calorie Malnutrition", "Chronic uremia-related catabolic state.",
         "Recognized CKD/ESRD prognostic marker."),
        ("Muscle Wasting", "Loss of lean muscle mass from chronic catabolism.", "Contributes to functional decline."),
        ("Low Albumin (When Documented)", "Serum albumin below normal, when documented.",
         "Recognized prognostic marker."),
        ("Dietary-Management Burden", "Burden of fluid/protein/phosphate/potassium dietary restrictions.",
         "Risk factor for decline and caregiver burden."),
    ],
    ESRD: [
        ("Advanced Protein-Energy Wasting", "Severe uremia-related catabolic state at end stage.",
         "Core end-stage nutritional prognostic marker."),
        ("Severe Anorexia", "Marked reduction or absence of appetite at end stage.",
         "Contributes to overall decline."),
    ],
}

# ---------------------------------------------------------------------------
# Treatments (Section 10)
# (treatment_name, treatment_category, description)
# ---------------------------------------------------------------------------
TREATMENTS: Dict[str, List[Tuple[str, str, str]]] = {
    CKD: [
        ("ACE Inhibitor/ARB Therapy", "DISEASE_DIRECTED", "Blood-pressure control and proteinuria reduction to slow progression."),
        ("Conservative Kidney Management", "SUPPORTIVE", "Non-dialysis medical management of CKD complications."),
        ("Dietary/Fluid Management", "SUPPORTIVE", "Protein/phosphate/potassium/fluid restriction as indicated by stage."),
        ("Comfort-Focused Symptom Management", "HOSPICE", "Symptom-focused care when disease-directed treatment is limited."),
    ],
    ESRD: [
        ("Hemodialysis/Peritoneal Dialysis", "DISEASE_DIRECTED", "Renal replacement therapy for ESRD."),
        ("Comfort-Focused Symptom Management", "HOSPICE",
         "Symptom-focused care when dialysis is declined or discontinued."),
    ],
}

# ---------------------------------------------------------------------------
# Medications (Section 11)
# (medication_name, drug_class, purpose, expected_benefits, common_side_effects, hospice_relevance)
# ---------------------------------------------------------------------------
MEDICATIONS: Dict[str, List[Tuple[str, str, str, str, str, str]]] = {
    CKD: [
        ("ACE Inhibitors/ARBs", "Antihypertensive/renoprotective", "Slow CKD progression, reduce proteinuria.",
         "Reduced blood pressure and albuminuria.", "Hyperkalemia, acute kidney injury risk.",
         "May be discontinued at end stage."),
        ("Erythropoiesis-Stimulating Agents", "ESA", "Manage anemia of CKD.", "Improved hemoglobin/energy.",
         "Hypertension, thrombosis risk.", "Improves fatigue-related decline."),
        ("Phosphate Binders", "Phosphate binder", "Manage hyperphosphatemia.", "Lowered serum phosphate.",
         "Constipation, GI upset.", "Symptom management."),
    ],
    ESRD: [
        ("Loop Diuretics", "Diuretic", "Manage volume overload.", "Reduced edema/fluid overload.",
         "Electrolyte disturbance, ototoxicity.", "Comfort-focused fluid management."),
        ("Potassium Binders", "Potassium-lowering agent", "Manage hyperkalemia.", "Lowered serum potassium.",
         "GI upset.", "Reduces arrhythmia risk."),
    ],
}

# ---------------------------------------------------------------------------
# Psychosocial Concerns (Section 12)
# (concern_name, description)
# ---------------------------------------------------------------------------
PSYCHOSOCIAL_CONCERNS: Dict[str, List[Tuple[str, str]]] = {
    CKD: [
        ("Chronic Illness Burden", "Psychosocial strain of managing a progressive chronic disease and dietary restrictions."),
    ],
    ESRD: [
        ("Family Conflict Regarding Dialysis-Withdrawal Decision", "Disagreement among family about "
         "discontinuing or declining dialysis."),
        ("Anxiety About Dialysis Dependence/Discontinuation", "Distress around ongoing or withdrawn renal "
         "replacement therapy."),
    ],
}

# ---------------------------------------------------------------------------
# Spiritual Concerns (Section 13)
# (concern_name, description)
# ---------------------------------------------------------------------------
SPIRITUAL_CONCERNS: Dict[str, List[Tuple[str, str]]] = {
    CKD: [
        ("Meaning-Making Around Chronic Illness and Mortality",
         "Spiritual reflection prompted by progressive, irreversible decline."),
    ],
    ESRD: [
        ("Existential Distress Around Forgoing/Discontinuing Dialysis",
         "Spiritual/meaning-related distress tied to end-of-life treatment decisions."),
    ],
}

# ---------------------------------------------------------------------------
# Interdisciplinary Triggers (Section 14)
# (discipline, trigger_condition)
# ---------------------------------------------------------------------------
INTERDISCIPLINARY_TRIGGERS: Dict[str, List[Tuple[str, str]]] = {
    CKD: [
        ("RN", "Decline monitoring and stage-progression care coordination."),
        ("DIETICIAN", "Nutrition/fluid-restriction management support."),
    ],
    ESRD: [
        ("RN", "Dialysis-withdrawal care coordination and end-stage symptom monitoring."),
        ("MSW", "Psychosocial support for family conflict or treatment-decision distress."),
        ("CHAPLAIN", "Spiritual support for dialysis withdrawal and end-of-life meaning-making."),
    ],
}

# ---------------------------------------------------------------------------
# E: TREATMENT LIMITATIONS (End Stage Renal Disease only)
# (limitation_name, limitation_category, description, evidence_requirement, hospice_relevance)
# ---------------------------------------------------------------------------
TREATMENT_LIMITATIONS: Dict[str, List[Tuple[str, str, str, str, str]]] = {
    ESRD: [
        ("Dialysis Declined", "TREATMENT_DECLINED",
         "Patient/family declines initiation of renal replacement therapy.",
         "Documented goals-of-care discussion.",
         "Supports terminal-prognosis review under LCD Renal Disease (criterion 1a)."),
        ("Dialysis Discontinued", "TREATMENT_DISCONTINUED",
         "Renal replacement therapy stopped after initiation.",
         "Documented discontinuation order and goals-of-care discussion.",
         "Supports terminal-prognosis review under LCD Renal Disease (criterion 1b)."),
        ("Dialysis Not Tolerated", "TREATMENT_INTOLERANT",
         "Patient unable to tolerate dialysis sessions (hemodynamic instability, access complications, etc).",
         "Nephrology/dialysis-unit documentation.",
         "Supports terminal-prognosis review."),
        ("Dialysis Contraindicated", "TREATMENT_CONTRAINDICATED",
         "Dialysis medically contraindicated for this patient.",
         "Physician assessment documented in the record.",
         "Supports terminal-prognosis review."),
        ("Renal Transplant Not Pursued", "TREATMENT_DECLINED",
         "Patient/family elects not to pursue evaluation or listing for renal transplant.",
         "Documented goals-of-care discussion.",
         "Supports terminal-prognosis review under LCD Renal Disease (criterion 1a)."),
        ("Not A Transplant Candidate", "NOT_A_CANDIDATE",
         "Patient ruled out as a candidate for renal transplant.",
         "Nephrology/transplant-team assessment documented in the record.",
         "Supports terminal-prognosis review under LCD Renal Disease (criterion 1a)."),
        ("Conservative Kidney Management Selected", "COMFORT_FOCUSED",
         "Care goals shifted to conservative, non-dialysis, comfort-focused kidney management.",
         "Care plan/goals-of-care documentation.",
         "Core hospice transition marker."),
    ],
}

# ---------------------------------------------------------------------------
# H: END-STAGE FINDINGS (End Stage Renal Disease only)
# (finding_name, description, evidence_requirement, clinical_significance, hospice_relevance)
# ---------------------------------------------------------------------------
END_STAGE_FINDINGS: Dict[str, List[Tuple[str, str, str, str, str]]] = {
    ESRD: [
        ("CKD G5/ESRD (GFR Below 15)", "GFR below 15 mL/min/1.73m2, meeting the end-stage CKD/ESRD threshold.",
         "Laboratory/calculated GFR result.", "Defines the end-stage renal function threshold.",
         "Core end-stage indicator supporting LCD Renal Disease review."),
        ("Dialysis Dependence", "Sustained requirement for renal replacement therapy to sustain life.",
         "Dialysis/nephrology records.", "Reflects complete loss of native renal function.",
         "End-stage indicator supporting LCD Renal Disease review."),
        ("Anuria", "Complete absence of urine output.",
         "Intake/output records over sustained period.",
         "Reflects total loss of residual renal function.",
         "End-stage indicator supporting LCD Renal Disease review."),
        ("Uremic Encephalopathy", "Severe altered consciousness from uremic toxin accumulation.",
         "Clinical exam and laboratory correlation.",
         "Reflects advanced uremic burden.",
         "End-stage indicator supporting LCD Renal Disease review."),
        ("Refractory Fluid Overload", "Volume overload unresponsive to maximal diuretic/dialysis therapy.",
         "Clinical exam and treatment-response documentation.",
         "Reflects loss of volume-regulation capacity.",
         "End-stage indicator supporting LCD Renal Disease review."),
        ("Refractory Metabolic Abnormalities", "Electrolyte/acid-base disturbances unresponsive to treatment.",
         "Laboratory trend plus treatment-response documentation.",
         "Reflects loss of homeostatic regulation.",
         "End-stage indicator supporting LCD Renal Disease review."),
        ("Advanced Functional Decline", "Profound, near-total functional dependence at end stage.",
         "Functional/PPS assessment.", "Reflects end-stage functional status.",
         "Supports overall terminal-prognosis picture."),
        ("Advanced Nutritional Decline", "Profound protein-energy wasting/malnutrition at end stage.",
         "Weight and laboratory (albumin) trend.", "Reflects end-stage nutritional status.",
         "Supports overall terminal-prognosis picture."),
    ],
}

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
# (source_disease_name, relationship_type, target_disease_name_or_None,
#  target_concept_type_or_None, target_concept_lookup)
# Only relationships whose source AND target concepts already exist (or are
# created by this script) are added -- referencing an unrelated disease not
# present in the ontology (e.g. Diabetes, Hypertension, a generic
# "Cardiovascular Disease") is skipped rather than creating an orphan edge.
# ---------------------------------------------------------------------------
DISEASE_TO_DISEASE_RELATIONSHIPS: List[Tuple[str, str, str]] = [
    (CKD, "MAY_PROGRESS_TO", ESRD),
    ("Chronic Systolic Heart Failure", "MAY_CONTRIBUTE_TO", CKD),
]

# (source_disease_name, relationship_type, target_concept_type, target_disease_name, target_concept_name)
DISEASE_TO_CONCEPT_RELATIONSHIPS: List[Tuple[str, str, str, str, str]] = [
    (ESRD, "MAY_CAUSE", "COMPLICATION", ESRD, "Uremia"),
    (ESRD, "MAY_CAUSE", "SYMPTOM", ESRD, "Oliguria/Anuria"),
    (ESRD, "MAY_CAUSE", "COMPLICATION", ESRD, "Intractable Hyperkalemia"),
    (ESRD, "MAY_CAUSE", "COMPLICATION", ESRD, "Uremic Pericarditis"),
    (ESRD, "MAY_CAUSE", "COMPLICATION", ESRD, "Intractable Fluid Overload"),
]

# Diseases referenced by the requested relationship set that do not exist
# anywhere in the ontology and are therefore intentionally NOT linked (no
# orphan edges created): Diabetes, Hypertension, generic "Cardiovascular
# Disease" (only specific cardiovascular diseases exist: Chronic Systolic
# Heart Failure, Coronary Artery Disease, Prior Myocardial Infarction,
# Atrial Fibrillation).
SKIPPED_RELATIONSHIPS_MISSING_TARGET = [
    ("Diabetes", "MAY_CONTRIBUTE_TO", CKD),
    ("Hypertension", "MAY_CONTRIBUTE_TO", CKD),
    (CKD, "INCREASES_RISK_OF", "Cardiovascular Disease"),
]


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
    inserted = 0
    for disease_name, rows in TREATMENTS.items():
        disease = diseases[disease_name]
        existing_rows = existing_rows_by_canonical_name(
            db.query(OntologyDiseaseTreatment).filter_by(disease_id=disease.id).all(),
            domain="TREATMENT",
            table_name=OntologyDiseaseTreatment.__tablename__,
            disease_id=disease.id,
            importer_name=IMPORTER_NAME,
            name_attr="treatment_name",
            category_attr="treatment_category",
        )
        for name, category, desc in rows:
            normalized_name = concept_identity_key("TREATMENT", name)
            existing = existing_rows.get(normalized_name)
            if existing is not None:
                result = reconcile_category(
                    domain="TREATMENT",
                    disease_id=existing.disease_id,
                    normalized_name=existing.normalized_name,
                    existing_row_id=existing.id,
                    existing_display_name=existing.treatment_name,
                    existing_category=existing.treatment_category,
                    incoming_display_name=name,
                    incoming_category=category,
                    importer_name=IMPORTER_NAME,
                )
                if result.changed:
                    existing.treatment_category = result.category
                continue
            row = OntologyDiseaseTreatment(
                id=uuid.uuid4(),
                disease_id=disease.id,
                treatment_name=name,
                normalized_name=normalized_name,
                treatment_category=category,
                description=desc,
            )
            db.add(row)
            db.flush()
            existing_rows[normalized_name] = row
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
        existing_rows = existing_rows_by_canonical_name(
            db.query(OntologyDiseaseTreatmentLimitation).filter_by(disease_id=disease.id).all(),
            domain="TREATMENT_LIMITATION",
            table_name=OntologyDiseaseTreatmentLimitation.__tablename__,
            disease_id=disease.id,
            importer_name=IMPORTER_NAME,
            name_attr="limitation_name",
            category_attr="limitation_category",
        )
        for name, category, desc, evidence_req, hospice_rel in rows:
            normalized_name = concept_identity_key("TREATMENT_LIMITATION", name)
            existing = existing_rows.get(normalized_name)
            if existing is not None:
                result = reconcile_category(
                    domain="TREATMENT_LIMITATION",
                    disease_id=existing.disease_id,
                    normalized_name=existing.normalized_name,
                    existing_row_id=existing.id,
                    existing_display_name=existing.limitation_name,
                    existing_category=existing.limitation_category,
                    incoming_display_name=name,
                    incoming_category=category,
                    importer_name=IMPORTER_NAME,
                )
                if result.changed:
                    existing.limitation_category = result.category
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


def populate_evidence_rules(db, diseases) -> int:
    """J: one active evidence rule per active concept row, for every concept
    domain in CONCEPT_DOMAINS, for Chronic Kidney Disease and End Stage
    Renal Disease only. Hospice-eligibility-support concepts always cite
    the LCD regardless of source disease; all other concept types cite the
    general CKD clinical-knowledge source."""
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
                source_label = LCD_SOURCE
            else:
                source_label = EVIDENCE_SOURCE_BY_DISEASE_NAME.get(disease_name, CKD_SOURCE)
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
    """Add only supported, non-duplicative cross-disease/concept
    relationships using existing OntologyRelationship rows. Skips any
    relationship whose source or target concept does not exist in the
    ontology (see SKIPPED_RELATIONSHIPS_MISSING_TARGET)."""
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
    """Run the full A-K population for the Renal System (CKD + ESRD)
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
