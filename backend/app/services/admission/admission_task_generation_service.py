from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.task import Task
from app.models.enums import (
    TaskDiscipline,
    TaskOrigin,
    TaskRegulatoryBasis,
    TaskStatus,
    TaskType,
)


@dataclass(frozen=True)
class AdmissionTaskSpec:
    task_type: str
    alert_reason: str
    due_hours: int
    discipline: str
    regulatory_basis: Optional[str]
    origin: str
    condition: Optional[str] = None
    assigned_role: Optional[str] = None
    priority: Optional[str] = None


class AdmissionTaskGenerationService:
    """
    Admission Task Generation Service.

    Purpose:
    - Generate admission-related tasks from admission status transitions.
    - Prevent duplicate task creation.
    - Use only DB-backed enum-safe task values.
    - Load workflow rules from admission_task_registry.json.
    - Keep API routes and workflow services from directly creating tasks.

    This service does not commit.
    The caller controls transaction boundaries.
    """

    REGISTRY_PATH = (
        Path(__file__).resolve().parents[2]
        / "config"
        / "admission_task_registry.json"
    )

    _registry_cache: Optional[Dict[str, Any]] = None

    @classmethod
    def generate_transition_tasks(
        cls,
        *,
        db: Session,
        patient: Patient,
        previous_status: str,
        new_status: str,
        created_by: UUID,
        is_medicare: bool = False,
        msw_ordered: bool = False,
        sc_ordered: bool = False,
        chha_ordered: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate tasks for a completed admission status transition.

        This method is idempotent.
        Existing tasks are not duplicated.
        """

        specs = cls.get_specs_for_status(
            new_status=new_status,
        )

        created_tasks: List[str] = []
        skipped_existing_tasks: List[str] = []
        skipped_condition_tasks: List[str] = []

        for spec in specs:
            if not cls._condition_matches(
                spec=spec,
                is_medicare=is_medicare,
                msw_ordered=msw_ordered,
                sc_ordered=sc_ordered,
                chha_ordered=chha_ordered,
            ):
                skipped_condition_tasks.append(
                    spec.task_type
                )
                continue

            if cls.task_exists(
                db=db,
                patient=patient,
                task_type=spec.task_type,
            ):
                skipped_existing_tasks.append(
                    spec.task_type
                )
                continue

            cls.create_task(
                db=db,
                patient=patient,
                spec=spec,
                created_by=created_by,
            )

            created_tasks.append(
                spec.task_type
            )

        return {
            "previous_status": previous_status,
            "new_status": new_status,
            "created_tasks": created_tasks,
            "skipped_existing_tasks": skipped_existing_tasks,
            "skipped_condition_tasks": skipped_condition_tasks,
            "created_count": len(created_tasks),
        }

    @classmethod
    def get_specs_for_status(
        cls,
        *,
        new_status: str,
    ) -> List[AdmissionTaskSpec]:
        """
        Load task specs for a target admission status.
        """

        registry = cls.load_registry()

        status_rules = registry.get(
            "status_task_rules",
            {},
        )

        raw_specs = status_rules.get(
            new_status,
            [],
        )

        return [
            AdmissionTaskSpec(
                task_type=item["task_type"],
                alert_reason=item["alert_reason"],
                due_hours=item["due_hours"],
                discipline=item["discipline"],
                regulatory_basis=item.get("regulatory_basis"),
                origin=item["origin"],
                condition=item.get("condition"),
                assigned_role=item.get("assigned_role"),
                priority=item.get("priority"),
            )
            for item in raw_specs
        ]

    @classmethod
    def create_task(
        cls,
        *,
        db: Session,
        patient: Patient,
        spec: AdmissionTaskSpec,
        created_by: UUID,
    ) -> Task:
        """
        Create one admission task.
        """

        now = datetime.now(timezone.utc)

        task = Task(
            id=uuid4(),
            tenant_id=patient.tenant_id,
            patient_id=patient.id,
            task_type=cls._enum_member(
                TaskType,
                spec.task_type,
            ),
            alert_reason=spec.alert_reason,
            status=TaskStatus.PENDING,
            origin=cls._enum_member(
                TaskOrigin,
                spec.origin,
            ),
            discipline=cls._enum_member(
                TaskDiscipline,
                spec.discipline,
            ),
            regulatory_basis=(
                cls._enum_member(
                    TaskRegulatoryBasis,
                    spec.regulatory_basis,
                )
                if spec.regulatory_basis
                else None
            ),
            priority=spec.priority,
            assigned_role=spec.assigned_role,
            notification_required=True,
            created_at=now,
            due_at=now + timedelta(
                hours=spec.due_hours,
            ),
            created_by=created_by,
        )

        db.add(task)

        return task

    @classmethod
    def task_exists(
        cls,
        *,
        db: Session,
        patient: Patient,
        task_type: str,
    ) -> bool:
        """
        Prevent duplicate admission task creation.
        """

        resolved_task_type = cls._enum_member(
            TaskType,
            task_type,
        )

        existing = (
            db.query(Task)
            .filter(
                Task.tenant_id == patient.tenant_id,
                Task.patient_id == patient.id,
                Task.task_type == resolved_task_type,
            )
            .first()
        )

        return existing is not None

    @classmethod
    def load_registry(
        cls,
    ) -> Dict[str, Any]:
        """
        Load admission task registry from JSON.

        Cached after first load.
        """

        if cls._registry_cache is not None:
            return cls._registry_cache

        if not cls.REGISTRY_PATH.exists():
            raise FileNotFoundError(
                f"Admission task registry not found: "
                f"{cls.REGISTRY_PATH}"
            )

        with cls.REGISTRY_PATH.open(
            "r",
            encoding="utf-8",
        ) as file:
            cls._registry_cache = json.load(file)

        return cls._registry_cache

    @classmethod
    def clear_registry_cache(
        cls,
    ) -> None:
        """
        Clear registry cache.

        Used by tests or hot reload workflows.
        """

        cls._registry_cache = None

    @staticmethod
    def _condition_matches(
        *,
        spec: AdmissionTaskSpec,
        is_medicare: bool,
        msw_ordered: bool,
        sc_ordered: bool,
        chha_ordered: bool,
    ) -> bool:
        """
        Evaluate conditional task rules.
        """

        if spec.condition is None:
            return True

        if spec.condition == "is_medicare":
            return is_medicare

        if spec.condition == "msw_ordered":
            return msw_ordered

        if spec.condition == "sc_ordered":
            return sc_ordered

        if spec.condition == "chha_ordered":
            return chha_ordered

        if spec.condition == "rn_bereavement_required":
            return not msw_ordered and not sc_ordered

        return False

    @staticmethod
    def _enum_member(
        enum_class,
        value: str,
    ):
        """
        Resolve a required enum member.

        This is intentionally strict.
        Unknown enum values should fail fast because
        PostgreSQL-backed enums must match DB exactly.
        """

        try:
            return enum_class(value)
        except ValueError as exc:
            raise ValueError(
                f"Invalid {enum_class.__name__} value: {value}"
            ) from exc