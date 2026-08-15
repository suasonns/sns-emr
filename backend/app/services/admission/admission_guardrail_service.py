# services/admission/admission_guardrail_service.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.admission import Admission

import logging

logger = logging.getLogger(__name__)


class TrainingModeBlockedError(ValueError):
    """Raised when a real workflow action is attempted on a training patient."""


class AdmissionPrerequisiteError(ValueError):
    """Raised when a required prerequisite for admission-related action is missing."""


@dataclass(frozen=True)
class AdmissionReadiness:
    ready: bool
    blockers: list[str]


class AdmissionGuardrailService:
    """
    Admission guardrail service.

    PURPOSE
    -------
    Prevent accidental admissions and centralize the exact trigger logic for hospice admission.

    FINAL RULES ENFORCED
    --------------------
    1. Training patients can never be admitted.
    2. RN ICA is assessment only and never changes admission state.
    3. Consent/election does NOT automatically admit the patient.
    4. Records release does NOT automatically admit the patient.
    5. Admission happens ONLY when:
         - patient is not training
         - election/consent is signed
         - records release is signed
         - SOC datetime is manually entered
         - if authorization fields exist, they must also be complete
    6. This supports BOTH:
         - RN-driven workflow
         - Office-driven workflow

    EXISTING FIELD ASSUMPTIONS
    --------------------------
    This module intentionally uses your existing field names where possible:

    Patient:
        tenant_id
        is_training
        records_release_signed_at
        admission_status
        updated_at
        updated_by

    Admission:
        tenant_id
        patient_id
        status
        election_signed_at
        soc_date
        effective_date
        admission_date
        admission_authorized_at
        admission_authorized_by
        updated_at
        updated_by

    IMPORTANT
    ---------
    This module does NOT require RN ICA to exist.
    RN ICA may be started/completed independently and will NEVER admit the patient.
    """

    # =========================================================
    # PUBLIC API
    # =========================================================

    @staticmethod
    def ensure_not_training(patient: Patient) -> None:
        """
        Hard guardrail for training patients.
        """
        if getattr(patient, "is_training", False):
            raise TrainingModeBlockedError(
                "Training Mode – real admission, SOC, orders, census activation, and billing actions are disabled"
            )

    @classmethod
    def get_latest_admission(
        cls,
        *,
        db: Session,
        patient: Patient,
    ) -> Admission:
        """
        Fetch latest admission for a patient.
        """
        tenant_id = getattr(patient, "tenant_id", None)
        if not tenant_id:
            raise AdmissionPrerequisiteError("Patient tenant_id is missing")
        
        admission = (
            db.query(Admission)
            .filter(
                Admission.tenant_id == tenant_id,
                Admission.patient_id == patient.id,
            )
            .order_by(Admission.created_at.desc())
            .first()
        )
        
        if not admission:
            raise AdmissionPrerequisiteError("Admission record missing")

        return admission

    @classmethod
    def record_election_signed(
        cls,
        *,
        db: Session,
        patient: Patient,
        election_signed_at: datetime,
        actor_user_id: UUID,
        commit: bool = True,
    ) -> dict[str, Any]:
        """
        Record the election/consent signature.

        IMPORTANT:
        - Does NOT admit the patient.
        - Leaves status as PENDING.
        - Merely records legal prerequisite and returns current readiness.
        """
        cls.ensure_not_training(patient)

        if election_signed_at is None:
            raise AdmissionPrerequisiteError("election_signed_at is required")

        admission = cls.get_latest_admission(
            db=db,
            patient=patient,
        )

        signed_at = cls._normalize_input_dt(election_signed_at)

        admission.election_signed_at = signed_at

        # Election signature does not own effective_date

        cls._touch_model(
            model=admission,
            actor_user_id=actor_user_id,
        )

        # Deliberately keep pending / not admitted
        if getattr(admission, "status", None) is None:
            admission.status = "PENDING"

        readiness = cls._readiness_without_soc(
            patient=patient,
            admission=admission,
        )

        if hasattr(patient, "admission_status"):
            # Derived workflow state only; not yet admitted
            patient.admission_status = "CONSENT_SIGNED"

        cls._touch_model(
            model=patient,
            actor_user_id=actor_user_id,
            utc_aware=True,
        )

        if commit:
            db.commit()
            db.refresh(admission)
            db.refresh(patient)
        else:
            db.flush()

        return {
            "success": True,
            "admitted": False,
            "training_blocked": False,
            "trigger_source": "CONSENT",
            "admission_id": str(admission.id),
            "patient_id": str(patient.id),
            "status": admission.status,
            "patient_admission_status": getattr(patient, "admission_status", None),
            "election_signed_at": admission.election_signed_at,
            "records_release_signed_at": getattr(patient, "records_release_signed_at", None),
            "soc_date": getattr(admission, "soc_date", None),
            "ready_for_admission": readiness.ready,
            "blockers": readiness.blockers,
            "message": "Election/consent recorded. System is waiting for manual SOC date before admitting.",
        }

    @classmethod
    def record_records_release_signed(
        cls,
        *,
        db: Session,
        patient: Patient,
        signed_at: datetime,
        actor_user_id: UUID,
        commit: bool = True,
    ) -> dict[str, Any]:
        """
        Record records release signature.

        IMPORTANT:
        - Does NOT admit the patient.
        - Leaves status as PENDING.
        """
        cls.ensure_not_training(patient)

        if signed_at is None:
            raise AdmissionPrerequisiteError("records release signed_at is required")

        admission = cls.get_latest_admission(
            db=db,
            patient=patient,
        )

        normalized = cls._normalize_input_dt(signed_at)

        patient.records_release_signed_at = normalized
        cls._touch_model(
            model=patient,
            actor_user_id=actor_user_id,
            utc_aware=True,
        )

        readiness = cls._readiness_without_soc(
            patient=patient,
            admission=admission,
        )

        if hasattr(patient, "admission_status") and getattr(patient, "admission_status", None) in {None, "REFERRAL"}:
            patient.admission_status = "CONSENT_SIGNED"

        if commit:
            db.commit()
            db.refresh(patient)
            db.refresh(admission)
        else:
            db.flush()

        return {
            "success": True,
            "admitted": False,
            "training_blocked": False,
            "trigger_source": "RECORDS_RELEASE",
            "admission_id": str(admission.id),
            "patient_id": str(patient.id),
            "status": admission.status,
            "patient_admission_status": getattr(patient, "admission_status", None),
            "election_signed_at": getattr(admission, "election_signed_at", None),
            "records_release_signed_at": patient.records_release_signed_at,
            "soc_date": getattr(admission, "soc_date", None),
            "ready_for_admission": readiness.ready,
            "blockers": readiness.blockers,
            "message": "Records release recorded. System is waiting for manual SOC date before admitting.",
        }

    @classmethod
    def start_rn_ica(
        cls,
        *,
        db: Session,
        patient: Patient,
        actor_user_id: UUID,
        commit: bool = False,
    ) -> dict[str, Any]:
        """
        RN ICA is assessment only.

        IMPORTANT:
        - NEVER changes admission state.
        - Safe for training? No. Real-only by default.
          If you want training ICA allowed, remove ensure_not_training() here
          and keep training blocked only from SOC/admission/order entry.
        """
        cls.ensure_not_training(patient)

        admission = cls.get_latest_admission(
            db=db,
            patient=patient,
        )

        readiness = cls._readiness_without_soc(
            patient=patient,
            admission=admission,
        )

        if commit:
            db.commit()

        return {
            "success": True,
            "admitted": False,
            "training_blocked": False,
            "trigger_source": "RN_ICA",
            "patient_id": str(patient.id),
            "admission_id": str(admission.id),
            "status": admission.status,
            "patient_admission_status": getattr(patient, "admission_status", None),
            "ready_for_admission": readiness.ready,
            "blockers": readiness.blockers,
            "message": "RN ICA started. No admission state change occurred.",
        }

    @classmethod
    def complete_rn_ica(
        cls,
        *,
        db: Session,
        patient: Patient,
        actor_user_id: UUID,
        commit: bool = False,
    ) -> dict[str, Any]:
        """
        RN ICA completion is assessment only.

        IMPORTANT:
        - NEVER changes admission state.
        """
        cls.ensure_not_training(patient)

        admission = cls.get_latest_admission(
            db=db,
            patient=patient,
        )

        readiness = cls._readiness_without_soc(
            patient=patient,
            admission=admission,
        )

        if commit:
            db.commit()

        return {
            "success": True,
            "admitted": False,
            "training_blocked": False,
            "trigger_source": "RN_ICA_COMPLETE",
            "patient_id": str(patient.id),
            "admission_id": str(admission.id),
            "status": admission.status,
            "patient_admission_status": getattr(patient, "admission_status", None),
            "ready_for_admission": readiness.ready,
            "blockers": readiness.blockers,
            "message": "RN ICA completed. No admission state change occurred.",
        }

    @classmethod
    def set_soc_datetime(
        cls,
        *,
        db: Session,
        patient: Patient,
        soc_datetime: datetime,
        actor_user_id: UUID,
        trigger_source: str = "RN",
        commit: bool = True,
    ) -> dict[str, Any]:
        """
        Set manual SOC datetime and trigger admission if prerequisites are satisfied.

        THIS IS THE ONLY PLACE THAT SHOULD AUTO-PROMOTE TO ADMITTED.
        """
        cls.ensure_not_training(patient)

        if soc_datetime is None:
            raise AdmissionPrerequisiteError("soc_datetime is required")

        admission = cls.get_latest_admission(
            db=db,
            patient=patient,
        )

        normalized_soc = cls._normalize_input_dt(soc_datetime)

        admission.soc_date = normalized_soc

        # Keep these aligned to SOC if present in your schema.
        if hasattr(admission, "effective_date"):
            admission.effective_date = normalized_soc

        if hasattr(admission, "admission_date"):
            admission.admission_date = normalized_soc

        cls._touch_model(
            model=admission,
            actor_user_id=actor_user_id,
        )

        readiness = cls.get_admission_readiness(
            patient=patient,
            admission=admission,
        )

        admitted = False
        if readiness.ready:
            admission.status = "ADMITTED"
            admitted = True

            if hasattr(patient, "admission_status"):
                patient.admission_status = "ADMITTED"

            cls._touch_model(
                model=patient,
                actor_user_id=actor_user_id,
                utc_aware=True,
            )
        else:
            # Keep it pending if prerequisites are incomplete.
            if getattr(admission, "status", None) != "NON_ADMIT":
                admission.status = "PENDING"

            if hasattr(patient, "admission_status") and getattr(patient, "admission_status", None) in {None, "REFERRAL"}:
                patient.admission_status = "CONSENT_SIGNED"

            cls._touch_model(
                model=patient,
                actor_user_id=actor_user_id,
                utc_aware=True,
            )

        if commit:
            db.commit()
            db.refresh(admission)
            db.refresh(patient)
        else:
            db.flush()

        return {
            "success": True,
            "admitted": admitted,
            "training_blocked": False,
            "trigger_source": trigger_source,
            "patient_id": str(patient.id),
            "admission_id": str(admission.id),
            "status": admission.status,
            "patient_admission_status": getattr(patient, "admission_status", None),
            "election_signed_at": getattr(admission, "election_signed_at", None),
            "records_release_signed_at": getattr(patient, "records_release_signed_at", None),
            "soc_date": admission.soc_date,
            "ready_for_admission": readiness.ready,
            "blockers": readiness.blockers,
            "message": (
                "Patient admitted after manual SOC datetime entry."
                if admitted
                else "SOC datetime saved, but admission prerequisites are still incomplete."
            ),
        }

    @classmethod
    def get_admission_readiness(
        cls,
        *,
        patient: Patient,
        admission: Admission,
    ) -> AdmissionReadiness:
        """
        Full readiness check including SOC.

        Admission is ready ONLY when all required prerequisites are complete.
        """
        blockers: list[str] = []

        if getattr(patient, "is_training", False):
            blockers.append("Patient is marked as training")

        if not getattr(admission, "election_signed_at", None):
            blockers.append("Election/consent is not signed")

        if not getattr(patient, "records_release_signed_at", None):
            blockers.append("Records release is not signed")

        if not getattr(admission, "soc_date", None):
            blockers.append("SOC datetime is not set")

        # Optional authorization guardrails only if your schema actively uses them
        if hasattr(admission, "admission_authorized_at"):
            if not getattr(admission, "admission_authorized_at", None):
                blockers.append("Admission is not authorized")

        if hasattr(admission, "admission_authorized_by"):
            if not getattr(admission, "admission_authorized_by", None):
                blockers.append("Admission authorizer is missing")

        return AdmissionReadiness(
            ready=not blockers,
            blockers=blockers,
        )

    # =========================================================
    # INTERNAL HELPERS
    # =========================================================

    @classmethod
    def _readiness_without_soc(
        cls,
        *,
        patient: Patient,
        admission: Admission,
    ) -> AdmissionReadiness:
        """
        Readiness snapshot BEFORE SOC is entered.
        Useful after consent/release actions.
        """
        blockers: list[str] = []

        if getattr(patient, "is_training", False):
            blockers.append("Patient is marked as training")

        if not getattr(admission, "election_signed_at", None):
            blockers.append("Election/consent is not signed")

        if not getattr(patient, "records_release_signed_at", None):
            blockers.append("Records release is not signed")

        # Intentionally SOC blocker here, because this is the final trigger.
        if not getattr(admission, "soc_date", None):
            blockers.append("Waiting for manual SOC datetime")

        if hasattr(admission, "admission_authorized_at"):
            if not getattr(admission, "admission_authorized_at", None):
                blockers.append("Admission is not authorized")

        if hasattr(admission, "admission_authorized_by"):
            if not getattr(admission, "admission_authorized_by", None):
                blockers.append("Admission authorizer is missing")

        return AdmissionReadiness(
            ready=not blockers,
            blockers=blockers,
        )

    @staticmethod
    def _normalize_input_dt(value: datetime) -> datetime:
        """
        Normalize incoming datetimes to naive UTC for DB consistency.
        """
        if value is None:
            raise AdmissionPrerequisiteError("Datetime value is required")

        if value.tzinfo is None:
            return value

        return value.astimezone(timezone.utc).replace(tzinfo=None)

    @staticmethod
    def _touch_model(
        *,
        model: Any,
        actor_user_id: UUID,
        utc_aware: bool = False,
    ) -> None:
        """
        Update standard audit fields safely if they exist.
        """
        now_aware = datetime.now(timezone.utc)
        now_naive = now_aware.replace(tzinfo=None)

        if hasattr(model, "updated_at"):
            model.updated_at = now_aware if utc_aware else now_naive

        if hasattr(model, "updated_by"):
            model.updated_by = actor_user_id
