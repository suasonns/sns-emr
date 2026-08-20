from __future__ import annotations

import copy
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


SUPPORT_PERSON_TEMPLATE = {"name": "", "phone": "", "relationship": ""}

INITIAL_FORM: dict[str, Any] = {
    "pain": {
        "uncomfortable": "",
        "painLevel": "",
        "mentalStatus": "",
        "historian": "",
        "historianOtherName": "",
        "historianOtherRelation": "",
        "notes": "",
    },
    "psychosocial": {
        "maritalStatus": "",
        "childrenUnder21": "",
        "childrenInHome": "",
        "familyPcgName": "",
        "familyPcgRelation": "",
        "familyPcgHireDuration": "",
        "patientLives": "",
        "livingArrangement": "",
        "familyCommunication": "",
        "familyRelation": "",
        "familyResponseToIllness": "",
        "socialInteraction": "",
        "supportSystem": "",
        "supportPersons": [
            copy.deepcopy(SUPPORT_PERSON_TEMPLATE),
            copy.deepcopy(SUPPORT_PERSON_TEMPLATE),
        ],
        "communitySupportSystems": "",
        "communicationStyle": "",
        "communicationStyleOther": "",
        "drugAlcoholHistory": "",
        "culturalDiversityCommunication": "",
        "culturalDiversitySpace": "",
        "culturalDiversityFamilyRole": "",
        "culturalDiversityTraditions": "",
        "responsiblePartyName": "",
        "responsiblePartyRelationship": "",
        "mentalCompetency": "",
        "literacyLanguageSkills": "",
        "legalConcerns": "",
        "roleChanges": "",
        "caregiverAvailabilityCapability": "",
        "environmentalSafetyObstacles": "",
        "spiritualIssuesConcern": False,
        "spiritualIssuesNote": "",
        "longTermCareAppropriate": "",
        "notes": "",
    },
    "patientDistress": {
        "patientResponse": [],
        "patientConcerns": [],
        "iadl": {
            "phoneAccess": "",
            "shopping": "",
            "mealPrep": "",
            "housework": "",
            "finances": "",
        },
        "anxietyRating": "",
        "anxietyRatedBy": "",
        "distressRating": "",
        "distressRatedBy": "",
        "responseToPreviousLoss": "",
        "copingStyle": "",
        "illnessImpactPhysicalFunction": "",
        "planOfCareComplianceObstacles": "",
        "ongoingCopingItems": [],
        "suicideRisk": {
            "ageSexRiskFactorsPresent": False,
            "earlyChildhoodLoss": False,
            "currentAlcoholDrugAbuse": False,
            "recentIrreversibleLoss": False,
            "specificSuicidePlanIdentified": False,
            "lethalityOfMethod": "",
            "meansAvailability": "",
            "notLeftUnsupervised": False,
            "notes": "",
            "notifiedCaseManagerSupervisor": False,
            "notifiedCaseManagerSupervisorAt": "",
            "notifiedAttendingPhysician": False,
            "notifiedAttendingPhysicianAt": "",
        },
        "abuseNeglectExploitation": {
            "categories": [],
            "indicatorsObserved": "",
            "reportedTo": "",
            "reportDate": "",
            "reportReferenceCaseNumber": "",
            "reportedBy": "",
            "reportedByUserId": "",
        },
        "notes": "",
    },
    "familyDistress": {
        "familyResponse": [],
        "abilityToProvideCare": "",
        "willingnessToProvideCare": "",
        "familyCrisis": [],
        "pcgAnxietyRating": "",
        "pcgAnxietyRatedBy": "",
        "notes": "",
    },
    "financialLegal": {
        "allNeedsMet": "",
        "isVeteran": "",
        "carePaidBy": "",
        "financialAssessmentNote": "",
        "patientLacks": [],
        "needsAssistance": [],
        "livingWill": "",
        "livingWillCopy": "",
        "livingWillNeedHelp": "",
        "healthPOA": "",
        "healthPOACopy": "",
        "healthPOANeedHelp": "",
        "healthProxy": "",
        "healthProxyCopy": "",
        "healthProxyNeedHelp": "",
        "burialPlans": "",
        "burialPlansNeedHelp": "",
        "mortuaryName": "",
        "mortuaryPhone": "",
        "mortuaryAddress": "",
        "mortuaryCity": "",
        "mortuaryState": "",
        "mortuaryZip": "",
        "notes": "",
    },
    "referrals": {
        "communityProgram": "",
        "communityAccepted": "",
        "communityReferralSatisfaction": "",
        "therapy": [],
        "volunteerServices": [],
        "notes": "",
    },
    "narrative": {
        "careProvided": [],
        "notes": "",
    },
    "finalization": {
        "staff_title": "",
        "assessment_complete": False,
        "clinician_name": "",
        "clinician_user_id": "",
        "signature_date": "",
        "patient_acknowledgement": False,
        "patient_signature_name": "",
        "patient_signature_relationship": "",
        "patient_signature_date": "",
        "countersign_required": False,
        "countersign_staff_name": "",
        "countersign_staff_user_id": "",
        "countersign_staff_title": "",
        "countersign_signature_date": "",
    },
}


def build_initial_form() -> dict[str, Any]:
    return copy.deepcopy(INITIAL_FORM)



def _merge_template(template: Any, value: Any) -> Any:
    if isinstance(template, dict):
        source = value if isinstance(value, dict) else {}
        merged = {key: _merge_template(template_value, source.get(key)) for key, template_value in template.items()}
        for key, extra_value in source.items():
            if key not in merged:
                merged[key] = copy.deepcopy(extra_value)
        return merged

    if isinstance(template, list):
        if not isinstance(value, list):
            return copy.deepcopy(template)
        return copy.deepcopy(value)

    return copy.deepcopy(template if value is None else value)



def merge_msw_ica_form_data(form_data: dict[str, Any] | None) -> dict[str, Any]:
    merged = _merge_template(INITIAL_FORM, form_data if isinstance(form_data, dict) else {})

    support_people = merged.get("psychosocial", {}).get("supportPersons")
    normalized_support_people: list[dict[str, Any]] = []
    if isinstance(support_people, list):
        for item in support_people:
            if isinstance(item, dict):
                normalized_support_people.append({
                    "name": str(item.get("name") or ""),
                    "phone": str(item.get("phone") or ""),
                    "relationship": str(item.get("relationship") or ""),
                })
    while len(normalized_support_people) < 2:
        normalized_support_people.append(copy.deepcopy(SUPPORT_PERSON_TEMPLATE))
    merged["psychosocial"]["supportPersons"] = normalized_support_people

    merged["patientDistress"]["patientResponse"] = list(merged["patientDistress"].get("patientResponse") or [])
    merged["patientDistress"]["patientConcerns"] = list(merged["patientDistress"].get("patientConcerns") or [])
    merged["patientDistress"]["ongoingCopingItems"] = list(merged["patientDistress"].get("ongoingCopingItems") or [])
    merged["patientDistress"]["abuseNeglectExploitation"]["categories"] = list(
        (merged["patientDistress"].get("abuseNeglectExploitation") or {}).get("categories") or []
    )
    merged["familyDistress"]["familyResponse"] = list(merged["familyDistress"].get("familyResponse") or [])
    merged["familyDistress"]["familyCrisis"] = list(merged["familyDistress"].get("familyCrisis") or [])
    merged["financialLegal"]["patientLacks"] = list(merged["financialLegal"].get("patientLacks") or [])
    merged["financialLegal"]["needsAssistance"] = list(merged["financialLegal"].get("needsAssistance") or [])
    merged["referrals"]["therapy"] = list(merged["referrals"].get("therapy") or [])
    merged["referrals"]["volunteerServices"] = list(merged["referrals"].get("volunteerServices") or [])
    merged["narrative"]["careProvided"] = list(merged["narrative"].get("careProvided") or [])
    return merged


class MswIcaAssessment(Base):
    __tablename__ = "msw_ica_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id", ondelete="SET NULL"), nullable=True, index=True)

    assessment_type = Column(String(32), nullable=False, default="MSWICA")
    status = Column(String(32), nullable=False, default="DRAFT")
    locked = Column(Boolean, nullable=False, default=False)

    form_data = Column(JSONB, nullable=False, default=build_initial_form)
    notes = Column(Text, nullable=True)

    locked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    patient = relationship("Patient", backref="msw_ica_assessments")
    visit = relationship("Visit", backref="msw_ica_assessments")
