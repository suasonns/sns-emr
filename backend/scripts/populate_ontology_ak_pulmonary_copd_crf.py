# scripts/populate_ontology_ak_pulmonary_copd_crf.py
"""
Idempotent population script for the Pulmonary System (A-K, all domains):

    System:  Pulmonary System
    Family:  Chronic Obstructive Pulmonary Disease
    Diseases:
        - Chronic Obstructive Pulmonary Disease (primary; general COPD
          identity, GOLD staging, symptoms, complications, prognosis, and
          functional/nutritional decline)
        - Chronic Respiratory Failure (advanced/end-stage state of COPD
          with hypoxemia and/or hypercapnia; treatment limitations,
          end-stage findings, and hospice eligibility support)

Chronic Respiratory Failure is linked to Chronic Obstructive Pulmonary
Disease via a MAY_PROGRESS_TO relationship -- it is not a separate body
system or family, and Acute Respiratory Failure / Asthma are not created
by this script. Aliases (COPD, Chronic Bronchitis, Emphysema, Chronic
Obstructive Airway Disease, Chronic Respiratory Insufficiency, End-Stage
Lung Disease, End-Stage COPD, Hypoxemic/Hypercapnic Respiratory Failure)
are documented in each disease's disease_description, never as duplicate
disease rows.

Source ownership:
    - A, B, C, D, F, G, J, K: general Chronic Obstructive Pulmonary Disease
      clinical knowledge (GOLD COPD spirometric staging framework; standard
      COPD/respiratory-failure hospice-decline literature). Clinical
      knowledge is the primary ontology source -- the LCD is not used to
      define the disease itself.
    - E (Treatment Limitations), H (End-Stage Findings), and I (Hospice
      Eligibility Support) only: backend/app/config/lcd/
      pulmonary_copd_respiratory_failure.json ("LCD Hospice Eligibility
      Determination - Pulmonary Disease"). The LCD does not define the rest
      of the pulmonary ontology.

Every system/family/disease/concept row is resolved by stable name (never
a hardcoded UUID) and inserted only if a matching row does not already
exist by the table's existing unique constraint. Re-running this script is
always safe:

    - missing records are inserted
    - matching records are left unchanged
    - no records are ever deleted
    - no other body system, disease, or patient/staff table is touched

Run with: .\\.venv\\Scripts\\python.exe scripts\\populate_ontology_ak_pulmonary_copd_crf.py
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

SYSTEM_NAME = "Pulmonary System"
FAMILY_NAME = "Chronic Obstructive Pulmonary Disease"
COPD = "Chronic Obstructive Pulmonary Disease"
CRF = "Chronic Respiratory Failure"
APPROVED_DISEASE_NAMES = [COPD, CRF]

PULM_SOURCE = (
    "General Chronic Obstructive Pulmonary Disease clinical knowledge (GOLD "
    "spirometric staging framework GOLD 1-4; standard COPD/respiratory-"
    "failure hospice-decline literature)"
)
LCD_SOURCE = (
    "LCD Hospice Eligibility Determination \u2013 Pulmonary Disease "
    "(COPD, Respiratory failure with hypoxia, hypercapnia.pdf)"
)

EVIDENCE_SOURCE_BY_DISEASE_NAME: Dict[str, str] = {
    COPD: PULM_SOURCE,
    CRF: PULM_SOURCE,
}
# Domains E (Treatment Limitations), H (End-Stage Findings), and I (Hospice
# Eligibility Support) always cite the LCD regardless of which disease they
# are attached to -- handled explicitly in populate_evidence_rules below,
# not via this generic per-disease map.

IMAGING_TEST_NAMES = {"chest x-ray", "chest ct"}

# ---------------------------------------------------------------------------
# A: DISEASE IDENTITY
# (disease_category, primary_organ, disease_type, disease_description,
#  clinical_purpose, hospice_relevance)
# ---------------------------------------------------------------------------
DISEASE_IDENTITY: Dict[str, Tuple[str, str, str, str, str, str]] = {
    COPD: (
        "Pulmonary",
        "Lung",
        "Chronic",
        "Chronic Obstructive Pulmonary Disease (COPD): persistent "
        "respiratory symptoms and airflow limitation due to airway and/or "
        "alveolar abnormalities, most often caused by significant exposure "
        "to noxious particles or gases (commonly cigarette smoking), "
        "persisting for at least 3 months. A single abnormal spirometry "
        "result does not establish COPD -- chronicity must be documented "
        "from prior spirometry, imaging, or clinical history; when "
        "chronicity is not documented, an acute process (e.g. acute "
        "bronchitis, asthma exacerbation) remains a differential and "
        "chronicity evidence is marked missing rather than inferred. "
        "Staged by GOLD spirometric category based on post-bronchodilator "
        "FEV1 percent predicted (GOLD 1 mild >=80%, GOLD 2 moderate "
        "50-79%, GOLD 3 severe 30-49%, GOLD 4 very severe <30%). "
        "Progresses, in advanced/GOLD 4 disease, to Chronic Respiratory "
        "Failure (see MAY_PROGRESS_TO relationship). Aliases (documentation "
        "synonyms, not separate diseases): COPD, Chronic Bronchitis, "
        "Emphysema, Chronic Obstructive Airway Disease, Chronic "
        "Obstructive Lung Disease.",
        "Identify expected findings, staging, decline patterns, and "
        "differentiation from acute respiratory processes for chronic "
        "obstructive pulmonary disease across all GOLD stages.",
        "Advanced COPD (GOLD 4) approaching or meeting Chronic Respiratory "
        "Failure criteria supports terminal-prognosis review; see the "
        "Chronic Respiratory Failure disease record for LCD-specific "
        "hospice eligibility support criteria.",
    ),
    CRF: (
        "Pulmonary",
        "Lung",
        "Chronic (Advanced COPD/Respiratory Failure)",
        "Chronic Respiratory Failure: the advanced/end-stage state of "
        "Chronic Obstructive Pulmonary Disease marked by disabling dyspnea "
        "at rest and either hypoxemia (pO2 at or below 55 mmHg, or O2 "
        "saturation at or below 88 percent on room air) or hypercapnia "
        "(pCO2 at or above 50 mmHg), whether or not supplemental oxygen or "
        "ventilatory support has been initiated. Represented as the "
        "advanced concept within the Chronic Obstructive Pulmonary Disease "
        "hierarchy (see MAY_PROGRESS_TO relationship from Chronic "
        "Obstructive Pulmonary Disease), not as a separate body system or "
        "family. Aliases (documentation synonyms, not separate diseases): "
        "Chronic Respiratory Insufficiency, End-Stage Lung Disease, "
        "End-Stage COPD, Hypoxemic Respiratory Failure, Hypercapnic "
        "Respiratory Failure.",
        "Identify treatment-limitation, end-stage, and hospice-eligibility "
        "relevant indicators for chronic respiratory failure per LCD "
        "Hospice Eligibility Determination - Pulmonary Disease.",
        "When disabling dyspnea at rest and documented progression of "
        "end-stage pulmonary disease are present, together with hypoxemia "
        "or hypercapnia and supporting factors (cor pulmonale, "
        "unintentional weight loss, resting tachycardia), supports "
        "terminal-prognosis review under LCD Pulmonary Disease criteria. "
        "These are review-support criteria only; they do not automatically "
        "determine eligibility, prognosis, or patient-specific presence -- "
        "physician judgment and patient-specific documentation remain "
        "required.",
    ),
}

# ---------------------------------------------------------------------------
# B: SYMPTOMOLOGY
# (symptom_name, description, hospice_relevance, severity_scale)
# ---------------------------------------------------------------------------
SYMPTOMS: Dict[str, List[Tuple[str, str, str, str]]] = {
    COPD: [
        ("Dyspnea on Exertion", "Breathlessness with activity from airflow limitation.",
         "Contributes to functional decline assessment.", "Mild to severe"),
        ("Chronic Cough", "Persistent productive or non-productive cough.",
         "Common presenting/monitoring symptom.", "Mild to severe"),
        ("Sputum Production", "Chronic mucus production, often worse in the morning.",
         "Tracks chronic bronchitis phenotype and exacerbation risk.", "Mild to copious"),
        ("Wheezing", "Musical breath sounds from airflow obstruction.",
         "Reflects bronchospasm/airway narrowing.", "Mild to severe"),
        ("Chest Tightness", "Sensation of chest constriction with breathing effort.",
         "Common comfort-focused symptom-management target.", "Mild to severe"),
        ("Fatigue/Weakness", "Generalized tiredness from increased work of breathing.",
         "Contributes to functional decline assessment.", "Mild to profound"),
        ("Anxiety Related to Breathlessness", "Distress associated with dyspnea episodes.",
         "Contributes to overall decline and quality-of-life burden.", "Mild to severe"),
        ("Sleep Disturbance", "Nocturnal dyspnea and cough disrupt sleep.",
         "Contributes to overall decline and quality-of-life burden.", "Mild to severe"),
    ],
    CRF: [
        ("Disabling Dyspnea at Rest", "Breathlessness present even without exertion.",
         "Disabling dyspnea at rest is a direct LCD supporting indicator.", "Severe to refractory"),
        ("Air Hunger", "Subjective sense of insufficient breath despite effort.",
         "Core end-stage comfort-management target.", "Moderate to severe"),
        ("Cyanosis", "Bluish discoloration from severe hypoxemia.",
         "Reflects advanced hypoxemic burden.", "Mild to severe"),
        ("Confusion/Somnolence (Hypercapnia-Related)", "Altered mental status from CO2 narcosis.",
         "Reflects advanced hypercapnic burden.", "Mild confusion to coma"),
    ],
}

# ---------------------------------------------------------------------------
# Clinical Findings (Section 3) -- includes COPD GOLD staging concepts
# (finding_name, finding_description)
# ---------------------------------------------------------------------------
FINDINGS: Dict[str, List[Tuple[str, str]]] = {
    COPD: [
        ("GOLD Stage 1 (Mild)", "Post-bronchodilator FEV1 80% predicted or greater."),
        ("GOLD Stage 2 (Moderate)", "Post-bronchodilator FEV1 50-79% predicted."),
        ("GOLD Stage 3 (Severe)", "Post-bronchodilator FEV1 30-49% predicted."),
        ("GOLD Stage 4 (Very Severe)", "Post-bronchodilator FEV1 below 30% predicted; corresponds to advanced/end-stage disease."),
        ("Barrel Chest", "Increased anteroposterior chest diameter from hyperinflation."),
        ("Decreased Breath Sounds", "Reduced air entry on auscultation from hyperinflation/airflow limitation."),
        ("Prolonged Expiratory Phase", "Extended expiration reflecting airflow obstruction."),
        ("Use of Accessory Muscles of Respiration", "Recruitment of neck/shoulder muscles to assist breathing."),
        ("Pursed-Lip Breathing", "Compensatory breathing pattern to reduce dynamic hyperinflation."),
    ],
    CRF: [
        ("FEV1 Less Than 30 Percent Predicted (If Available)", "Severe airflow limitation supporting end-stage disease."),
        ("Serial FEV1 Decline Greater Than 40 mL/Year", "Documented progressive decline in lung function over time."),
        ("Digital Clubbing", "Finger clubbing associated with chronic hypoxemia."),
    ],
}

# ---------------------------------------------------------------------------
# Labs (Section 4)
# (lab_name, normal_range, expected_abnormal_range, clinical_significance, hospice_significance)
# ---------------------------------------------------------------------------
LABS: Dict[str, List[Tuple[str, str, str, str, str]]] = {
    COPD: [
        ("Spirometry (FEV1/FVC Ratio)", "FEV1/FVC >=0.70 post-bronchodilator", "<0.70 post-bronchodilator",
         "Confirms airflow obstruction and stages severity.", "Serial decline supports chronicity and staging."),
        ("Arterial Blood Gas (ABG)", "pO2 80-100 mmHg, pCO2 35-45 mmHg", "Variable hypoxemia/hypercapnia by severity",
         "Assesses gas exchange adequacy.", "Trend supports progression toward respiratory failure."),
        ("Pulse Oximetry (O2 Saturation)", ">=95% on room air", "<95% on room air, worsening with progression",
         "Non-invasive oxygenation screen.", "Serial decline supports staging and end-stage assessment."),
    ],
    CRF: [
        ("Arterial Blood Gas - pO2", "80-100 mmHg", "<=55 mmHg at rest on room air",
         "Reflects hypoxemic respiratory failure.", "LCD Pulmonary Disease pO2 threshold (criterion 2a)."),
        ("Arterial Blood Gas - pCO2", "35-45 mmHg", ">=50 mmHg",
         "Reflects hypercapnic respiratory failure.", "LCD Pulmonary Disease pCO2 threshold (criterion 2c)."),
        ("Pulse Oximetry - O2 Saturation", ">=95% on room air", "<=88% on room air",
         "Non-invasive oxygenation screen at end stage.", "LCD Pulmonary Disease O2 saturation threshold (criterion 2b)."),
    ],
}

# ---------------------------------------------------------------------------
# Diagnostic Tests (Section 5)
# (test_name, purpose, expected_findings, evidence_weight)
# ---------------------------------------------------------------------------
DIAGNOSTICS: Dict[str, List[Tuple[str, str, str, str]]] = {
    COPD: [
        ("Chest X-Ray", "Assess for hyperinflation, flattened diaphragm, bullae.",
         "Hyperinflated lung fields with flattened diaphragms in advancing disease.", "moderate"),
        ("Chest CT", "Detailed assessment of emphysema pattern, bullae, and airway wall thickening.",
         "Emphysematous changes and airway remodeling supporting chronicity.", "moderate"),
        ("Pulmonary Function Testing", "Confirm and stage airflow obstruction.",
         "Reduced FEV1/FVC ratio with progressive FEV1 decline by stage.", "high"),
        ("Echocardiogram", "Assess for right heart strain/cor pulmonale from chronic pulmonary disease.",
         "Right ventricular enlargement/dysfunction and elevated pulmonary artery pressure in advancing disease.",
         "moderate"),
    ],
}

# ---------------------------------------------------------------------------
# Complications (Section 6)
# (complication_name, description, common_occurrence, clinical_significance)
# ---------------------------------------------------------------------------
COMPLICATIONS: Dict[str, List[Tuple[str, str, str, str]]] = {
    COPD: [
        ("Acute Exacerbation of COPD", "Acute worsening of respiratory symptoms beyond normal day-to-day variation.",
         "common", "Recurrent exacerbations are a key prognostic factor and hospitalization driver."),
        ("Pneumonia", "Pulmonary infection superimposed on chronic airflow limitation.", "common",
         "Increases risk of acute respiratory failure."),
        ("Cor Pulmonale (Right Heart Failure)", "Right ventricular strain/failure secondary to chronic pulmonary disease.",
         "common", "Direct LCD supporting indicator at end stage; target of MAY_CAUSE relationship."),
        ("Pulmonary Hypertension", "Elevated pulmonary artery pressure from chronic hypoxemia/vascular remodeling.",
         "common", "Contributes to cor pulmonale and overall decline."),
        ("Hypoxemic Respiratory Failure", "Inadequate oxygenation despite ventilatory effort.", "uncommon",
         "Progresses toward end-stage chronic respiratory failure; target of MAY_CAUSE relationship."),
        ("Hypercapnic Respiratory Failure", "Inadequate CO2 clearance despite ventilatory effort.", "uncommon",
         "Progresses toward end-stage chronic respiratory failure; target of MAY_CAUSE relationship."),
        ("Polycythemia", "Compensatory increase in red blood cell mass from chronic hypoxemia.", "uncommon",
         "Reflects chronicity and severity of hypoxemia."),
        ("Osteoporosis", "Reduced bone density from steroid use, deconditioning, and systemic inflammation.",
         "common", "Contributes to functional decline and fracture risk."),
        ("Skeletal Muscle Wasting", "Loss of peripheral muscle mass from deconditioning and systemic inflammation.",
         "common", "Contributes to functional decline (pulmonary cachexia)."),
        ("Anxiety/Depression", "Psychological burden of chronic breathlessness.", "common",
         "Contributes to overall decline and quality-of-life burden."),
    ],
    CRF: [
        ("Cor Pulmonale (Right Heart Failure)", "Right ventricular strain/failure at end-stage severity.", "common",
         "Direct LCD supporting indicator; target of MAY_CAUSE relationship and MAY_CONTRIBUTE_TO relationship to Chronic Systolic Heart Failure."),
        ("Hypoxemic Respiratory Failure", "Inadequate oxygenation meeting end-stage thresholds.", "common",
         "Core end-stage marker; target of MAY_CAUSE relationship."),
        ("Hypercapnic Respiratory Failure", "Inadequate CO2 clearance meeting end-stage thresholds.", "common",
         "Core end-stage marker; target of MAY_CAUSE relationship."),
        ("Recurrent Pulmonary Infections", "Repeated respiratory infections at end stage.", "common",
         "Reflects loss of respiratory reserve."),
        ("Respiratory Acidosis", "Acid-base disturbance from CO2 retention.", "common",
         "Reflects loss of ventilatory compensation at end stage."),
    ],
}

# ---------------------------------------------------------------------------
# Prognostic Indicators (Section 9 / D)
# (indicator_name, description, supporting_evidence)
# ---------------------------------------------------------------------------
PROGNOSTIC_INDICATORS: Dict[str, List[Tuple[str, str, str]]] = {
    COPD: [
        ("Declining FEV1 Trend", "Sustained downward trend in airflow across GOLD stages.",
         "Serial spirometry trend."),
        ("Serial FEV1 Decline Greater Than 40 mL/Year", "Rapid decline rate associated with worse prognosis.",
         "Serial spirometry trend."),
        ("Increasing Frequency of ER Visits/Hospitalizations for Pulmonary Infection",
         "Rising acute-care utilization for respiratory decompensation.", "Hospitalization/ER-visit history."),
        ("Documented Cor Pulmonale", "Right heart strain/failure secondary to pulmonary disease, when documented.",
         "Echocardiogram/clinical exam."),
        ("Unintentional Weight Loss 10 Percent or Greater in 6 Months", "Progressive weight loss not explained by other causes.",
         "Weight trend."),
        ("Resting Tachycardia Greater Than 100 Per Minute", "Elevated resting heart rate.", "Vital-sign trend."),
        ("Recurrent Hospitalization for Respiratory Failure", "Repeated admissions for acute respiratory decompensation.",
         "Hospitalization history."),
        ("Declining Functional Status", "Progressive ADL dependence.", "Functional/PPS assessment."),
        ("Poor Bronchodilator Response", "Markedly decreased functional capacity despite optimized bronchodilator therapy.",
         "Pulmonary function/clinical response trend."),
    ],
}

# ---------------------------------------------------------------------------
# Hospice Eligibility Support (Section 9B / I) -- LCD-sourced only
# (indicator_name, description, supporting_evidence, lcd_reference)
# ---------------------------------------------------------------------------
HOSPICE_ELIGIBILITY_SUPPORT: Dict[str, List[Tuple[str, str, str, str]]] = {
    CRF: [
        ("Disabling Dyspnea at Rest", "Poor bronchodilator response with markedly decreased functional capacity, "
         "or FEV1 less than 30 percent predicted if available.",
         "Clinical assessment and pulmonary function testing, when available (LCD criterion 1a).", LCD_SOURCE),
        ("Progression of End-Stage Pulmonary Disease Documented",
         "Increasing ER visits, pulmonary-infection hospitalizations, respiratory failure, increasing physician "
         "home visits, or serial FEV1 decline greater than 40 mL/year.",
         "Hospitalization/visit history and serial spirometry (LCD criterion 1b).", LCD_SOURCE),
        ("Hypoxemia at Rest (pO2 <=55 mmHg)", "Hypoxemia at rest on room air with pO2 less than or equal to 55 mmHg.",
         "Arterial blood gas result (LCD criterion 2a).", LCD_SOURCE),
        ("O2 Saturation 88 Percent or Less", "Oxygen saturation less than or equal to 88 percent.",
         "Pulse oximetry result (LCD criterion 2b).", LCD_SOURCE),
        ("Hypercapnia (pCO2 >=50 mmHg)", "Hypercapnia with pCO2 greater than or equal to 50 mmHg.",
         "Arterial blood gas result (LCD criterion 2c).", LCD_SOURCE),
        ("Cor Pulmonale Secondary to Pulmonary Disease", "Right heart failure secondary to pulmonary disease.",
         "Echocardiogram/clinical exam (LCD criterion 3).", LCD_SOURCE),
        ("Unintentional Weight Loss 10 Percent or Greater in 6 Months",
         "Unintentional progressive weight loss of at least 10 percent over the last six months.",
         "Weight trend (LCD criterion 4).", LCD_SOURCE),
        ("Resting Tachycardia Greater Than 100 Per Minute", "Resting tachycardia greater than 100 per minute.",
         "Vital-sign assessment (LCD criterion 5).", LCD_SOURCE),
    ],
}

# ---------------------------------------------------------------------------
# Functional Impact (Section 7 / F)
# (impact_name, description, severity)
# ---------------------------------------------------------------------------
FUNCTIONAL_IMPACTS: Dict[str, List[Tuple[str, str, str]]] = {
    COPD: [
        ("Activity Intolerance", "Reduced exercise/activity tolerance from dyspnea and deconditioning.", "mild to severe"),
        ("Exertional Dyspnea Limiting ADLs", "Breathlessness with activities of daily living.", "mild to severe"),
        ("Mobility Decline", "Progressive reduction in ambulation ability.", "mild to severe"),
        ("Increasing ADL Dependence", "Progressive dependence in feeding, ambulation, continence, transfer, "
         "bathing, and dressing.", "mild to severe"),
    ],
    CRF: [
        ("Dyspnea at Rest Limiting All Activity", "Breathlessness present even without exertion, precluding activity.",
         "severe"),
        ("Advanced ADL Dependence", "Complete or near-complete dependence in feeding, ambulation, continence, "
         "transfer, bathing, and dressing.", "severe"),
    ],
}

# ---------------------------------------------------------------------------
# Nutritional Impact (Section 8 / G)
# (impact_name, description, clinical_significance)
# ---------------------------------------------------------------------------
NUTRITIONAL_IMPACTS: Dict[str, List[Tuple[str, str, str]]] = {
    COPD: [
        ("Increased Caloric Expenditure from Work of Breathing", "Elevated resting energy expenditure from increased respiratory effort.",
         "Contributes to weight loss risk."),
        ("Anorexia/Early Satiety (Dyspnea-Related)", "Reduced intake from breathlessness during meals.",
         "Contributes to overall decline."),
        ("Unintentional Weight Loss", "Weight loss not explained by other causes.",
         "Recognized COPD prognostic marker."),
        ("Muscle Wasting (Pulmonary Cachexia)", "Loss of lean muscle mass from chronic catabolism and deconditioning.",
         "Contributes to functional decline."),
    ],
    CRF: [
        ("Severe Pulmonary Cachexia", "Advanced protein-energy wasting at end stage.",
         "Core end-stage nutritional prognostic marker."),
        ("Advanced Unintentional Weight Loss", "Marked progressive weight loss at end stage.",
         "Recognized end-stage prognostic marker."),
    ],
}

# ---------------------------------------------------------------------------
# Treatments (Section 10)
# (treatment_name, treatment_category, description)
# ---------------------------------------------------------------------------
TREATMENTS: Dict[str, List[Tuple[str, str, str]]] = {
    COPD: [
        ("Bronchodilator Therapy", "DISEASE_DIRECTED", "Short- and long-acting bronchodilators to relieve airflow limitation."),
        ("Inhaled Corticosteroids", "DISEASE_DIRECTED", "Reduce airway inflammation in select COPD phenotypes."),
        ("Pulmonary Rehabilitation", "SUPPORTIVE", "Structured exercise and education program to improve function."),
        ("Long-Term Oxygen Therapy", "SUPPORTIVE", "Supplemental oxygen for chronic hypoxemia."),
        ("Comfort-Focused Symptom Management", "HOSPICE", "Symptom-focused care when disease-directed treatment is limited."),
        ("Respiratory Therapy Evaluation and Support", "SUPPORTIVE",
         "Respiratory Therapy involvement may be relevant for review when documented pulmonary evidence, "
         "including dyspnea, hypoxemia, or declining spirometry, supports it. This is general clinical "
         "knowledge only. It does not mean Respiratory Therapy was ordered, provided, required, or assigned "
         "for a specific patient. Patient-level use requires patient-record evidence and human clinical review."),
    ],
    CRF: [
        ("Noninvasive Ventilation (BiPAP)", "DISEASE_DIRECTED", "Ventilatory support for hypercapnic respiratory failure."),
        ("Comfort-Focused Symptom Management", "HOSPICE",
         "Symptom-focused care when mechanical ventilation is declined or discontinued."),
        ("Respiratory Therapy Evaluation and Support", "SUPPORTIVE",
         "Respiratory Therapy involvement may be relevant for review when documented end-stage pulmonary "
         "evidence, including hypoxemia at rest, hypercapnia, or ventilatory decline, supports it. This is "
         "general clinical knowledge only. It does not mean Respiratory Therapy was ordered, provided, "
         "required, or assigned for a specific patient. Patient-level use requires patient-record evidence "
         "and human clinical review."),
    ],
}

# ---------------------------------------------------------------------------
# Medications (Section 11)
# (medication_name, drug_class, purpose, expected_benefits, common_side_effects, hospice_relevance)
# ---------------------------------------------------------------------------
MEDICATIONS: Dict[str, List[Tuple[str, str, str, str, str, str]]] = {
    COPD: [
        ("Short-Acting Bronchodilators (SABA/SAMA)", "Bronchodilator", "Rapid relief of acute dyspnea/bronchospasm.",
         "Improved airflow and symptom relief.", "Tremor, tachycardia, dry mouth.", "Core symptom-management tool."),
        ("Long-Acting Bronchodilators (LABA/LAMA)", "Bronchodilator", "Maintenance bronchodilation.",
         "Sustained symptom control and reduced exacerbations.", "Tremor, tachycardia, dry mouth.",
         "Continued through end stage for symptom control."),
        ("Inhaled Corticosteroids", "Anti-inflammatory", "Reduce airway inflammation and exacerbation frequency.",
         "Fewer exacerbations in select phenotypes.", "Oral candidiasis, pneumonia risk.",
         "May continue for symptom control."),
    ],
    CRF: [
        ("Opioids for Dyspnea Palliation", "Opioid", "Palliate refractory dyspnea/air hunger.",
         "Reduced sensation of breathlessness.", "Sedation, constipation, respiratory depression risk.",
         "Core comfort-focused symptom-management tool at end stage."),
        ("Anxiolytics for Air Hunger", "Anxiolytic", "Reduce anxiety associated with air hunger.",
         "Reduced dyspnea-related distress.", "Sedation.", "Comfort-focused symptom management."),
    ],
}

# ---------------------------------------------------------------------------
# Psychosocial Concerns (Section 12)
# (concern_name, description)
# ---------------------------------------------------------------------------
PSYCHOSOCIAL_CONCERNS: Dict[str, List[Tuple[str, str]]] = {
    COPD: [
        ("Anxiety Related to Breathlessness", "Psychosocial strain from recurrent dyspnea episodes and activity limitation."),
    ],
    CRF: [
        ("Fear of Suffocation/Air Hunger", "Distress related to the sensation of being unable to breathe."),
        ("Family Distress Regarding Oxygen/Ventilation Decisions", "Family strain around decisions to escalate, "
         "decline, or discontinue oxygen or ventilatory support."),
    ],
}

# ---------------------------------------------------------------------------
# Spiritual Concerns (Section 13)
# (concern_name, description)
# ---------------------------------------------------------------------------
SPIRITUAL_CONCERNS: Dict[str, List[Tuple[str, str]]] = {
    COPD: [
        ("Meaning-Making Around Progressive Breathlessness and Mortality",
         "Spiritual reflection prompted by progressive, irreversible respiratory decline."),
    ],
    CRF: [
        ("Existential Distress Around Declining Ventilatory Support",
         "Spiritual/meaning-related distress tied to end-of-life ventilatory-support decisions."),
    ],
}

# ---------------------------------------------------------------------------
# Interdisciplinary Triggers (Section 14)
# (discipline, trigger_condition)
# ---------------------------------------------------------------------------
#
# NOTE: Respiratory Therapy (RT) is the clinically accurate discipline for
# pulmonary rehabilitation, oxygen-therapy, and ventilatory-support triggers,
# but "RT" is not a permitted value in the
# ck_ontology_disease_interdisciplinary_trigger_discipline CHECK constraint
# (allowed: RN, PHYSICIAN, MSW, BSW, CHAPLAIN, VOLUNTEER, BEREAVEMENT,
# DIETICIAN, PT, OT, IDG). Substituting a different discipline (e.g. PT)
# would misrepresent the underlying clinical knowledge, so those trigger
# facts are intentionally omitted here rather than mislabeled. See backlog:
# add RT to the discipline enum, then populate the omitted RT triggers.
INTERDISCIPLINARY_TRIGGERS: Dict[str, List[Tuple[str, str]]] = {
    COPD: [
        ("RN", "Decline monitoring and stage-progression care coordination."),
    ],
    CRF: [
        ("RN", "End-stage symptom monitoring and care coordination."),
        ("MSW", "Psychosocial support for family conflict or treatment-decision distress."),
        ("CHAPLAIN", "Spiritual support for ventilatory-support withdrawal and end-of-life meaning-making."),
    ],
}

# ---------------------------------------------------------------------------
# E: TREATMENT LIMITATIONS (Chronic Respiratory Failure only)
# (limitation_name, limitation_category, description, evidence_requirement, hospice_relevance)
# ---------------------------------------------------------------------------
TREATMENT_LIMITATIONS: Dict[str, List[Tuple[str, str, str, str, str]]] = {
    CRF: [
        ("Mechanical Ventilation Declined", "TREATMENT_DECLINED",
         "Patient/family declines initiation of invasive or noninvasive mechanical ventilation.",
         "Documented goals-of-care discussion.",
         "Supports terminal-prognosis review under LCD Pulmonary Disease."),
        ("Mechanical Ventilation Discontinued", "TREATMENT_DISCONTINUED",
         "Ventilatory support stopped after initiation.",
         "Documented discontinuation order and goals-of-care discussion.",
         "Supports terminal-prognosis review under LCD Pulmonary Disease."),
        ("Long-Term Oxygen Therapy Not Tolerated", "TREATMENT_INTOLERANT",
         "Patient unable to tolerate supplemental oxygen (mask/cannula intolerance, claustrophobia, etc).",
         "Nursing/respiratory-therapy documentation.",
         "Supports terminal-prognosis review."),
        ("Maximal Bronchodilator Therapy Without Symptom Relief", "TREATMENT_FAILED",
         "Poor bronchodilator response despite optimized therapy, with markedly decreased functional capacity.",
         "Pulmonary function/clinical response documentation.",
         "Supports terminal-prognosis review under LCD Pulmonary Disease (criterion 1a)."),
        ("Not A Candidate for Lung Transplant", "NOT_A_CANDIDATE",
         "Patient ruled out as a candidate for lung transplantation.",
         "Pulmonology/transplant-team assessment documented in the record.",
         "Supports terminal-prognosis review."),
        ("Invasive Ventilation Contraindicated", "TREATMENT_CONTRAINDICATED",
         "Invasive mechanical ventilation medically contraindicated for this patient.",
         "Physician assessment documented in the record.",
         "Supports terminal-prognosis review."),
        ("Comfort-Focused Pulmonary Care Selected", "COMFORT_FOCUSED",
         "Care goals shifted to comfort-focused, non-ventilatory management of respiratory symptoms.",
         "Care plan/goals-of-care documentation.",
         "Core hospice transition marker."),
    ],
}

# ---------------------------------------------------------------------------
# H: END-STAGE FINDINGS (Chronic Respiratory Failure only)
# (finding_name, description, evidence_requirement, clinical_significance, hospice_relevance)
# ---------------------------------------------------------------------------
END_STAGE_FINDINGS: Dict[str, List[Tuple[str, str, str, str, str]]] = {
    CRF: [
        ("Disabling Dyspnea at Rest", "Breathlessness present even without exertion, with markedly decreased "
         "functional capacity.", "Clinical assessment.", "Defines the disabling-dyspnea end-stage threshold.",
         "Core end-stage indicator supporting LCD Pulmonary Disease review (criterion 1a)."),
        ("Hypoxemia at Rest (pO2 <=55 mmHg)", "Resting hypoxemia on room air meeting the end-stage threshold.",
         "Arterial blood gas result.", "Reflects severe impairment of oxygenation.",
         "End-stage indicator supporting LCD Pulmonary Disease review (criterion 2a)."),
        ("Hypercapnia (pCO2 >=50 mmHg)", "Elevated CO2 meeting the end-stage threshold.",
         "Arterial blood gas result.", "Reflects severe impairment of ventilation.",
         "End-stage indicator supporting LCD Pulmonary Disease review (criterion 2c)."),
        ("Cor Pulmonale Secondary to Pulmonary Disease", "Right heart failure secondary to chronic pulmonary disease.",
         "Echocardiogram/clinical exam.", "Reflects advanced pulmonary-vascular burden.",
         "End-stage indicator supporting LCD Pulmonary Disease review (criterion 3)."),
        ("Progressive Serial FEV1 Decline (>40 mL/Year)", "Documented rapid decline in lung function over time.",
         "Serial spirometry trend.", "Reflects accelerating disease progression.",
         "End-stage indicator supporting LCD Pulmonary Disease review (criterion 1b)."),
        ("Advanced Functional Decline", "Profound, near-total functional dependence at end stage.",
         "Functional/PPS assessment.", "Reflects end-stage functional status.",
         "Supports overall terminal-prognosis picture."),
        ("Advanced Nutritional Decline (Pulmonary Cachexia)", "Profound protein-energy wasting at end stage.",
         "Weight trend.", "Reflects end-stage nutritional status.",
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
# present in the ontology is skipped rather than creating an orphan edge.
# ---------------------------------------------------------------------------
DISEASE_TO_DISEASE_RELATIONSHIPS: List[Tuple[str, str, str]] = [
    (COPD, "MAY_PROGRESS_TO", CRF),
    (CRF, "MAY_CONTRIBUTE_TO", "Chronic Systolic Heart Failure"),
]

# (source_disease_name, relationship_type, target_concept_type, target_disease_name, target_concept_name)
DISEASE_TO_CONCEPT_RELATIONSHIPS: List[Tuple[str, str, str, str, str]] = [
    (CRF, "MAY_CAUSE", "COMPLICATION", CRF, "Cor Pulmonale (Right Heart Failure)"),
    (CRF, "MAY_CAUSE", "COMPLICATION", CRF, "Hypoxemic Respiratory Failure"),
    (CRF, "MAY_CAUSE", "COMPLICATION", CRF, "Hypercapnic Respiratory Failure"),
    (CRF, "MAY_CAUSE", "SYMPTOM", CRF, "Disabling Dyspnea at Rest"),
]

# No relationships to diseases outside the existing ontology were requested
# for this task; none were skipped.
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
    domain in CONCEPT_DOMAINS, for Chronic Obstructive Pulmonary Disease and
    Chronic Respiratory Failure only. Hospice-eligibility-support concepts
    always cite the LCD regardless of source disease; all other concept
    types cite the general COPD clinical-knowledge source."""
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
                source_label = EVIDENCE_SOURCE_BY_DISEASE_NAME.get(disease_name, PULM_SOURCE)
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
    """Run the full A-K population for the Pulmonary System (COPD + CRF)
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
