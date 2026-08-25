"""
One-time data-correction script: populate Loren Shields' (patient_id
3885a918-7c8b-4d6d-af3a-577cc898ebdb) facesheet, PatientDiagnosis records,
and RNICA assessment using his real HospiceMD RN Comprehensive Nursing
Assessment (visit 5/22/2024 by Romel Suason, RN) plus supporting Kaiser
Permanente chart-export demographics.

SUPERSEDED: patient_id 3885a918-7c8b-4d6d-af3a-577cc898ebdb no longer
exists (Loren Shields' canonical record is now patient_id
c4410e1f-8ca7-4635-900e-9883e8aca122, same tenant). Also,
HEART_FAILURE_CRITERIA_ANSWERS below uses "yes"/"unknown" strings, which
do not match the real boolean True/False/None convention the eligibility
engine (_compare's EQUALS operator) and RNICA.jsx's LcdTernaryButtons
actually use -- "yes" == True is False in Python, so running this script
as-is would silently fail to satisfy any LCD criterion. Kept for
historical reference only; see scripts/backfill_loren_lcd_eligibility.py
for the corrected, currently-applicable backfill against the live record.

Run with: python scripts/populate_loren_shields.py
"""
from datetime import date, datetime, timezone

from app.core.database import SessionLocal
from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet
from app.models.patient_diagnosis import PatientDiagnosis
from app.models.rnica_assessment import RnicaAssessment
from app.models.enums import DiagnosisType, DiagnosisStatus, DiagnosisSource

PATIENT_ID = "3885a918-7c8b-4d6d-af3a-577cc898ebdb"
TENANT_ID = "01271980-0000-0000-0000-000005101977"

# (icd10, description, related_to_terminal)
SECONDARY_DX = [
    ("N31.9", "Neuromuscular dysfunction of bladder, unspecified", False),
    ("I87.2", "Venous insufficiency (chronic) (peripheral)", True),
    ("M15.9", "Polyosteoarthritis, unspecified", False),
    ("I20.89", "Other forms of angina pectoris", True),
    ("N20.9", "Urinary calculus, unspecified", False),
    ("N39.0", "Urinary tract infection, site not specified", False),
    ("I10", "Essential (primary) hypertension", True),
    ("J12.3", "Human metapneumovirus pneumonia", False),
    ("Z98.890", "Other specified postprocedural states", False),
    ("Z85.9", "Personal history of malignant neoplasm, unspecified", False),
    ("E44.0", "Moderate protein-calorie malnutrition", False),
    ("I69.351", "Hemiplegia following cerebral infarction affecting right dominant side", False),
    ("E11.42", "Type 2 diabetes mellitus with diabetic polyneuropathy", False),
    ("E78.5", "Hyperlipidemia, unspecified", True),
    ("E11.69", "Type 2 diabetes mellitus with other specified complication", False),
    ("E11.22", "Type 2 diabetes mellitus with diabetic chronic kidney disease", False),
    ("I12.9", "Hypertensive chronic kidney disease with stage 1-4/unspecified chronic kidney disease", True),
    ("N18.31", "Chronic kidney disease, stage 3a", False),
    ("M47.812", "Spondylosis without myelopathy or radiculopathy, cervical region", False),
    ("G89.0", "Central pain syndrome", False),
    ("I25.10", "Atherosclerotic heart disease of native coronary artery without angina pectoris", True),
    ("I25.2", "Old myocardial infarction", True),
    ("I70.0", "Atherosclerosis of aorta", True),
]

NARRATIVE = (
    "This is a case of 73 year-old White male, admitted to Love & Faith Hospice Services, Inc. "
    "under routine care with a terminal diagnosis of Chronic systolic (congestive) heart failure "
    "(I50.22) with secondary diagnoses including venous insufficiency, angina, hypertension, "
    "hypertensive CKD, hyperlipidemia, atherosclerotic heart disease, old MI, and atherosclerosis "
    "of the aorta. Patient lives in Rose Villa Grand Terrace Board and Care Facility. Patient's "
    "POA, Letha Harrison, has had a vehicular accident and undergone brain surgery and cannot "
    "decide on behalf of the patient. Patient has an estranged daughter who he does not want "
    "involved in his medical/financial affairs. Patient is DNR. Hospice MSW arranged for a "
    "paralegal to work with the facility administrator to sign on behalf of the patient wanting "
    "to be placed on hospice. Patient's physical and functional abilities continued to decline. "
    "Alert and oriented to person, place, and time but completely bed/chair-bound, requiring "
    "maximum assistance with all ADLs from paid caregivers. Multiple hospital admissions, most "
    "recent in October of the previous year. Increasing generalized body weakness and "
    "progressive loss of ability to perform ADLs. Braden scale 11 (high risk); Fall risk score "
    "14 (high risk). KPS 40%, PPS 40%, NYHA IV. Chair-bound, relies on wheelchair, needs maximum "
    "assistance due to fatigue and generalized weakness. Requires maximum assist with 6/6 ADLs "
    "due to terminal illness. Cardiac disease results in inability to carry on any physical "
    "activity without discomfort. Optimally treated for heart disease with vasodilators. History "
    "of unexplained syncope/fainting. Incontinent of bladder. Patient is eligible for hospice "
    "services and meets LCD guidelines. Physician/Hospice Medical Director Dr. John Liu certified "
    "the first benefit period (05/22/24 to 08/19/24)."
)

CURRENT_MEDICATIONS = [
    "Duloxetine 60 mg daily (depression/nerve pain)",
    "Norco 5-325mg 1 tab PO for moderate pain (4-6); may take 2 tabs for severe pain (7-10)",
    "Gabapentin 300 mg TID (nerve pain)",
    "Carvedilol 6.25 mg 1 tab PO BID (CHF/hypertension)",
    "Lisinopril 10 mg 1 tab PO daily (hypertension)",
    "Furosemide 40 mg 1 tab PO daily (CHF)",
    "Atorvastatin 80 mg daily (hyperlipidemia)",
    "Glipizide 5 mg BID (type 2 diabetes)",
    "Metformin BID (type 2 diabetes)",
]

HEART_FAILURE_CRITERIA_ANSWERS = {
    "1a": "yes",  # ruled out as surgical candidate
    "1b": "unknown",  # declined surgical procedures - not answered
    "1c": "yes",  # optimally treated with diuretics/vasodilators
    "1d": "unknown",  # unable to be on vasodilators - not answered
    "2a": "yes",  # NYHA class IV
    "2b": "unknown",  # EF < 20 - not documented in this assessment
    "3a": "unknown",
    "3b": "unknown",
    "3c": "yes",  # history of unexplained syncope/fainting
    "3d": "unknown",
    "3e": "unknown",
}


def build_form_data():
    return {
        "demographics": {
            "firstName": "Loren",
            "lastName": "Shields",
            "dob": "1950-07-25",
            "gender": "Male",
            "race": ["White"],
            "ethnicity": [],
            "preferredLanguage": "English",
            "needsInterpreter": False,
            "religion": "",
            "maritalStatus": "",
            "militaryService": "",
            "phone": "910-850-6818",
            "alternatePhone": "805-910-6818",
            "address": {
                "street": "11906 Kingston St",
                "city": "Grand Terrace",
                "state": "CA",
                "zip": "92313-2313",
                "county": "",
            },
            "emergencyContact": {
                "name": "Letha Harrison",
                "relationship": "POA / Advance Directive Agent (Friend)",
                "phone": "805-336-5168",
            },
            "pcg": {
                "name": "",
                "relationship": "No PCG - facility staff provides care",
                "phone": "",
                "healthStatus": "Fair",
                "anxietyLevel": "None",
                "ableToAdministerMeds": "No",
                "willingToProvideCare": "N/A - facility staff",
                "pcgConcerns": (
                    "No PCG. Patient's POA (Letha Harrison) incapacitated after vehicular "
                    "accident/brain surgery and unable to make decisions. Estranged daughter "
                    "not involved per patient wishes. Hospice MSW/paralegal assisted facility "
                    "administrator with consent signature for hospice admission."
                ),
                "caregiverEvaluation": {
                    "physicalAbility": "",
                    "cognitiveAbility": "",
                    "emotionalReadiness": "",
                    "availabilityForCare": "",
                    "trainingNeeds": ["Hospice", "Disease process", "Medication", "Advance directive"],
                    "willingnessScore": "",
                    "capabilityScore": "",
                    "supportSystemAdequacy": "Limited",
                    "evaluationNotes": "",
                },
            },
            "livingSituation": {
                "siteOfService": "Hospice in patient's home/residence (B&C, RCFE)",
                "admittedFrom": "Residential Setting (Home, B&C, AL)",
                "livingArrangement": "Rose Villa Grand Terrace Board and Care Facility",
                "availabilityOfAssistance": "Facility staff (paid caregivers)",
            },
            "advancedCarePlanning": {
                "codeStatus": "DNR",
                "codeStatusDate": "2024-05-22",
                "lifeSustainingTreatmentPreference": "No",
                "lifeSustainingTreatmentPreferenceDate": "2024-05-22",
                "hospitalizationPreference": "Wants to avoid hospitalization",
                "hospitalizationPreferenceDate": "2024-05-22",
                "decisionMaker": "Facility administrator (via MSW/paralegal, due to incapacitated POA)",
                "poaName": "Letha Harrison (incapacitated - vehicular accident/brain surgery)",
                "poaPhone": "805-336-5168",
                "advanceDirectiveOnFile": False,
                "polstOnFile": False,
            },
        },

        "vitals": {
            "temperature": "99", "temperatureUnit": "F",
            "pulse": "100", "pulseQuality": "", "pulseRhythm": "",
            "respirations": "24", "respirationPattern": "",
            "bloodPressure": {"systolic": "130", "diastolic": "70", "position": ""},
            "height": "", "heightUnit": "in", "weight": "", "weightUnit": "lbs",
            "bmi": "", "mac": "38", "oxygenSaturation": "98", "oxygenSaturationOnRA": False,
            "ivAssessment": {
                "hasIV": False, "type": "", "size": "", "site": "",
                "dressingType": "", "insertionDate": "", "lastChangeDate": "",
                "condition": "", "flushSchedule": "", "notes": "No IVs.",
            },
        },

        "pain": {
            "verbalizesPain": "Yes",
            "uncomfortableBecauseOfPain": "Yes",
            "neuropathicPain": True,
            "screeningDate": "2024-05-22",
            "comprehensiveAssessmentCompleted": True,
            "comprehensiveAssessmentDate": "2024-05-22",
            "assessmentTool": "",
            "painIntensity": {"current": "4-6", "worst": "7-10", "best": "", "acceptable": ""},
            "painLocation": ["Right knee"],
            "painCharacter": ["Neuropathic"],
            "painRadiation": "",
            "painBodySites": ["Right knee"],
            "painMapMode": "verbal",
            "aggravatingFactors": ["Severely contracted right knee"],
            "relievingFactors": ["Repositioning", "Scheduled rest periods"],
            "painManagementPlan": (
                "Reported to Dr. John Liu; ordered Norco 5-325mg 1 tab PO for moderate pain "
                "(4-6), may take 2 tabs for severe pain (7-10). Continue Gabapentin 300mg TID "
                "for neuropathic pain. Reinforced non-pharmacological interventions: scheduled "
                "rest periods and repositioning."
            ),
            "flacc": {"face": "", "legs": "", "activity": "", "cry": "", "consolability": "", "total": ""},
            "painad": {"breathing": "", "vocalization": "", "facialExpression": "Grimacing", "bodyLanguage": "", "consolability": "", "total": ""},
            "nonPharmInterventions": ["Repositioning", "Scheduled rest periods"],
        },

        "symptomImpact": {
            "pain": "Moderate", "shortnessOfBreath": "Mild", "anxiety": "None",
            "nausea": "None", "vomiting": "None", "diarrhea": "None",
            "constipation": "None", "agitation": "None",
            "totalScore": "", "assessmentDate": "2024-05-22",
        },

        "diagnoses": {
            "primaryDiagnosis": {
                "icd10": "I50.22",
                "description": "Chronic systolic (congestive) heart failure",
                "onsetDate": "",
            },
            "secondaryDiagnoses": [
                {"icd10": code, "description": desc, "relatedToTerminal": related}
                for code, desc, related in SECONDARY_DX
            ],
            "comorbidities": [
                {"icd10": code, "description": desc}
                for code, desc, related in SECONDARY_DX if related
            ],
            "terminalPrognosis": (
                "Life expectancy of 6 months or less if disease follows its normal course. "
                "Certified by Dr. John Liu, Hospice Medical Director, for benefit period 1 "
                "(05/22/24 - 08/19/24)."
            ),
            "diseaseTrajectory": "Slow, steady decline",
            "lcdEligibilityNarrative": NARRATIVE,
            "ndsEligibility": {
                "detectedDisease": "HEART_FAILURE",
                "criteriaAnswers": {"HEART_FAILURE": HEART_FAILURE_CRITERIA_ANSWERS},
                "criteriaFacts": {"HEART_FAILURE": {}},
            },
        },

        "performanceStatus": {
            "pps": "40",
            "ppsJustification": (
                "Mainly in bed, unable to do any work, extensive evidence of disease, "
                "considerable dependence for care, normal or reduced intake, fully "
                "conscious or confused or drowsy."
            ),
            "kps": "40",
            "kpsJustification": "Disabled; requires special care and assistance.",
            "ecog": "", "ecogJustification": "",
            "fast": "", "fastStage": "",
            "nyha": "IV",
            "nyhaJustification": (
                "Unable to carry on any physical activity without discomfort. Symptoms of "
                "heart failure at rest; discomfort increases with any physical activity."
            ),
            "functionalDeclineNotes": (
                "Chair-bound, relies on wheelchair; needs maximum assistance due to fatigue "
                "and generalized body weakness. Requires maximum assist with 6/6 ADLs due to "
                "terminal illness."
            ),
        },

        "neurological": {
            "consciousness": "Alert",
            "orientation": {"time": True, "place": True, "person": True, "situation": True},
            "communication": "Normal", "hearing": "", "vision": "", "balance": "Normal",
            "cognition": "Forgetfulness noted",
            "delirium": False, "seizureHistory": False,
            "psychiatricHistory": "Depression (continue Duloxetine 60mg daily)",
            "sensoryDeficits": [],
            "sleepRest": {
                "sleepPattern": "Satisfied w/ sleep", "averageSleepHours": "6-8",
                "sleepAids": [], "restfulness": "Per PCG, uninterrupted sleep at night", "notes": "",
            },
            "hopeItems": {"n0500": "", "n0510": "", "n0520": ""},
            "notes": "Alert and oriented x3, able to verbalize needs and discomfort.",
        },

        "cardiovascular": {
            "bpSymptoms": ["Normal (SBP 91-159)"],
            "pulseQuality": "Regular",
            "edema": {"present": False, "location": [], "severity": "", "pitting": ""},
            "chestPain": {"present": False, "type": "", "frequency": ""},
            "peripheralCirculation": "", "heartSounds": "", "jvd": False,
            "notes": (
                "BP maintained by Carvedilol 6.25mg BID and Lisinopril 10mg daily. No chest "
                "pain, no edema noted; on Furosemide 40mg daily for CHF. History of two heart "
                "attacks and two strokes. Hyperlipidemia managed with Atorvastatin 80mg daily."
            ),
        },

        "respiratory": {
            "sobSeverity": "Mild", "exertionLevel": "w/ mild exertion",
            "shortnessOfBreathScreened": True, "screeningDate": "2024-05-22",
            "treatmentInitiated": True, "treatmentDate": "2024-05-22",
            "lungSounds": [], "respirations": ["Normal"],
            "coughType": "None", "sputumCharacter": "",
            "oxygenTherapy": {
                "inUse": True, "type": "Nasal cannula", "litersPerMinute": "2",
                "hoursPerDay": "", "satOnO2": "98",
            },
            "notes": (
                "No signs of respiratory distress on visit. Episodes of SOB on minimal "
                "exertion managed with rest, positioning, and supplemental O2. Even though "
                "SOB is present, patient declines further treatment."
            ),
        },

        "infection": {
            "allergies": [],
            "currentInfections": [], "historyOfResistantInfections": [],
            "immunosuppressed": False, "precautions": [],
            "notes": "NKDA. No infection or signs/symptoms of allergy reported.",
        },

        "gastrointestinal": {
            "nausea": "None", "vomiting": "None", "diarrhea": "None", "constipation": "None",
            "bowelSounds": "Normal", "abdomen": "Soft, non-tender, not distended",
            "bowelStatus": "Continent", "lastBM": "2024-05-22",
            "continence": "Continent",
            "feedingTube": {"present": False, "type": "", "site": ""},
            "ostomy": {"present": False, "type": "", "condition": ""},
            "notes": "Bowel movement frequency 4-5x/week. Normoactive bowel sounds x4 quadrants.",
        },

        "nutrition": {
            "weightLossPastSixMonths": "No", "appetite": "Fair",
            "dietType": "Regular NAS", "fluidIntake": "",
            "swallowingIssues": [], "oralMucosa": "",
            "dentures": {"upper": False, "lower": False, "condition": ""},
            "nutritionalSupplements": "",
            "notes": "Consumed ~30% of meal served today per PCG/facility staff report.",
        },

        "endocrine": {
            "thyroid": {"assessment": "", "notes": ""},
            "diabetes": {
                "type": "Type 2", "glucoseMonitoring": "Monitored in hospice care",
                "lastHbA1c": "", "lastHbA1cDate": "",
                "insulinType": "", "insulinDose": "",
                "oralHypoglycemics": ["Glipizide 5mg BID", "Metformin BID"],
            },
            "endocrineSymptoms": [], "symptomSeverity": {},
            "currentEndocrineMeds": ["Glipizide 5mg BID", "Metformin BID"],
            "notes": "",
        },

        "genitourinary": {
            "urinaryStatus": "Incontinent", "frequency": "",
            "catheter": {
                "present": False, "type": "", "size": "",
                "insertionDate": "", "lastChangeDate": "",
                "condition": "", "urineCharacteristics": ["Clear", "Yellow"],
            },
            "urineOutput": "", "twentyFourHourVolume": "",
            "reproductive": {"concerns": [], "notes": ""},
            "bladderManagement": [],
            "notes": "Incontinent of bladder function.",
        },

        "musculoskeletal": {
            "weakness": "Increasing generalized body weakness",
            "rigidity": "", "contractures": "Severely contracted right knee; contractures on bilateral lower extremities",
            "paralysis": "Right hemiplegia (old CVA, residual)",
            "romLimitations": ["Right knee"],
            "gait": "Non-ambulatory", "assistiveDevices": ["Wheelchair", "Hospital bed with full rails"],
            "fallHistory": {"fallsLast90Days": "Yes - history of falls over past 2 months", "fallInjuries": ""},
            "mobility": {
                "ambulatoryStatus": "Non-ambulatory - chair-bound, relies on wheelchair",
                "endurance": "Maximum assist due to fatigue and generalized weakness",
                "transferAbility": "Maximum assist",
            },
            "adl": {
                "bathing": "3 - Maximal/Complete dependence",
                "dressing": "3 - Maximal/Complete dependence",
                "toileting": "3 - Maximal/Complete dependence",
                "transferring": "3 - Maximal/Complete dependence",
                "eating": "3 - Maximal/Complete dependence",
                "grooming": "3 - Maximal/Complete dependence",
            },
            "notes": (
                "Total ADL score 18/18 (max dependence); 6 of 6 activities with complete "
                "dependence. Requires maximum assist with 6/6 ADLs due to terminal illness."
            ),
        },

        "skin": {
            "skinConditionsPresent": True,
            "skinStatus": ["Normal"], "skinTurgor": "Fair",
            "skinBodySites": ["Right ankle"],
            "braden": {
                "sensoryPerception": "2 - Very limited", "moisture": "2 - Very moist",
                "activity": "2 - Chairfast", "mobility": "2 - Very limited",
                "nutrition": "2 - Probably inadequate", "frictionShear": "1 - Problem",
                "total": "11",
            },
            "pressureInjuryRisk": "High risk",
            "wounds": [
                {
                    "location": "Right ankle",
                    "stage": "Stage III",
                    "size": "1.0 x 1.0 x 0.5 cm",
                    "treatment": (
                        "Cleanse with NS, pat dry, apply Santyl, apply collagen, cover with "
                        "dry dressing, change dressing daily until healed."
                    ),
                }
            ],
            "woundImpairment": "Yes",
            "notes": (
                "Braden score 11 (high risk). Reinforced compliance with treatment and "
                "reposition q2h; use mild, unscented soaps; keep perineal area clean."
            ),
        },

        "imminentDeath": {
            "appearsThreeDaysOrLess": "No",
            "indicators": [], "comfortMeasuresInPlace": False, "familyNotified": False,
            "notes": "",
        },

        "sfv": {
            "symptomImpactScreeningCompleted": True,
            "symptomImpactScreeningDate": "2024-05-22",
            "inPersonSfvCompleted": False, "sfvDate": "", "reasonNotCompleted": "", "findings": "",
            "triggeredSymptoms": [],
            "symptomImpactAtSfv": {
                "pain": "", "shortnessOfBreath": "", "anxiety": "", "nausea": "",
                "vomiting": "", "diarrhea": "", "constipation": "", "agitation": "",
            },
            "interventions": [], "notes": "",
        },

        "safety": {
            "safetyAssessmentCompleted": True,
            "homeEnvironment": ["Confined to bed or chair/w-c", "Requires electricity for medical equipment"],
            "fallRiskAssessmentCompleted": True,
            "fallRiskLevel": "High risk (score 14)",
            "firearmInHome": False,
            "oxygenInUse": True, "oxygenSafetyReviewed": True,
            "disasterLevel": "Level 1 - Hospice must assist. No assistance available.",
            "disasterLevelOneConditions": ["Confined to bed or chair-w/c", "Dependent on walker or cane", "Requires electricity for medical equipment"],
            "disasterLevelTwoConditions": [],
            "notes": "Reinforced safety precautions and fall-preventive measures.",
        },

        "psychosocial": {
            "familySocialSupport": "Limited",
            "primarySupportPerson": "Facility administrator / Rose Villa staff",
            "supportRelationship": "Board & Care facility",
            "patientConcerns": ["Financial or legal concerns", "Family relationships strained"],
            "caregiverFamilyConcerns": [],
            "distressRating": "None",
            "psychosocialHistory": [],
            "copingAssessment": "", "copingNotes": "",
            "interventionPlan": ["Social Work"],
            "notes": (
                "No PCG. POA (Letha Harrison) incapacitated after vehicular accident/brain "
                "surgery. Estranged daughter not to be involved per patient wishes. Hospice "
                "MSW arranged paralegal support to obtain facility administrator consent for "
                "hospice admission. SW visit needed: Yes."
            ),
        },

        "spiritual": {
            "patientActiveInFaithTradition": False,
            "patientFaith": "",
            "caregiverActiveInFaithTradition": False, "caregiverFaith": "",
            "spiritualConcerns": [],
            "spiritualDistressRating": "None",
            "concernsDiscussed": False, "concernsDiscussedDate": "",
            "chaplainNeeded": True,
            "notes": "SC visit needed: Yes.",
        },

        "bereavement": {
            "patientConcerns": [], "caregiverConcerns": [],
            "bereavementRisk": "", "riskFactors": [],
            "bereavementVisitNeeded": True,
            "notes": "BC visit needed: Yes.",
        },

        "personalCare": {
            "aideTasks": ["Grooming", "Light meal preparation", "Linen change"],
            "aideVisitPreferences": {"frequency": "", "preferredTime": "", "duration": ""},
            "volunteerServices": [],
            "communityResources": [],
            "equipmentSupplyNeeds": ["Hospital bed with full rails", "Wheelchair"],
            "notes": "",
        },

        "teachingNeeds": {
            "primaryLearner": "Facility staff / PCG",
            "learningStylePreference": "",
            "barriersToLearning": [],
            "educationTopics": [],
            "teachingMethods": [],
            "patientFamilyResponse": "PCG verbalized understanding of teachings provided.",
            "followUpPlan": "",
            "notes": (
                "Teachings provided: diagnosis/disease process, medications (incl. comfort "
                "pack, opioid use/risk), medication reconciliation, oxygen, DME, infection "
                "control, safe use/disposal of controlled medications, skin care, fall "
                "prevention."
            ),
        },

        "admissionsOrder": {
            "admissionStatement": (
                "On completion of assessment and medical history available to me, I have "
                "discussed patient's status with the Physician. Based on information provided "
                "to the Physician and review of patient's medical history, the Physician has "
                "issued an order to admit this patient to Hospice. This is a verbal order / "
                "read back and verified."
            ),
            "levelOfCare": {
                "level": "Routine Home Care", "effectiveDate": "2024-05-22",
                "justification": "Meets LCD hospice eligibility guidelines for Heart Disease.",
            },
            "visitFrequency": [
                {"discipline": "LVN", "frequency": "2x/week for assessment, monitoring, medication reviews and administration, and updates in POC."},
                {"discipline": "MSW", "frequency": "Psychosocial evaluation within 5 days of admission."},
                {"discipline": "RN", "frequency": "Every 14 days and as needed for supervisory visits."},
                {"discipline": "SC", "frequency": "Spiritual needs evaluation within 5 days of admission."},
                {"discipline": "VOL", "frequency": "PRN or upon request."},
            ],
            "treatmentMedsOrderCompleted": True,
            "haAssignment": {"assignedAide": "", "notApplicable": False},
            "initialPocIdg": {
                "created": False, "createdDate": "",
                "notes": "IDG should only be created after all problems identified during this Assessment have been added to Initial POC.",
            },
            "nonCoveredItems": [],
            "toVerification": {
                "verbalOrderReadBack": True, "verifiedBy": "Romel Suason, RN",
                "prescriberContacted": True, "verificationTimestamp": "2024-05-22",
            },
        },

        "medications": {
            "scheduledOpioid": False, "scheduledOpioidDate": "",
            "prnOpioid": True, "prnOpioidDate": "2024-05-22",
            "bowelRegimen": False, "bowelRegimenDate": "",
            "currentMedications": CURRENT_MEDICATIONS,
            "orders": [],
            "medReconciliation": {"completed": True, "completedDate": "2024-05-22", "completedBy": "Romel Suason, RN"},
        },

        "referrals": {
            "socialWork": {"referred": True, "reason": "Psychosocial evaluation, consent/legal support", "urgency": "Within 5 days"},
            "spiritualCare": {"referred": True, "reason": "Spiritual needs evaluation", "urgency": "Within 5 days"},
            "volunteer": {"referred": False, "type": "", "urgency": ""},
            "therapy": [], "dietitian": {"referred": False, "reason": ""},
            "pharmacist": {"referred": False, "reason": ""},
            "other": [], "notes": "",
        },

        "finalization": {
            "completedSections": [],
            "incompleteCount": 0,
            "responseToInterventions": {
                "initialResponseSummary": "",
                "interventionEffectiveness": [],
                "baselineEstablished": True,
                "baselineDate": "2024-05-22",
                "progressNotes": "",
            },
            "pocEntries": [], "pocDraft": {"problem": "", "goal": "", "intervention": "", "discipline": ""},
            "pocGenerationCompleted": False, "pocReviewedWithIdg": False,
            "signatureCertification": True,
            "clinicianSignature": "Romel Suason, RN",
            "signatureDate": "2024-05-22",
        },
    }


def main():
    db = SessionLocal()
    try:
        patient = db.get(Patient, PATIENT_ID)
        if not patient:
            raise RuntimeError("Patient not found")

        # ---- 1. Facesheet corrections ----
        fs = (
            db.query(PatientFaceSheet)
            .filter(PatientFaceSheet.patient_id == PATIENT_ID)
            .first()
        )
        if not fs:
            raise RuntimeError("Facesheet not found")

        fs.gender = fs.gender or "Male"
        fs.race = fs.race or "White"
        fs.language = fs.language or "English"
        fs.phone = fs.phone or "910-850-6818"
        fs.address = fs.address or "11906 Kingston St"
        fs.city = fs.city or "Grand Terrace"
        fs.state = fs.state or "CA"
        fs.zip = fs.zip or "92313-2313"
        fs.has_allergies = False if fs.has_allergies is None else fs.has_allergies
        fs.allergies = fs.allergies or "NKDA (No Known Drug Allergies)"
        fs.emergency_contact_name = fs.emergency_contact_name or "Letha Harrison"
        fs.emergency_contact_relationship = fs.emergency_contact_relationship or "POA / Advance Directive Agent (Friend)"
        fs.emergency_contact_phone = fs.emergency_contact_phone or "805-336-5168"
        fs.medical_director_name = fs.medical_director_name or "John Liu, MD"
        fs.current_level_of_care = fs.current_level_of_care or "Routine Home Care"
        fs.current_pos_type = fs.current_pos_type or "Board & Care / RCFE"
        fs.current_pos_name = fs.current_pos_name or "Rose Villa Grand Terrace Board and Care Facility"
        fs.soc_date = fs.soc_date or date(2024, 5, 22)

        # ---- 2. PatientDiagnosis rows ----
        existing_codes = {
            d.icd10_code
            for d in db.query(PatientDiagnosis).filter(PatientDiagnosis.patient_id == PATIENT_ID).all()
        }

        if "I50.22" not in existing_codes:
            db.add(PatientDiagnosis(
                tenant_id=TENANT_ID,
                patient_id=PATIENT_ID,
                diagnosis_type=DiagnosisType.PRIMARY,
                status=DiagnosisStatus.ACTIVE,
                source=DiagnosisSource.RN_ICA,
                icd10_code="I50.22",
                diagnosis_description="Chronic systolic (congestive) heart failure",
                display_name="Chronic systolic (congestive) heart failure (I50.22)",
                is_terminal=True,
                is_related_to_terminal=True,
                effective_date=date(2024, 5, 22),
                effective_benefit_period_number=1,
                supporting_evidence_summary=(
                    "KPS/PPS 40, NYHA IV, hx of unexplained syncope, optimally treated with "
                    "diuretics/vasodilators, ruled out as surgical candidate. Meets LCD heart "
                    "disease criteria per RN comprehensive assessment 5/22/2024."
                ),
            ))

        added = 0
        for code, desc, related in SECONDARY_DX:
            if code in existing_codes:
                continue
            db.add(PatientDiagnosis(
                tenant_id=TENANT_ID,
                patient_id=PATIENT_ID,
                diagnosis_type=DiagnosisType.SECONDARY,
                status=DiagnosisStatus.ACTIVE,
                source=DiagnosisSource.RN_ICA,
                icd10_code=code,
                diagnosis_description=desc,
                display_name=f"{desc} ({code})",
                is_terminal=False,
                is_related_to_terminal=related,
                effective_date=date(2024, 5, 22),
                effective_benefit_period_number=1,
            ))
            added += 1

        # ---- 3. RNICA assessment ----
        existing_rnica = (
            db.query(RnicaAssessment)
            .filter(RnicaAssessment.patient_id == PATIENT_ID)
            .first()
        )
        if existing_rnica:
            print("RNICA assessment already exists - skipping creation:", existing_rnica.id)
        else:
            rnica = RnicaAssessment(
                patient_id=PATIENT_ID,
                assessment_type="RNICA",
                status="COMPLETED",
                locked=False,
                form_data=build_form_data(),
                notes="Populated from HospiceMD RN Comprehensive Nursing Assessment, visit 5/22/2024, Romel Suason RN.",
                created_at=datetime(2024, 5, 22, tzinfo=timezone.utc),
                updated_at=datetime(2024, 5, 22, tzinfo=timezone.utc),
            )
            db.add(rnica)

        db.commit()
        print(f"Facesheet updated. {added} new secondary diagnoses added. RNICA assessment created/verified.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
