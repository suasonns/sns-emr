from __future__ import annotations

"""
California Two-Hour In-Person Licensed-Nurse Response chain (issue #143;
Title 22 Section 74820/74848; DPH-18-002E-HospiceAgencies_Text.pdf).

Model chain:
  Patient -> BenefitPeriod (optional) -> PatientResponseEvent
    -> one or more NurseResponseAssignment rows (reassignment allowed,
       clock never restarts) -> InterimPatientSupport rows while waiting
    -> ResponseIntervention rows once the nurse arrives.

Clock: START = PatientResponseEvent.received_at,
       STOP  = NurseResponseAssignment.arrived_at (in-person arrival only).
Assignment, dispatch, acceptance, telephone/video contact, and IDG
notification never start or stop the clock.
"""

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class PatientResponseEvent(Base):
    """The patient medical-need or safety-concern report that starts the two-hour clock."""

    __tablename__ = "patient_response_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    admission_id = Column(UUID(as_uuid=True), ForeignKey("admissions.id", ondelete="SET NULL"), nullable=True, index=True)
    benefit_period_id = Column(
        UUID(as_uuid=True), ForeignKey("benefit_periods.id", ondelete="SET NULL"), nullable=True, index=True
    )

    event_type = Column(String(30), nullable=False, doc="MEDICAL_NEED / SAFETY_CONCERN")
    received_at = Column(
        DateTime(timezone=True),
        nullable=False,
        doc="The clock start. When the hospice received information of the medical need/safety concern -- never a later contact time.",
    )
    received_via = Column(String(40), nullable=True)
    reported_by_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)

    response_deadline_at = Column(
        DateTime(timezone=True),
        nullable=False,
        doc="received_at + 2 hours. Computed once at creation; never recalculated by reassignment.",
    )

    closed_at = Column(DateTime(timezone=True), nullable=True)
    closure_requires_patient_response = Column(Boolean, nullable=False, server_default="true")

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    patient = relationship("Patient")
    assignments = relationship(
        "NurseResponseAssignment", back_populates="patient_response_event", cascade="all, delete-orphan"
    )
    interim_support_records = relationship(
        "InterimPatientSupport", back_populates="patient_response_event", cascade="all, delete-orphan"
    )
    interventions = relationship(
        "ResponseIntervention", back_populates="patient_response_event", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_patient_response_events_tenant_deadline", "tenant_id", "response_deadline_at"),
        Index("ix_patient_response_events_tenant_patient", "tenant_id", "patient_id"),
        CheckConstraint(
            "event_type IN ('MEDICAL_NEED','SAFETY_CONCERN')",
            name="ck_patient_response_events_event_type",
        ),
    )


class NurseResponseAssignment(Base):
    """
    One nurse assignment for a PatientResponseEvent. Reassignment creates a
    new row; it must never reset response_deadline_at on the parent event
    or restart the clock.
    """

    __tablename__ = "nurse_response_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_response_event_id = Column(
        UUID(as_uuid=True), ForeignKey("patient_response_events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nurse_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    assigned_at = Column(DateTime(timezone=True), nullable=False)
    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    arrived_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="The clock stop. In-person arrival only -- never telephone/video contact or task completion.",
    )

    reassigned_from_assignment_id = Column(
        UUID(as_uuid=True), ForeignKey("nurse_response_assignments.id", ondelete="SET NULL"), nullable=True
    )
    reassignment_reason = Column(Text, nullable=True)

    is_late = Column(Boolean, nullable=True)
    variance_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    patient_response_event = relationship("PatientResponseEvent", back_populates="assignments")

    __table_args__ = (
        Index("ix_nurse_response_assignments_tenant_id", "tenant_id"),
        CheckConstraint(
            "reassigned_from_assignment_id IS NULL OR reassigned_from_assignment_id != id",
            name="ck_nurse_response_assignments_no_self_reassign",
        ),
        CheckConstraint(
            "is_late IS NULL OR is_late = false OR variance_reason IS NOT NULL",
            name="ck_nurse_response_assignments_late_requires_variance_reason",
        ),
    )


class InterimPatientSupport(Base):
    """Support maintained for the patient while awaiting in-person nurse arrival."""

    __tablename__ = "interim_patient_support"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_response_event_id = Column(
        UUID(as_uuid=True), ForeignKey("patient_response_events.id", ondelete="CASCADE"), nullable=False, index=True
    )

    support_type = Column(String(40), nullable=False, doc="TELEPHONE / VIDEO / CAREGIVER_COACHING / OTHER")
    provided_at = Column(DateTime(timezone=True), nullable=False)
    provided_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    patient_response_event = relationship("PatientResponseEvent", back_populates="interim_support_records")

    __table_args__ = (Index("ix_interim_patient_support_tenant_id", "tenant_id"),)


class ResponseIntervention(Base):
    """Assessment/intervention performed once the nurse arrives in person."""

    __tablename__ = "response_interventions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_response_event_id = Column(
        UUID(as_uuid=True), ForeignKey("patient_response_events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nurse_response_assignment_id = Column(
        UUID(as_uuid=True), ForeignKey("nurse_response_assignments.id", ondelete="SET NULL"), nullable=True
    )

    intervention_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    performed_at = Column(DateTime(timezone=True), nullable=False)
    performed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    patient_response_recorded_at = Column(DateTime(timezone=True), nullable=True)
    patient_response_summary = Column(Text, nullable=True)
    idg_notified_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    patient_response_event = relationship("PatientResponseEvent", back_populates="interventions")

    __table_args__ = (Index("ix_response_interventions_tenant_id", "tenant_id"),)


class PatientResponseAuditEvent(Base):
    """Domain audit trail for the two-hour response chain."""

    __tablename__ = "patient_response_audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_response_event_id = Column(
        UUID(as_uuid=True), ForeignKey("patient_response_events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    admission_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    event_type = Column(String(50), nullable=False, index=True)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    actor_account_discipline = Column(String(50), nullable=True)
    prior_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    reason = Column(Text, nullable=True)
    event_metadata = Column("metadata", JSONB, nullable=True)
    correlation_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    __table_args__ = (
        Index(
            "ix_patient_response_audit_events_tenant_event_created",
            "tenant_id",
            "event_type",
            "created_at",
        ),
        CheckConstraint(
            "event_type IN ("
            "'REQUIREMENT_CREATED','ASSIGNED','REASSIGNED','DISPATCHED','ARRIVED',"
            "'INTERIM_SUPPORT_RECORDED','ASSESSMENT_RECORDED','INTERVENTION_RECORDED',"
            "'PATIENT_RESPONSE_RECORDED','IDG_NOTIFIED','DEADLINE_MISSED',"
            "'RECORD_CORRECTED','RECORD_FINALIZED'"
            ")",
            name="ck_patient_response_audit_events_type",
        ),
    )
