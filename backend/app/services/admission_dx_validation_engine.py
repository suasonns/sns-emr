from __future__ import annotations

import importlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.admission import Admission
from app.models.patient import Patient
from app.models.patient_diagnosis import PatientDiagnosis
from app.models.enums import DiagnosisType, DiagnosisStatus
from app.services.diagnosis_sync_service import sync_official_primary_diagnosis


# =========================================================
# DATA SHAPES
# =========================================================

@dataclass
class PreviousPrimaryDiagnosis:
    id: Optional[uuid.UUID]
    icd10_code: Optional[str]
    display_name: Optional[str]
    diagnosis_description: Optional[str]
    source: Optional[Any]

@dataclass
class DxDecisionResult:
    success: bool
    status: str
    message: str
    previous_primary: Optional[dict[str, Any]]
    new_primary: Optional[dict[str, Any]]
    actions: list[str]


# =========================================================
# ENGINE
# =========================================================

class AdmissionDxValidationEngine:
    """
    Admission DX validation + comparison engine.

    PURPOSE
    -------
    1. Build a new-admission comparison snapshot using prior admission context.
    2. Carry forward secondary + comorbidity diagnoses.
    3. Force RN primary-diagnosis selection.
    4. If the primary changes, move the old primary into secondary for the new chart.
    5. Preserve previous labs/H&P in comparison output instead of overwriting.

    IMPORTANT
    ---------
    - This engine assumes:
        * visits are already tied to admission_id
        * a new admission row already exists
    - It does NOT auto-admit.
    - It does NOT overwrite prior clinical history.
    """

    # -----------------------------------------------------
    # PUBLIC ENTRYPOINT 1
    # -----------------------------------------------------
    @classmethod
    def build_comparison_snapshot(
        cls,
        *,
        db: Session,
        patient: Patient,
        new_admission: Admission,
    ) -> dict[str, Any]:
        previous_admission = cls._get_previous_admission(
            db=db,
            patient=patient,
            new_admission=new_admission,
        )

        if not previous_admission:
            return {
                "status": "no_previous_admission",
                "patient_id": str(patient.id),
                "new_admission_id": str(new_admission.id),
                "previous_admission_id": None,
                "previous_primary": None,
                "secondary_diagnoses": [],
                "comorbidities": [],
                "previous_labs": [],
                "previous_hnp": None,
                "requires_primary_dx_selection": True,
            }

        previous_primary = cls._get_previous_primary(
            db=db,
            patient=patient,
            previous_admission=previous_admission,
        )

        previous_secondary = cls._get_previous_diagnoses_by_type(
            db=db,
            patient=patient,
            previous_admission=previous_admission,
            diagnosis_type=DiagnosisType.SECONDARY,
        )

        previous_comorbidities = cls._get_previous_diagnoses_by_type(
            db=db,
            patient=patient,
            previous_admission=previous_admission,
            diagnosis_type=DiagnosisType.COMORBIDITY,
        )

        previous_labs = cls._load_previous_labs(
            db=db,
            patient=patient,
            previous_admission=previous_admission,
        )

        previous_hnp = cls._load_previous_hnp(
            db=db,
            patient=patient,
            previous_admission=previous_admission,
        )

        return {
            "status": "comparison_ready",
            "patient_id": str(patient.id),
            "new_admission_id": str(new_admission.id),
            "previous_admission_id": str(previous_admission.id),
            "previous_primary": (
                {
                    "id": str(previous_primary.id) if previous_primary and previous_primary.id else None,
                    "icd10_code": previous_primary.icd10_code if previous_primary else None,
                    "display_name": previous_primary.display_name if previous_primary else None,
                    "diagnosis_description": previous_primary.diagnosis_description if previous_primary else None,
                }
                if previous_primary
                else None
            ),
            "secondary_diagnoses": previous_secondary,
            "comorbidities": previous_comorbidities,
            "previous_labs": previous_labs,
            "previous_hnp": previous_hnp,
            "requires_primary_dx_selection": True,
        }

    # -----------------------------------------------------
    # PUBLIC ENTRYPOINT 2
    # -----------------------------------------------------
    @classmethod
    def clone_secondary_and_comorbidities(
        cls,
        *,
        db: Session,
        patient: Patient,
        new_admission: Admission,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        previous_admission = cls._get_previous_admission(
            db=db,
            patient=patient,
            new_admission=new_admission,
        )

        if not previous_admission:
            return {
                "status": "no_previous_admission",
                "cloned_count": 0,
            }

        to_clone = []

        to_clone.extend(
            cls._load_previous_dx_rows(
                db=db,
                patient=patient,
                previous_admission=previous_admission,
                diagnosis_type=DiagnosisType.SECONDARY,
            )
        )

        to_clone.extend(
            cls._load_previous_dx_rows(
                db=db,
                patient=patient,
                previous_admission=previous_admission,
                diagnosis_type=DiagnosisType.COMORBIDITY,
            )
        )

        now = datetime.now(timezone.utc)

        cloned_count = 0

        for old_dx in to_clone:
            if cls._diagnosis_already_exists_on_admission(
                db=db,
                new_admission=new_admission,
                icd10_code=getattr(old_dx, "icd10_code", None),
                diagnosis_type=getattr(old_dx, "diagnosis_type", None),
            ):
                continue

            new_dx = PatientDiagnosis(
                id=uuid.uuid4(),
                tenant_id=patient.tenant_id,
                patient_id=patient.id,
                diagnosis_type=old_dx.diagnosis_type,
                status=DiagnosisStatus.ACTIVE,
                source=getattr(old_dx, "source", None),
                icd10_code=getattr(old_dx, "icd10_code", None),
                diagnosis_description=getattr(old_dx, "diagnosis_description", None),
                display_name=getattr(old_dx, "display_name", None),
                active=True,
                is_terminal=getattr(old_dx, "is_terminal", False),
                is_related_to_terminal=getattr(old_dx, "is_related_to_terminal", False),
                effective_date=getattr(old_dx, "effective_date", None),
                created_by=user_id,
            )

            # If diagnosis rows now support admission_id, use it.
            if hasattr(new_dx, "admission_id"):
                setattr(new_dx, "admission_id", new_admission.id)

            # Optional enterprise flags if your model supports them
            if hasattr(new_dx, "change_reason"):
                new_dx.change_reason = "CLONED_FROM_PREVIOUS_ADMISSION"
            if hasattr(new_dx, "notes"):
                summary = (
                    f"Cloned from previous admission {previous_admission.id} on {now.isoformat()} "
                    f"for review in admission {new_admission.id}."
                )
                new_dx.notes = summary

            db.add(new_dx)
            cloned_count += 1

        db.flush()

        return {
            "status": "secondary_and_comorbidities_cloned",
            "previous_admission_id": str(previous_admission.id),
            "new_admission_id": str(new_admission.id),
            "cloned_count": cloned_count,
        }

    # -----------------------------------------------------
    # PUBLIC ENTRYPOINT 3
    # -----------------------------------------------------
    @classmethod
    def validate_and_apply_primary_decision(
        cls,
        *,
        db: Session,
        patient: Patient,
        new_admission: Admission,
        user_id: uuid.UUID,
        primary_diagnosis: str,
        is_same_primary_as_previous: bool,
    ) -> DxDecisionResult:
        """
        RN must explicitly choose the new primary diagnosis decision.

        RULES
        -----
        - If same primary:
            use previous primary as new primary
        - If different primary:
            create/sync new primary
            move old primary to SECONDARY on the new admission
        """
        previous_admission = cls._get_previous_admission(
            db=db,
            patient=patient,
            new_admission=new_admission,
        )

        previous_primary = cls._get_previous_primary(
            db=db,
            patient=patient,
            previous_admission=previous_admission,
        ) if previous_admission else None

        if is_same_primary_as_previous:
            if not previous_primary or not previous_primary.icd10_code:
                return DxDecisionResult(
                    success=False,
                    status="missing_previous_primary",
                    message="RN selected same primary, but no previous primary diagnosis is available.",
                    previous_primary=(
                        {
                            "id": str(previous_primary.id) if previous_primary and previous_primary.id else None,
                            "icd10_code": previous_primary.icd10_code if previous_primary else None,
                            "display_name": previous_primary.display_name if previous_primary else None,
                            "diagnosis_description": previous_primary.diagnosis_description if previous_primary else None,
                        }
                        if previous_primary
                        else None
                    ),
                    new_primary=None,
                    actions=[],
                )

            # Use existing sync service to keep SSOT behavior consistent
            sync_result = sync_official_primary_diagnosis(
                db,
                tenant_id=patient.tenant_id,
                patient_id=patient.id,
                primary_diagnosis=previous_primary.icd10_code,
                source="RN_ICA",
                updated_by=user_id,
            )

            # If diagnosis rows support admission_id, attach the latest primary row to this admission.
            cls._attach_latest_primary_to_admission_if_supported(
                db=db,
                patient=patient,
                new_admission=new_admission,
            )

            return DxDecisionResult(
                success=True,
                status="primary_confirmed_same_as_previous",
                message="Primary diagnosis confirmed from previous admission.",
                previous_primary={
                    "id": str(previous_primary.id) if previous_primary.id else None,
                    "icd10_code": previous_primary.icd10_code,
                    "display_name": previous_primary.display_name,
                    "diagnosis_description": previous_primary.diagnosis_description,
                },
                new_primary={
                    "primary_diagnosis": sync_result.get("primary_diagnosis"),
                },
                actions=["confirmed_previous_primary"],
            )

        # Different primary:
        # 1) create/sync new primary from RN choice
        sync_result = sync_official_primary_diagnosis(
            db,
            tenant_id=patient.tenant_id,
            patient_id=patient.id,
            primary_diagnosis=primary_diagnosis,
            source="RN_ICA",
            updated_by=user_id,
        )

        cls._attach_latest_primary_to_admission_if_supported(
            db=db,
            patient=patient,
            new_admission=new_admission,
        )

        actions = ["created_new_primary"]

        # 2) Move old primary into SECONDARY on the new admission if there was one
        if previous_primary and previous_primary.icd10_code:
            cls._clone_previous_primary_as_secondary(
                db=db,
                patient=patient,
                new_admission=new_admission,
                previous_primary=previous_primary,
                user_id=user_id,
            )
            actions.append("previous_primary_moved_to_secondary")

        db.flush()

        return DxDecisionResult(
            success=True,
            status="primary_changed",
            message="New primary diagnosis selected; previous primary was carried forward as secondary.",
            previous_primary=(
                {
                    "id": str(previous_primary.id) if previous_primary and previous_primary.id else None,
                    "icd10_code": previous_primary.icd10_code if previous_primary else None,
                    "display_name": previous_primary.display_name if previous_primary else None,
                    "diagnosis_description": previous_primary.diagnosis_description if previous_primary else None,
                }
                if previous_primary
                else None
            ),
            new_primary={
                "primary_diagnosis": sync_result.get("primary_diagnosis"),
            },
            actions=actions,
        )

    # -----------------------------------------------------
    # INTERNAL HELPERS
    # -----------------------------------------------------
    @classmethod
    def _get_previous_admission(
        cls,
        *,
        db: Session,
        patient: Patient,
        new_admission: Admission,
    ) -> Optional[Admission]:
        return (
            db.query(Admission)
            .filter(
                Admission.tenant_id == patient.tenant_id,
                Admission.patient_id == patient.id,
                Admission.id != new_admission.id,
            )
            .order_by(Admission.created_at.desc())
            .first()
        )

    @classmethod
    def _get_previous_primary(
        cls,
        *,
        db: Session,
        patient: Patient,
        previous_admission: Optional[Admission],
    ) -> Optional[PreviousPrimaryDiagnosis]:
        if not previous_admission:
            return None

        query = (
            db.query(PatientDiagnosis)
            .filter(
                PatientDiagnosis.tenant_id == patient.tenant_id,
                PatientDiagnosis.patient_id == patient.id,
                PatientDiagnosis.diagnosis_type == DiagnosisType.PRIMARY,
                PatientDiagnosis.status == DiagnosisStatus.ACTIVE,
                PatientDiagnosis.active.is_(True),
            )
            .order_by(PatientDiagnosis.created_at.desc())
        )

        if hasattr(PatientDiagnosis, "admission_id"):
            query = query.filter(PatientDiagnosis.admission_id == previous_admission.id)

        row = query.first()
        if not row:
            return None

        return PreviousPrimaryDiagnosis(
            id=getattr(row, "id", None),
            icd10_code=getattr(row, "icd10_code", None),
            display_name=getattr(row, "display_name", None),
            diagnosis_description=getattr(row, "diagnosis_description", None),
            source=getattr(row, "source", None),
        )

    @classmethod
    def _load_previous_dx_rows(
        cls,
        *,
        db: Session,
        patient: Patient,
        previous_admission: Optional[Admission],
        diagnosis_type: DiagnosisType,
    ) -> list[PatientDiagnosis]:
        if not previous_admission:
            return []

        query = (
            db.query(PatientDiagnosis)
            .filter(
                PatientDiagnosis.tenant_id == patient.tenant_id,
                PatientDiagnosis.patient_id == patient.id,
                PatientDiagnosis.diagnosis_type == diagnosis_type,
                PatientDiagnosis.status == DiagnosisStatus.ACTIVE,
                PatientDiagnosis.active.is_(True),
            )
            .order_by(PatientDiagnosis.created_at.asc())
        )

        if hasattr(PatientDiagnosis, "admission_id"):
            query = query.filter(PatientDiagnosis.admission_id == previous_admission.id)

        return query.all()

    @classmethod
    def _get_previous_diagnoses_by_type(
        cls,
        *,
        db: Session,
        patient: Patient,
        previous_admission: Optional[Admission],
        diagnosis_type: DiagnosisType,
    ) -> list[dict[str, Any]]:
        rows = cls._load_previous_dx_rows(
            db=db,
            patient=patient,
            previous_admission=previous_admission,
            diagnosis_type=diagnosis_type,
        )

        return [
            {
                "id": str(row.id),
                "icd10_code": getattr(row, "icd10_code", None),
                "display_name": getattr(row, "display_name", None),
                "diagnosis_description": getattr(row, "diagnosis_description", None),
                "diagnosis_type": (
                    row.diagnosis_type.value
                    if hasattr(row.diagnosis_type, "value")
                    else str(row.diagnosis_type)
                ),
                "source": getattr(row, "source", None).value
                if hasattr(getattr(row, "source", None), "value")
                else str(getattr(row, "source", None))
                if getattr(row, "source", None) is not None
                else None,
            }
            for row in rows
        ]

    @classmethod
    def _diagnosis_already_exists_on_admission(
        cls,
        *,
        db: Session,
        new_admission: Admission,
        icd10_code: Optional[str],
        diagnosis_type: Any,
    ) -> bool:
        query = db.query(PatientDiagnosis).filter(
            PatientDiagnosis.tenant_id == new_admission.tenant_id,
            PatientDiagnosis.patient_id == new_admission.patient_id,
            PatientDiagnosis.icd10_code == icd10_code,
            PatientDiagnosis.diagnosis_type == diagnosis_type,
            PatientDiagnosis.status == DiagnosisStatus.ACTIVE,
            PatientDiagnosis.active.is_(True),
        )

        if hasattr(PatientDiagnosis, "admission_id"):
            query = query.filter(PatientDiagnosis.admission_id == new_admission.id)

        return query.first() is not None

    @classmethod
    def _attach_latest_primary_to_admission_if_supported(
        cls,
        *,
        db: Session,
        patient: Patient,
        new_admission: Admission,
    ) -> None:
        if not hasattr(PatientDiagnosis, "admission_id"):
            return

        latest_primary = (
            db.query(PatientDiagnosis)
            .filter(
                PatientDiagnosis.tenant_id == patient.tenant_id,
                PatientDiagnosis.patient_id == patient.id,
                PatientDiagnosis.diagnosis_type == DiagnosisType.PRIMARY,
                PatientDiagnosis.status == DiagnosisStatus.ACTIVE,
                PatientDiagnosis.active.is_(True),
            )
            .order_by(PatientDiagnosis.created_at.desc())
            .first()
        )

        if latest_primary:
            latest_primary.admission_id = new_admission.id

    @classmethod
    def _clone_previous_primary_as_secondary(
        cls,
        *,
        db: Session,
        patient: Patient,
        new_admission: Admission,
        previous_primary: PreviousPrimaryDiagnosis,
        user_id: uuid.UUID,
    ) -> None:
        if cls._diagnosis_already_exists_on_admission(
            db=db,
            new_admission=new_admission,
            icd10_code=previous_primary.icd10_code,
            diagnosis_type=DiagnosisType.SECONDARY,
        ):
            return

        now = datetime.now(timezone.utc)

        row = PatientDiagnosis(
            id=uuid.uuid4(),
            tenant_id=patient.tenant_id,
            patient_id=patient.id,
            diagnosis_type=DiagnosisType.SECONDARY,
            status=DiagnosisStatus.ACTIVE,

            # ✅ FIX: source must never be null
            source=previous_primary.source,

            icd10_code=previous_primary.icd10_code,
            diagnosis_description=previous_primary.diagnosis_description,
            display_name=previous_primary.display_name,
            active=True,
            is_terminal=False,
            is_related_to_terminal=True,
            effective_date=now.date(),

            created_by=user_id,
            updated_by=user_id,
            updated_at=now,
        )

        if hasattr(row, "admission_id"):
            row.admission_id = new_admission.id

        if hasattr(row, "change_reason"):
            row.change_reason = "PREVIOUS_PRIMARY_MOVED_TO_SECONDARY"

        if hasattr(row, "notes"):
            row.notes = (
                f"Previous primary diagnosis carried forward as secondary for new admission {new_admission.id}."
            )

        db.add(row)

    # -----------------------------------------------------
    # OPTIONAL MODEL ADAPTERS
    # -----------------------------------------------------
    @classmethod
    def _load_previous_labs(
        cls,
        *,
        db: Session,
        patient: Patient,
        previous_admission: Optional[Admission],
    ) -> list[dict[str, Any]]:
        model = cls._try_load_model(
            [
                ("app.models.lab_result", "LabResult"),
                ("app.models.patient_lab", "PatientLab"),
                ("app.models.lab", "Lab"),
            ]
        )

        if not model or not previous_admission:
            return []

        query = db.query(model).filter(
            getattr(model, "tenant_id") == patient.tenant_id,
            getattr(model, "patient_id") == patient.id,
        )

        if hasattr(model, "admission_id"):
            query = query.filter(getattr(model, "admission_id") == previous_admission.id)

        rows = query.order_by(getattr(model, "created_at").desc()).all() if hasattr(model, "created_at") else query.all()

        results = []
        for row in rows:
            results.append(
                {
                    "id": str(getattr(row, "id", "")),
                    "name": getattr(row, "name", None) or getattr(row, "test_name", None),
                    "value": getattr(row, "value", None) or getattr(row, "result_value", None),
                    "unit": getattr(row, "unit", None),
                    "source": "PREVIOUS",
                }
            )
        return results

    @classmethod
    def _load_previous_hnp(
        cls,
        *,
        db: Session,
        patient: Patient,
        previous_admission: Optional[Admission],
    ) -> Optional[dict[str, Any]]:
        if not previous_admission:
            return None

        from app.models.clinical_note import ClinicalNote

        query = db.query(ClinicalNote).filter(
            ClinicalNote.tenant_id == patient.tenant_id,
            ClinicalNote.patient_id == patient.id,
            ClinicalNote.note_type == "HNP",
        )

        if hasattr(ClinicalNote, "admission_id"):
            query = query.filter(ClinicalNote.admission_id == previous_admission.id)

        row = query.order_by(ClinicalNote.created_at.desc()).first()

        if not row:
            return None

        return {
            "id": str(row.id),
            "note_type": row.note_type,
            "encounter_date": str(getattr(row, "encounter_date", "")) if getattr(row, "encounter_date", None) else None,
            "source": "PREVIOUS",
            "content": getattr(row, "content", None),
        }

    @staticmethod
    def _try_load_model(candidates: list[tuple[str, str]]) -> Optional[Any]:
        for module_name, class_name in candidates:
            try:
                module = importlib.import_module(module_name)
                model = getattr(module, class_name, None)
                if model is not None:
                    return model
            except Exception:
                continue
        return None