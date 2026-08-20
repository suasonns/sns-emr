from __future__ import annotations

import copy
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


SUICIDE_RISK_TEMPLATE = {
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
}

SOURCE_DETAILS_TEMPLATE = {
    "Unfinished business": "",
    "Anger": "",
    "Grieving": "",
    "Fear": "",
    "Guilt": "",
    "Other losses": "",
}

INITIAL_FORM: dict[str, Any] = {
    "visitMeta": {
        "correction": False,
        "typeOfVisit": "",
        "visitKind": "",
        "visitKindSpecify": "",
        "reasonForVisit": "Initial Comprehensive Assessment",
        "visitDate": "",
        "timeIn": "",
        "timeOut": "",
        "duration": "",
        "enteredBy": "",
        "staffAssigned": "",
        "discipline": "SC",
        "careLevel": "",
    },
    "pain": {
        "controlled": "",
        "level": "",
    },
    "deliveryOfCare": {
        "declined": "",
        "hospiceScProvided": "",
        "alternateCaregiverName": "",
        "alternateCaregiverRelation": "",
        "alternateCaregiverPhone": "",
    },
    "spiritualCircumstances": {
        "mentalStatus": "",
        "historian": "",
        "historianOtherName": "",
        "historianOtherRelation": "",
        "maritalStatus": "",
        "childrenUnder21": "",
        "childrenInHome": "",
        "patientFaithCommunity": {
            "faith": "",
            "denomination": "",
            "faithCommunityName": "",
            "involvement": "",
            "address": "",
            "clergyName": "",
            "phone": "",
        },
        "pcgFaithCommunity": {
            "sameAsPatient": False,
            "faith": "",
            "denomination": "",
            "faithCommunityName": "",
            "involvement": "",
            "address": "",
            "clergyName": "",
            "phone": "",
        },
        "faithDecisionMaker": "",
        "cultureDecisionMaker": "",
        "spiritualSupport": [],
        "spiritualSupportOther": "",
    },
    "patientDistress": {
        "unresponsive": False,
        "sources": [],
        "sourceOther": "",
        "sourceDetails": copy.deepcopy(SOURCE_DETAILS_TEMPLATE),
        "rating": "",
        "ratedBy": [],
        "suicideRisk": copy.deepcopy(SUICIDE_RISK_TEMPLATE),
    },
    "caregiverDistress": {
        "sources": [],
        "sourceOther": "",
        "sourceDetails": copy.deepcopy(SOURCE_DETAILS_TEMPLATE),
        "rating": "",
        "ratedBy": [],
        "suicideRisk": copy.deepcopy(SUICIDE_RISK_TEMPLATE),
    },
    "narrative": {
        "careProvided": [],
        "careProvidedOther": "",
        "note": "",
    },
    "signature": {
        "acknowledgement": "",
        "signedByName": "",
        "signedByUserId": "",
        "signedByCredentials": "SC",
        "signedDate": "",
        "reviewDate": "",
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



def merge_scica_form_data(form_data: dict[str, Any] | None) -> dict[str, Any]:
    merged = _merge_template(INITIAL_FORM, form_data if isinstance(form_data, dict) else {})

    merged["spiritualCircumstances"]["spiritualSupport"] = list(merged["spiritualCircumstances"].get("spiritualSupport") or [])
    merged["patientDistress"]["sources"] = list(merged["patientDistress"].get("sources") or [])
    merged["caregiverDistress"]["sources"] = list(merged["caregiverDistress"].get("sources") or [])
    merged["narrative"]["careProvided"] = list(merged["narrative"].get("careProvided") or [])

    patient_rated_by = merged["patientDistress"].get("ratedBy")
    caregiver_rated_by = merged["caregiverDistress"].get("ratedBy")
    merged["patientDistress"]["ratedBy"] = list(patient_rated_by) if isinstance(patient_rated_by, list) else []
    merged["caregiverDistress"]["ratedBy"] = list(caregiver_rated_by) if isinstance(caregiver_rated_by, list) else []

    patient_source_details = merged["patientDistress"].get("sourceDetails")
    caregiver_source_details = merged["caregiverDistress"].get("sourceDetails")
    merged["patientDistress"]["sourceDetails"] = {
        key: str((patient_source_details or {}).get(key) or "")
        for key in SOURCE_DETAILS_TEMPLATE
    }
    merged["caregiverDistress"]["sourceDetails"] = {
        key: str((caregiver_source_details or {}).get(key) or "")
        for key in SOURCE_DETAILS_TEMPLATE
    }
    return merged


class ScicaAssessment(Base):
    __tablename__ = "scica_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id", ondelete="SET NULL"), nullable=True, index=True)

    assessment_type = Column(String(32), nullable=False, default="SCICA")
    status = Column(String(32), nullable=False, default="DRAFT")
    locked = Column(Boolean, nullable=False, default=False)

    form_data = Column(JSONB, nullable=False, default=build_initial_form)
    notes = Column(Text, nullable=True)

    locked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    patient = relationship("Patient", backref="scica_assessments")
    visit = relationship("Visit", backref="scica_assessments")
