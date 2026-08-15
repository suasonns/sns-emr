from __future__ import annotations

import importlib
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.admission import Admission
from app.models.patient import Patient
from app.models.patient_diagnosis import PatientDiagnosis
from app.models.clinical_note import ClinicalNote
from app.models.enums import DiagnosisType, DiagnosisStatus


def clone_previous_admission(
    db: Session,
    *,
    patient_id: uuid.UUID,
    new_admission: Admission,
    user_id: uuid.UUID,
) -> dict[str, Any]:
    """
    Clone previous admission context into a new admission.

    RULES
    -----
    - Copy SECONDARY and COMORBIDITY diagnoses only
    - DO NOT copy PRIMARY diagnosis automatically
    - Store previous primary for RN review
    - Copy previous labs if a compatible lab model exists
    - Copy previous H&P if present
    - Mark copied content as historical / previous / review-required where supported
    """

    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id)
        .first()
    )
    if not patient:
        return {
            "status": "patient_not_found",
            "patient_id": str(patient_id),
        }

    previous_admission = (
        db.query(Admission)
        .filter(
            Admission.tenant_id == patient.tenant_id,
            Admission.patient_id == patient.id,
            Admission.id != new_admission.id,
        )
        .order_by(Admission.created_at.desc())
        .first()
    )

    if not previous_admission:
        return {
            "status": "no_previous_admission",
            "patient_id": str(patient.id),
            "new_admission_id": str(new_admission.id),
            "previous_admission_id": None,
            "cloned_secondary_count": 0,
            "cloned_comorbidity_count": 0,
            "cloned_lab_count": 0,
            "cloned_hnp_count": 0,
            "previous_primary_dx": None,
        }

    now = datetime.now(timezone.utc)

    # =========================================================
    # PREVIOUS DIAGNOSES
    # =========================================================
    previous_dx_query = (
        db.query(PatientDiagnosis)
        .filter(
            PatientDiagnosis.tenant_id == patient.tenant_id,
            PatientDiagnosis.patient_id == patient.id,
            PatientDiagnosis.status == DiagnosisStatus.ACTIVE,
            PatientDiagnosis.active.is_(True),
        )
    )

    # Only use admission_id if your diagnosis model supports it
    if hasattr(PatientDiagnosis, "admission_id"):
        previous_dx_query = previous_dx_query.filter(
            PatientDiagnosis.admission_id == previous_admission.id
        )

    previous_dx_rows = previous_dx_query.order_by(PatientDiagnosis.created_at.asc()).all()

    previous_primary_dx = None
    cloned_secondary_count = 0
    cloned_comorbidity_count = 0

    for dx in previous_dx_rows:
        dx_type = (
            dx.diagnosis_type.value
            if hasattr(dx.diagnosis_type, "value")
            else str(dx.diagnosis_type)
        )

        if dx_type == DiagnosisType.PRIMARY.value:
            previous_primary_dx = {
                "id": str(dx.id),
                "icd10_code": getattr(dx, "icd10_code", None),
                "display_name": getattr(dx, "display_name", None),
                "diagnosis_description": getattr(dx, "diagnosis_description", None),
            }
            continue

        if dx_type not in {
            DiagnosisType.SECONDARY.value,
            DiagnosisType.COMORBIDITY.value,
        }:
            continue

        # prevent duplicate cloning into new admission
        existing_query = (
            db.query(PatientDiagnosis)
            .filter(
                PatientDiagnosis.tenant_id == patient.tenant_id,
                PatientDiagnosis.patient_id == patient.id,
                PatientDiagnosis.status == DiagnosisStatus.ACTIVE,
                PatientDiagnosis.active.is_(True),
                PatientDiagnosis.icd10_code == getattr(dx, "icd10_code", None),
                PatientDiagnosis.diagnosis_type == dx.diagnosis_type,
            )
        )
        if hasattr(PatientDiagnosis, "admission_id"):
            existing_query = existing_query.filter(
                PatientDiagnosis.admission_id == new_admission.id
            )

        existing = existing_query.first()
        if existing:
            continue

        new_dx = PatientDiagnosis(
            id=uuid.uuid4(),
            tenant_id=patient.tenant_id,
            patient_id=patient.id,
            diagnosis_type=dx.diagnosis_type,
            status=DiagnosisStatus.ACTIVE,
            source=getattr(dx, "source", None),
            icd10_code=getattr(dx, "icd10_code", None),
            diagnosis_description=getattr(dx, "diagnosis_description", None),
            display_name=getattr(dx, "display_name", None),
            active=True,
            is_terminal=getattr(dx, "is_terminal", False),
            is_related_to_terminal=getattr(dx, "is_related_to_terminal", False),
            effective_date=getattr(dx, "effective_date", None),
            created_by=user_id,
        )

        if hasattr(new_dx, "admission_id"):
            new_dx.admission_id = new_admission.id

        if hasattr(new_dx, "change_reason"):
            new_dx.change_reason = "CLONED_FROM_PREVIOUS_ADMISSION"

        if hasattr(new_dx, "notes"):
            new_dx.notes = (
                f"Cloned from previous admission {previous_admission.id} "
                f"into new admission {new_admission.id} for review."
            )

        db.add(new_dx)

        if dx_type == DiagnosisType.SECONDARY.value:
            cloned_secondary_count += 1
        elif dx_type == DiagnosisType.COMORBIDITY.value:
            cloned_comorbidity_count += 1

    # =========================================================
    # PREVIOUS LABS (OPTIONAL / ADAPTER-BASED)
    # =========================================================
    cloned_lab_count = 0

    lab_model = _try_load_model(
        [
            ("app.models.lab_result", "LabResult"),
            ("app.models.patient_lab", "PatientLab"),
            ("app.models.lab", "Lab"),
        ]
    )

    if lab_model is not None:
        previous_lab_query = (
            db.query(lab_model)
            .filter(
                getattr(lab_model, "tenant_id") == patient.tenant_id,
                getattr(lab_model, "patient_id") == patient.id,
            )
        )

        if hasattr(lab_model, "admission_id"):
            previous_lab_query = previous_lab_query.filter(
                getattr(lab_model, "admission_id") == previous_admission.id
            )

        previous_labs = previous_lab_query.all()

        for lab in previous_labs:
            # Build a cloned row only using fields that actually exist on the target model
            kwargs: dict[str, Any] = {}

            if hasattr(lab_model, "id"):
                kwargs["id"] = uuid.uuid4()
            if hasattr(lab_model, "tenant_id"):
                kwargs["tenant_id"] = patient.tenant_id
            if hasattr(lab_model, "patient_id"):
                kwargs["patient_id"] = patient.id
            if hasattr(lab_model, "admission_id"):
                kwargs["admission_id"] = new_admission.id
            if hasattr(lab_model, "name"):
                kwargs["name"] = getattr(lab, "name", None)
            if hasattr(lab_model, "test_name"):
                kwargs["test_name"] = getattr(lab, "test_name", None)
            if hasattr(lab_model, "value"):
                kwargs["value"] = getattr(lab, "value", None)
            if hasattr(lab_model, "result_value"):
                kwargs["result_value"] = getattr(lab, "result_value", None)
            if hasattr(lab_model, "unit"):
                kwargs["unit"] = getattr(lab, "unit", None)
            if hasattr(lab_model, "source"):
                kwargs["source"] = "PREVIOUS"
            if hasattr(lab_model, "is_current"):
                kwargs["is_current"] = False
            if hasattr(lab_model, "requires_review"):
                kwargs["requires_review"] = True
            if hasattr(lab_model, "created_at"):
                kwargs["created_at"] = now
            if hasattr(lab_model, "updated_at"):
                kwargs["updated_at"] = now
            if hasattr(lab_model, "created_by"):
                kwargs["created_by"] = user_id

            try:
                cloned_lab = lab_model(**kwargs)
                db.add(cloned_lab)
                cloned_lab_count += 1
            except Exception:
                # keep cloning safe even if the lab model shape differs
                continue

    # =========================================================
    # PREVIOUS H&P (OPTIONAL)
    # =========================================================
    cloned_hnp_count = 0

    previous_hnp_query = db.query(ClinicalNote).filter(
        ClinicalNote.tenant_id == patient.tenant_id,
        ClinicalNote.patient_id == patient.id,
        ClinicalNote.note_type == "HNP",
    )

    if hasattr(ClinicalNote, "admission_id"):
        previous_hnp_query = previous_hnp_query.filter(
            ClinicalNote.admission_id == previous_admission.id
        )

    previous_hnp = previous_hnp_query.order_by(ClinicalNote.created_at.desc()).first()

    if previous_hnp:
        new_hnp = ClinicalNote(
            id=uuid.uuid4(),
            tenant_id=patient.tenant_id,
            patient_id=patient.id,
            note_type="HNP",
            discipline=getattr(previous_hnp, "discipline", None),
            form_family=getattr(previous_hnp, "form_family", None),
            status="DRAFT",
            encounter_date=now.date(),
            content=getattr(previous_hnp, "content", None),
            created_by=user_id,
            created_at=now,
            updated_at=now,
        )

        if hasattr(new_hnp, "admission_id"):
            new_hnp.admission_id = new_admission.id
        if hasattr(new_hnp, "source"):
            new_hnp.source = "PREVIOUS"
        if hasattr(new_hnp, "requires_review"):
            new_hnp.requires_review = True

        db.add(new_hnp)
        cloned_hnp_count += 1

    db.flush()

    return {
        "status": "cloned",
        "patient_id": str(patient.id),
        "new_admission_id": str(new_admission.id),
        "previous_admission_id": str(previous_admission.id),
        "cloned_secondary_count": cloned_secondary_count,
        "cloned_comorbidity_count": cloned_comorbidity_count,
        "cloned_lab_count": cloned_lab_count,
        "cloned_hnp_count": cloned_hnp_count,
        "previous_primary_dx": previous_primary_dx,
    }


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
