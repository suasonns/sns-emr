from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import Mock, patch

from app.models.enums import (
    TaskDiscipline,
    TaskOrigin,
    TaskRegulatoryBasis,
    TaskStatus,
    TaskType,
)
from app.services.admission.admission_task_generation_service import (
    AdmissionTaskGenerationService,
    AdmissionTaskSpec,
)


def build_patient():
    return SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
    )


def build_spec(
    *,
    task_type="INITIAL_RN_ICA",
    alert_reason="Initial RN comprehensive assessment required",
    due_hours=0,
    discipline="RN",
    regulatory_basis="CONDITION_TRIGGER",
    origin="ADMISSION",
    condition=None,
    assigned_role="RN",
    priority="HIGH",
):
    return AdmissionTaskSpec(
        task_type=task_type,
        alert_reason=alert_reason,
        due_hours=due_hours,
        discipline=discipline,
        regulatory_basis=regulatory_basis,
        origin=origin,
        condition=condition,
        assigned_role=assigned_role,
        priority=priority,
    )


def test_condition_matches_no_condition():
    spec = build_spec()

    result = AdmissionTaskGenerationService._condition_matches(
        spec=spec,
        is_medicare=False,
        msw_ordered=False,
        sc_ordered=False,
        chha_ordered=False,
    )

    assert result is True


def test_condition_matches_medicare():
    spec = build_spec(
        task_type="NOE_DUE",
        condition="is_medicare",
    )

    result = AdmissionTaskGenerationService._condition_matches(
        spec=spec,
        is_medicare=True,
        msw_ordered=False,
        sc_ordered=False,
        chha_ordered=False,
    )

    assert result is True


def test_condition_does_not_match_medicare_when_false():
    spec = build_spec(
        task_type="NOE_DUE",
        condition="is_medicare",
    )

    result = AdmissionTaskGenerationService._condition_matches(
        spec=spec,
        is_medicare=False,
        msw_ordered=False,
        sc_ordered=False,
        chha_ordered=False,
    )

    assert result is False


def test_condition_matches_msw_ordered():
    spec = build_spec(
        task_type="INITIAL_MSW_ICA",
        discipline="MSW",
        condition="msw_ordered",
    )

    result = AdmissionTaskGenerationService._condition_matches(
        spec=spec,
        is_medicare=False,
        msw_ordered=True,
        sc_ordered=False,
        chha_ordered=False,
    )

    assert result is True


def test_condition_matches_sc_ordered():
    spec = build_spec(
        task_type="INITIAL_SC_ICA",
        discipline="SC",
        condition="sc_ordered",
    )

    result = AdmissionTaskGenerationService._condition_matches(
        spec=spec,
        is_medicare=False,
        msw_ordered=False,
        sc_ordered=True,
        chha_ordered=False,
    )

    assert result is True


def test_condition_matches_chha_ordered():
    spec = build_spec(
        task_type="OTHER",
        discipline="CHHA",
        condition="chha_ordered",
    )

    result = AdmissionTaskGenerationService._condition_matches(
        spec=spec,
        is_medicare=False,
        msw_ordered=False,
        sc_ordered=False,
        chha_ordered=True,
    )

    assert result is True


def test_condition_matches_rn_bereavement_required_when_msw_and_sc_refused():
    spec = build_spec(
        task_type="INITIAL_BEREAVEMENT",
        condition="rn_bereavement_required",
    )

    result = AdmissionTaskGenerationService._condition_matches(
        spec=spec,
        is_medicare=False,
        msw_ordered=False,
        sc_ordered=False,
        chha_ordered=False,
    )

    assert result is True


def test_condition_does_not_match_rn_bereavement_when_msw_ordered():
    spec = build_spec(
        task_type="INITIAL_BEREAVEMENT",
        condition="rn_bereavement_required",
    )

    result = AdmissionTaskGenerationService._condition_matches(
        spec=spec,
        is_medicare=False,
        msw_ordered=True,
        sc_ordered=False,
        chha_ordered=False,
    )

    assert result is False


def test_unknown_condition_returns_false():
    spec = build_spec(
        condition="unknown_condition",
    )

    result = AdmissionTaskGenerationService._condition_matches(
        spec=spec,
        is_medicare=False,
        msw_ordered=False,
        sc_ordered=False,
        chha_ordered=False,
    )

    assert result is False


def test_enum_member_resolves_task_type():
    result = AdmissionTaskGenerationService._enum_member(
        TaskType,
        "INITIAL_RN_ICA",
    )

    assert result == TaskType.INITIAL_RN_ICA


def test_enum_member_resolves_task_discipline():
    result = AdmissionTaskGenerationService._enum_member(
        TaskDiscipline,
        "RN",
    )

    assert result == TaskDiscipline.RN


def test_enum_member_rejects_invalid_value():
    try:
        AdmissionTaskGenerationService._enum_member(
            TaskType,
            "NOT_A_REAL_TASK_TYPE",
        )
    except ValueError as exc:
        assert "Invalid TaskType value" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for invalid TaskType"
        )


@patch.object(
    AdmissionTaskGenerationService,
    "create_task",
)
@patch.object(
    AdmissionTaskGenerationService,
    "task_exists",
)
def test_generate_transition_tasks_creates_tasks(
    mock_task_exists,
    mock_create_task,
):
    patient = build_patient()
    db = Mock()
    created_by = uuid4()

    mock_task_exists.return_value = False

    with patch.object(
        AdmissionTaskGenerationService,
        "get_specs_for_status",
        return_value=[
            build_spec(
                task_type="INITIAL_RN_ICA",
            ),
            build_spec(
                task_type="CERTIFICATION",
                discipline="MD",
                regulatory_basis="CERTIFICATION",
            ),
        ],
    ):
        result = AdmissionTaskGenerationService.generate_transition_tasks(
            db=db,
            patient=patient,
            previous_status="SOC_IN_PROGRESS",
            new_status="ADMITTED",
            created_by=created_by,
        )

    assert result["created_count"] == 2
    assert "INITIAL_RN_ICA" in result["created_tasks"]
    assert "CERTIFICATION" in result["created_tasks"]
    assert result["skipped_existing_tasks"] == []
    assert result["skipped_condition_tasks"] == []

    assert mock_create_task.call_count == 2


@patch.object(
    AdmissionTaskGenerationService,
    "create_task",
)
@patch.object(
    AdmissionTaskGenerationService,
    "task_exists",
)
def test_generate_transition_tasks_skips_existing_tasks(
    mock_task_exists,
    mock_create_task,
):
    patient = build_patient()
    db = Mock()
    created_by = uuid4()

    mock_task_exists.return_value = True

    with patch.object(
        AdmissionTaskGenerationService,
        "get_specs_for_status",
        return_value=[
            build_spec(
                task_type="INITIAL_RN_ICA",
            )
        ],
    ):
        result = AdmissionTaskGenerationService.generate_transition_tasks(
            db=db,
            patient=patient,
            previous_status="SOC_IN_PROGRESS",
            new_status="ADMITTED",
            created_by=created_by,
        )

    assert result["created_count"] == 0
    assert result["created_tasks"] == []
    assert result["skipped_existing_tasks"] == [
        "INITIAL_RN_ICA"
    ]

    mock_create_task.assert_not_called()


@patch.object(
    AdmissionTaskGenerationService,
    "create_task",
)
@patch.object(
    AdmissionTaskGenerationService,
    "task_exists",
)
def test_generate_transition_tasks_skips_condition_tasks(
    mock_task_exists,
    mock_create_task,
):
    patient = build_patient()
    db = Mock()
    created_by = uuid4()

    mock_task_exists.return_value = False

    with patch.object(
        AdmissionTaskGenerationService,
        "get_specs_for_status",
        return_value=[
            build_spec(
                task_type="NOE_DUE",
                condition="is_medicare",
            )
        ],
    ):
        result = AdmissionTaskGenerationService.generate_transition_tasks(
            db=db,
            patient=patient,
            previous_status="SOC_IN_PROGRESS",
            new_status="ADMITTED",
            created_by=created_by,
            is_medicare=False,
        )

    assert result["created_count"] == 0
    assert result["created_tasks"] == []
    assert result["skipped_condition_tasks"] == [
        "NOE_DUE"
    ]

    mock_create_task.assert_not_called()


@patch.object(
    AdmissionTaskGenerationService,
    "create_task",
)
@patch.object(
    AdmissionTaskGenerationService,
    "task_exists",
)
def test_generate_transition_tasks_creates_medicare_noe(
    mock_task_exists,
    mock_create_task,
):
    patient = build_patient()
    db = Mock()
    created_by = uuid4()

    mock_task_exists.return_value = False

    with patch.object(
        AdmissionTaskGenerationService,
        "get_specs_for_status",
        return_value=[
            build_spec(
                task_type="NOE_DUE",
                condition="is_medicare",
            )
        ],
    ):
        result = AdmissionTaskGenerationService.generate_transition_tasks(
            db=db,
            patient=patient,
            previous_status="SOC_IN_PROGRESS",
            new_status="ADMITTED",
            created_by=created_by,
            is_medicare=True,
        )

    assert result["created_count"] == 1
    assert result["created_tasks"] == [
        "NOE_DUE"
    ]

    mock_create_task.assert_called_once()


@patch.object(
    AdmissionTaskGenerationService,
    "create_task",
)
@patch.object(
    AdmissionTaskGenerationService,
    "task_exists",
)
def test_generate_transition_tasks_no_registry_for_status(
    mock_task_exists,
    mock_create_task,
):
    patient = build_patient()
    db = Mock()
    created_by = uuid4()

    with patch.object(
        AdmissionTaskGenerationService,
        "get_specs_for_status",
        return_value=[],
    ):
        result = AdmissionTaskGenerationService.generate_transition_tasks(
            db=db,
            patient=patient,
            previous_status="REFERRAL",
            new_status="UNKNOWN_STATUS",
            created_by=created_by,
        )

    assert result["created_count"] == 0
    assert result["created_tasks"] == []
    assert result["skipped_existing_tasks"] == []
    assert result["skipped_condition_tasks"] == []

    mock_task_exists.assert_not_called()
    mock_create_task.assert_not_called()


def test_create_task_adds_task_to_session():
    patient = build_patient()
    db = Mock()
    created_by = uuid4()

    spec = build_spec(
        task_type="INITIAL_RN_ICA",
        alert_reason="Initial RN comprehensive assessment required",
        due_hours=0,
        discipline="RN",
        regulatory_basis="CONDITION_TRIGGER",
        origin="ADMISSION",
    )

    task = AdmissionTaskGenerationService.create_task(
        db=db,
        patient=patient,
        spec=spec,
        created_by=created_by,
    )

    assert task.patient_id == patient.id
    assert task.tenant_id == patient.tenant_id
    assert task.alert_reason == spec.alert_reason
    assert task.created_by == created_by
    assert task.status == TaskStatus.PENDING
    assert task.origin == TaskOrigin.ADMISSION
    assert task.task_type == TaskType.INITIAL_RN_ICA
    assert task.discipline == TaskDiscipline.RN
    assert task.regulatory_basis == TaskRegulatoryBasis.CONDITION_TRIGGER

    db.add.assert_called_once_with(task)