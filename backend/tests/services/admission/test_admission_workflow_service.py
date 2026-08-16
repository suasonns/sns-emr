from types import SimpleNamespace
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import Mock, patch

from app.services.admission.admission_workflow_service import (
    AdmissionWorkflowService,
)


def build_patient(
    *,
    patient_id=None,
    admission_status="REFERRAL",
):
    return SimpleNamespace(
        id=patient_id or uuid4(),
        tenant_id=uuid4(),
        admission_status=admission_status,
    )


# =========================================================
# SUCCESSFUL STATUS CHANGE
# =========================================================

@patch(
    "app.services.admission.admission_workflow_service."
    "AdmissionStatusHistoryService"
)
@patch(
    "app.services.admission.admission_workflow_service."
    "AdmissionService"
)
def test_change_status_success(
    mock_admission_service,
    mock_history_service,
):
    patient = build_patient()

    db = Mock()

    mock_admission_service.validate_status_change.return_value = {
        "allowed": True,
        "blockers": [],
    }

    history_record = SimpleNamespace(
        id=uuid4(),
    )

    mock_history_service.update_patient_status.return_value = (
        history_record
    )

    result = AdmissionWorkflowService.change_status(
        db=db,
        patient=patient,
        new_status="POTENTIAL_ADMISSION",
        changed_by=uuid4(),
        role="ADMIN",
    )

    assert result["success"] is True
    assert result["status_changed"] is True

    db.commit.assert_called_once()


# =========================================================
# INVALID STATUS CHANGE
# =========================================================

@patch(
    "app.services.admission.admission_workflow_service."
    "AdmissionService"
)
def test_change_status_invalid_transition(
    mock_admission_service,
):
    patient = build_patient()

    db = Mock()

    mock_admission_service.validate_status_change.return_value = {
        "allowed": False,
        "reason": "Invalid transition",
        "blockers": [],
    }

    result = AdmissionWorkflowService.change_status(
        db=db,
        patient=patient,
        new_status="ADMITTED",
        changed_by=uuid4(),
        role="ADMIN",
    )

    assert result["success"] is False
    assert result["status_changed"] is False

    db.commit.assert_not_called()


# =========================================================
# BLOCKERS RETURNED
# =========================================================

@patch(
    "app.services.admission.admission_workflow_service."
    "AdmissionService"
)
def test_change_status_blocked_by_readiness(
    mock_admission_service,
):
    patient = build_patient(
        admission_status="SOC_IN_PROGRESS",
    )

    db = Mock()

    mock_admission_service.validate_status_change.return_value = {
        "allowed": False,
        "reason": "Admission blocked",
        "blockers": [
            "Primary diagnosis not established",
        ],
    }

    result = AdmissionWorkflowService.change_status(
        db=db,
        patient=patient,
        new_status="ADMITTED",
        changed_by=uuid4(),
        role="ADMIN",
    )

    assert result["success"] is False

    assert (
        "Primary diagnosis not established"
        in result["blockers"]
    )

    db.commit.assert_not_called()


# =========================================================
# NON ADMIT
# =========================================================

@patch(
    "app.services.admission.admission_workflow_service."
    "AdmissionWorkflowService.change_status"
)
def test_mark_non_admit(
    mock_change_status,
):
    patient = build_patient()

    db = Mock()

    mock_change_status.return_value = {
        "success": True,
    }

    result = AdmissionWorkflowService.mark_non_admit(
        db=db,
        patient=patient,
        changed_by=uuid4(),
        role="ADMIN",
        reason="Patient declined hospice",
    )

    assert result["success"] is True

    mock_change_status.assert_called_once()


# =========================================================
# START SOC
# =========================================================

@patch(
    "app.services.admission.admission_workflow_service."
    "AdmissionWorkflowService.change_status"
)
def test_start_soc(
    mock_change_status,
):
    patient = build_patient(
        admission_status="ADMISSION_SCHEDULED",
    )

    db = Mock()

    mock_change_status.return_value = {
        "success": True,
    }

    result = AdmissionWorkflowService.start_soc(
        db=db,
        patient=patient,
        changed_by=uuid4(),
        role="RN",
        soc_datetime=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
    )

    assert result["success"] is True

    _, kwargs = mock_change_status.call_args

    assert (
        kwargs["new_status"]
        == "SOC_IN_PROGRESS"
    )


# =========================================================
# COMPLETE ADMISSION
# =========================================================

@patch(
    "app.services.admission.admission_workflow_service."
    "AdmissionWorkflowService.change_status"
)
def test_complete_admission(
    mock_change_status,
):
    patient = build_patient(
        admission_status="SOC_IN_PROGRESS",
    )

    db = Mock()

    mock_change_status.return_value = {
        "success": True,
    }

    result = AdmissionWorkflowService.complete_admission(
        db=db,
        patient=patient,
        changed_by=uuid4(),
        role="RN",
        admit_datetime=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
    )

    assert result["success"] is True

    _, kwargs = mock_change_status.call_args

    assert (
        kwargs["new_status"]
        == "ADMITTED"
    )


# =========================================================
# SUMMARY
# =========================================================

@patch(
    "app.services.admission.admission_workflow_service."
    "AdmissionService"
)
def test_get_admission_summary(
    mock_admission_service,
):
    patient = build_patient()

    mock_admission_service.get_admission_summary.return_value = {
        "ready_for_soc": True,
        "blocker_count": 0,
        "blockers": [],
    }

    result = (
        AdmissionWorkflowService.get_admission_summary(
            patient=patient,
        )
    )

    assert result["ready_for_soc"] is True
    assert result["blocker_count"] == 0


# =========================================================
# VALIDATE ONLY
# =========================================================

@patch(
    "app.services.admission.admission_workflow_service."
    "AdmissionService"
)
def test_validate_status_change(
    mock_admission_service,
):
    patient = build_patient()

    mock_admission_service.validate_status_change.return_value = {
        "allowed": True,
        "reason": None,
    }

    result = (
        AdmissionWorkflowService.validate_status_change(
            patient=patient,
            new_status="POTENTIAL_ADMISSION",
            role="ADMIN",
        )
    )

    assert result["allowed"] is True