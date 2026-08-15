# models/poc_physician_approval.py

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


PHYSICIAN_ATTESTATION_TEXT = """
I have reviewed the patient's clinical status,
hospice eligibility information, current problems,
goals, interventions, medications, and the Plan of Care.

I certify that the Plan of Care is appropriate for
the patient's current condition and hospice needs.

I approve this Plan of Care and authorize its
continued implementation and ongoing interdisciplinary
management.

Electronic signature or submission of a signed
approval document constitutes physician attestation
and approval of this Plan of Care version.
""".strip()


PHYSICIAN_ATTESTATION_VERSION = "POC_PHYSICIAN_ATTESTATION_V1"


class PocPhysicianApproval(Base):
    __tablename__ = "poc_physician_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    poc_version_id = Column(UUID(as_uuid=True), nullable=False)

    physician_user_id = Column(UUID(as_uuid=True), nullable=True)
    physician_name = Column(String(255), nullable=False)
    physician_role = Column(String(100), nullable=False)

    approval_method = Column(String(50), nullable=False)

    approval_status = Column(
        String(50),
        nullable=False,
        server_default=text("'PENDING_PHYSICIAN_SIGNATURE'"),
    )

    approval_date = Column(Date, nullable=True)

    attestation_text = Column(
        Text,
        nullable=False,
        default=PHYSICIAN_ATTESTATION_TEXT,
    )

    attestation_version = Column(
        String(100),
        nullable=False,
        default=PHYSICIAN_ATTESTATION_VERSION,
        server_default=text("'POC_PHYSICIAN_ATTESTATION_V1'"),
    )

    electronic_signature_text = Column(String(255), nullable=True)
    electronically_signed_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    system_authenticated_at = Column(DateTime(timezone=True), nullable=True)

    approval_due_date = Column(Date, nullable=True)

    reminder_sent_at = Column(DateTime(timezone=True), nullable=True)
    compliance_warning_at = Column(DateTime(timezone=True), nullable=True)
    high_priority_alert_at = Column(DateTime(timezone=True), nullable=True)

    is_overdue = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    escalation_level = Column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    rejection_reason = Column(Text, nullable=True)
    rejected_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)

    rescission_reason = Column(Text, nullable=True)
    rescinded_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    rescinded_at = Column(DateTime(timezone=True), nullable=True)

    is_voided = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    void_reason = Column(Text, nullable=True)
    voided_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    voided_at = Column(DateTime(timezone=True), nullable=True)

    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    updated_by_user_id = Column(UUID(as_uuid=True), nullable=True)

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=func.now(),
    )

    documents = relationship(
        "PocPhysicianApprovalDocument",
        back_populates="approval",
        cascade="save-update, merge",
        passive_deletes=True,
    )

    audit_events = relationship(
        "PocPhysicianApprovalAuditEvent",
        back_populates="approval",
        cascade="save-update, merge",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint(
            """
            physician_role IN (
                'HOSPICE_MEDICAL_DIRECTOR',
                'ASSOCIATE_MEDICAL_DIRECTOR',
                'MEDICAL_DIRECTOR_DESIGNEE',
                'ATTENDING_PHYSICIAN'
            )
            """,
            name="ck_poc_physician_approvals_physician_role",
        ),
        CheckConstraint(
            """
            approval_method IN (
                'ELECTRONIC_SIGNATURE',
                'UPLOADED_SIGNED_APPROVAL_DOCUMENT'
            )
            """,
            name="ck_poc_physician_approvals_approval_method",
        ),
        CheckConstraint(
            """
            approval_status IN (
                'PENDING_PHYSICIAN_SIGNATURE',
                'PHYSICIAN_APPROVED',
                'PHYSICIAN_REJECTED',
                'APPROVAL_RESCINDED',
                'VOIDED'
            )
            """,
            name="ck_poc_physician_approvals_approval_status",
        ),
        CheckConstraint(
            "escalation_level IN (0, 1, 2, 3)",
            name="ck_poc_physician_approvals_escalation_level",
        ),
        CheckConstraint(
            """
            approval_status != 'PHYSICIAN_APPROVED'
            OR
            approval_date IS NOT NULL
            """,
            name="ck_poc_physician_approvals_approved_requires_approval_date",
        ),
        CheckConstraint(
            """
            approval_status != 'PHYSICIAN_APPROVED'
            OR
            attestation_text IS NOT NULL
            """,
            name="ck_poc_physician_approvals_approved_requires_attestation_text",
        ),
        CheckConstraint(
            """
            approval_status != 'PHYSICIAN_APPROVED'
            OR
            attestation_version IS NOT NULL
            """,
            name="ck_poc_physician_approvals_approved_requires_attestation_version",
        ),
        CheckConstraint(
            """
            approval_method != 'ELECTRONIC_SIGNATURE'
            OR
            approval_status != 'PHYSICIAN_APPROVED'
            OR
            (
                electronic_signature_text IS NOT NULL
                AND electronically_signed_by_user_id IS NOT NULL
                AND system_authenticated_at IS NOT NULL
            )
            """,
            name="ck_poc_physician_approvals_e_signature_requires_authentication",
        ),
        CheckConstraint(
            """
            approval_status != 'PHYSICIAN_REJECTED'
            OR
            (
                rejection_reason IS NOT NULL
                AND rejected_at IS NOT NULL
            )
            """,
            name="ck_poc_physician_approvals_rejection_requires_reason",
        ),
        CheckConstraint(
            """
            approval_status != 'APPROVAL_RESCINDED'
            OR
            (
                rescission_reason IS NOT NULL
                AND rescinded_at IS NOT NULL
            )
            """,
            name="ck_poc_physician_approvals_rescission_requires_reason",
        ),
        CheckConstraint(
            """
            is_voided = FALSE
            OR
            (
                is_voided = TRUE
                AND approval_status = 'VOIDED'
                AND void_reason IS NOT NULL
                AND voided_at IS NOT NULL
            )
            """,
            name="ck_poc_physician_approvals_void_requires_reason",
        ),
        CheckConstraint(
            """
            approval_status != 'VOIDED'
            OR
            is_voided = TRUE
            """,
            name="ck_poc_physician_approvals_void_status_requires_is_voided",
        ),
        CheckConstraint(
            """
            reminder_sent_at IS NULL
            OR
            approval_due_date IS NOT NULL
            """,
            name="ck_poc_physician_approvals_reminder_requires_due_date",
        ),
        CheckConstraint(
            """
            compliance_warning_at IS NULL
            OR
            approval_due_date IS NOT NULL
            """,
            name="ck_poc_physician_approvals_warning_requires_due_date",
        ),
        CheckConstraint(
            """
            high_priority_alert_at IS NULL
            OR
            approval_due_date IS NOT NULL
            """,
            name="ck_poc_physician_approvals_high_alert_requires_due_date",
        ),
        Index(
            "ix_poc_physician_approvals_tenant_id",
            "tenant_id",
        ),
        Index(
            "ix_poc_physician_approvals_patient_id",
            "patient_id",
        ),
        Index(
            "ix_poc_physician_approvals_poc_version_id",
            "poc_version_id",
        ),
        Index(
            "ix_poc_physician_approvals_status",
            "approval_status",
        ),
        Index(
            "ix_poc_physician_approvals_due_date",
            "approval_due_date",
        ),
        Index(
            "ix_poc_physician_approvals_overdue",
            "is_overdue",
        ),
        Index(
            "ix_poc_physician_approvals_escalation_level",
            "escalation_level",
        ),
        Index(
            "ix_poc_physician_approvals_tenant_status",
            "tenant_id",
            "approval_status",
        ),
        Index(
            "ix_poc_physician_approvals_tenant_overdue_escalation",
            "tenant_id",
            "is_overdue",
            "escalation_level",
        ),
        Index(
            "ix_poc_physician_approvals_tenant_patient_version",
            "tenant_id",
            "patient_id",
            "poc_version_id",
        ),
        Index(
            "ux_poc_physician_approvals_one_active_per_poc_version",
            "tenant_id",
            "poc_version_id",
            unique=True,
            postgresql_where=text("is_voided = FALSE"),
        ),
    )


class PocPhysicianApprovalDocument(Base):
    __tablename__ = "poc_physician_approval_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), nullable=False)

    poc_physician_approval_id = Column(
        UUID(as_uuid=True),
        ForeignKey("poc_physician_approvals.id", ondelete="RESTRICT"),
        nullable=False,
    )

    patient_id = Column(UUID(as_uuid=True), nullable=False)
    poc_version_id = Column(UUID(as_uuid=True), nullable=False)

    document_file_name = Column(String(500), nullable=False)
    document_file_type = Column(String(100), nullable=False)
    document_storage_key = Column(Text, nullable=False)
    document_sha256_hash = Column(String(128), nullable=True)

    document_source = Column(
        String(100),
        nullable=False,
        server_default=text("'UPLOADED_SIGNED_APPROVAL_DOCUMENT'"),
    )

    uploaded_by_user_id = Column(UUID(as_uuid=True), nullable=False)
    uploaded_by_name = Column(String(255), nullable=False)
    uploaded_by_role = Column(String(100), nullable=False)

    uploaded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    indexed_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    indexed_at = Column(DateTime(timezone=True), nullable=True)

    classified_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    classified_at = Column(DateTime(timezone=True), nullable=True)

    replaces_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("poc_physician_approval_documents.id", ondelete="RESTRICT"),
        nullable=True,
    )

    replacement_reason = Column(Text, nullable=True)

    is_voided = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    void_reason = Column(Text, nullable=True)
    voided_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    voided_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=func.now(),
    )

    approval = relationship(
        "PocPhysicianApproval",
        back_populates="documents",
    )

    replaced_document = relationship(
        "PocPhysicianApprovalDocument",
        remote_side=[id],
        uselist=False,
    )

    __table_args__ = (
        CheckConstraint(
            """
            document_file_type IN (
                'PDF',
                'SCANNED_SIGNED_FORM',
                'IMAGE_FILE'
            )
            """,
            name="ck_poc_physician_approval_documents_file_type",
        ),
        CheckConstraint(
            """
            uploaded_by_role IN (
                'RN',
                'CLINICAL_MANAGER',
                'DPCS',
                'QA',
                'MEDICAL_RECORDS_HIM',
                'AUTHORIZED_ADMINISTRATIVE_STAFF'
            )
            """,
            name="ck_poc_physician_approval_documents_uploaded_by_role",
        ),
        CheckConstraint(
            """
            document_source IN (
                'UPLOADED_SIGNED_APPROVAL_DOCUMENT'
            )
            """,
            name="ck_poc_physician_approval_documents_source",
        ),
        CheckConstraint(
            """
            document_sha256_hash IS NULL
            OR
            length(document_sha256_hash) = 64
            """,
            name="ck_poc_physician_approval_documents_sha256_length",
        ),
        CheckConstraint(
            """
            indexed_at IS NULL
            OR
            indexed_by_user_id IS NOT NULL
            """,
            name="ck_poc_physician_approval_documents_indexed_requires_user",
        ),
        CheckConstraint(
            """
            classified_at IS NULL
            OR
            classified_by_user_id IS NOT NULL
            """,
            name="ck_poc_physician_approval_documents_classified_requires_user",
        ),
        CheckConstraint(
            """
            replaces_document_id IS NULL
            OR
            (
                replaces_document_id IS NOT NULL
                AND replacement_reason IS NOT NULL
            )
            """,
            name="ck_poc_physician_approval_documents_replacement_requires_reason",
        ),
        CheckConstraint(
            """
            is_voided = FALSE
            OR
            (
                is_voided = TRUE
                AND void_reason IS NOT NULL
                AND voided_at IS NOT NULL
            )
            """,
            name="ck_poc_physician_approval_documents_void_requires_reason",
        ),
        Index(
            "ix_poc_physician_approval_documents_tenant_id",
            "tenant_id",
        ),
        Index(
            "ix_poc_physician_approval_documents_approval_id",
            "poc_physician_approval_id",
        ),
        Index(
            "ix_poc_physician_approval_documents_patient_id",
            "patient_id",
        ),
        Index(
            "ix_poc_physician_approval_documents_poc_version_id",
            "poc_version_id",
        ),
        Index(
            "ix_poc_physician_approval_documents_uploaded_by",
            "uploaded_by_user_id",
        ),
        Index(
            "ix_poc_physician_approval_documents_uploaded_at",
            "uploaded_at",
        ),
        Index(
            "ix_poc_physician_approval_documents_tenant_patient_version",
            "tenant_id",
            "patient_id",
            "poc_version_id",
        ),
        Index(
            "ix_poc_physician_approval_documents_hash",
            "document_sha256_hash",
        ),
        Index(
            "ux_poc_physician_approval_documents_one_active_per_approval",
            "tenant_id",
            "poc_physician_approval_id",
            unique=True,
            postgresql_where=text("is_voided = FALSE"),
        ),
    )


class PocPhysicianApprovalAuditEvent(Base):
    __tablename__ = "poc_physician_approval_audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), nullable=False)

    poc_physician_approval_id = Column(
        UUID(as_uuid=True),
        ForeignKey("poc_physician_approvals.id", ondelete="RESTRICT"),
        nullable=False,
    )

    patient_id = Column(UUID(as_uuid=True), nullable=False)
    poc_version_id = Column(UUID(as_uuid=True), nullable=False)

    event_type = Column(String(100), nullable=False)
    event_description = Column(Text, nullable=False)

    performed_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    performed_by_name = Column(String(255), nullable=True)
    performed_by_role = Column(String(100), nullable=True)

    event_metadata = Column(JSONB, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    approval = relationship(
        "PocPhysicianApproval",
        back_populates="audit_events",
    )

    __table_args__ = (
        CheckConstraint(
            """
            event_type IN (
                'APPROVAL_RECORD_CREATED',
                'PHYSICIAN_ATTESTATION_RECORDED',
                'ELECTRONIC_SIGNATURE_COMPLETED',
                'SIGNED_DOCUMENT_UPLOADED',
                'DOCUMENT_INDEXED',
                'DOCUMENT_CLASSIFIED',
                'DOCUMENT_REPLACED',
                'APPROVAL_MARKED_OVERDUE',
                'REMINDER_SENT',
                'COMPLIANCE_WARNING_CREATED',
                'HIGH_PRIORITY_ALERT_CREATED',
                'PHYSICIAN_APPROVAL_COMPLETED',
                'PHYSICIAN_APPROVAL_REJECTED',
                'PHYSICIAN_APPROVAL_RESCINDED',
                'APPROVAL_VOIDED',
                'DOCUMENT_VOIDED'
            )
            """,
            name="ck_poc_physician_approval_audit_events_type",
        ),
        CheckConstraint(
            """
            performed_by_user_id IS NOT NULL
            OR
            performed_by_name IS NOT NULL
            OR
            performed_by_role IS NOT NULL
            OR
            event_type IN (
                'APPROVAL_MARKED_OVERDUE',
                'COMPLIANCE_WARNING_CREATED',
                'HIGH_PRIORITY_ALERT_CREATED'
            )
            """,
            name="ck_poc_physician_approval_audit_events_actor_or_system_event",
        ),
        Index(
            "ix_poc_physician_approval_audit_events_tenant_id",
            "tenant_id",
        ),
        Index(
            "ix_poc_physician_approval_audit_events_approval_id",
            "poc_physician_approval_id",
        ),
        Index(
            "ix_poc_physician_approval_audit_events_patient_id",
            "patient_id",
        ),
        Index(
            "ix_poc_physician_approval_audit_events_poc_version_id",
            "poc_version_id",
        ),
        Index(
            "ix_poc_physician_approval_audit_events_event_type",
            "event_type",
        ),
        Index(
            "ix_poc_physician_approval_audit_events_created_at",
            "created_at",
        ),
        Index(
            "ix_poc_physician_approval_audit_events_tenant_patient_version",
            "tenant_id",
            "patient_id",
            "poc_version_id",
        ),
        Index(
            "ix_poc_physician_approval_audit_events_tenant_event_created",
            "tenant_id",
            "event_type",
            "created_at",
        ),
    )