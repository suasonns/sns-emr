# app/models/med_reconciliation.py

from __future__ import annotations

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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel
from app.models.tenant_mixin import TenantScopedMixin


class MedReconciliationImport(TenantScopedMixin, BaseModel):
    __tablename__ = "med_reconciliation_imports"

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_type = Column(String(32), nullable=False)
    source_context = Column(String(32), nullable=False)

    status = Column(
        String(32),
        nullable=False,
        server_default="PENDING_REVIEW",
    )

    source_file_name = Column(String(255), nullable=True)

    uploaded_by = Column(UUID(as_uuid=True), nullable=True)
    uploaded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    parsed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)

    raw_summary = Column(Text, nullable=True)

    patient = relationship("Patient")

    items = relationship(
        "MedReconciliationItem",
        back_populates="import_record",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('PDF', 'CCD', 'C-CDA', 'SCANNED_DOC', 'MANUAL')",
            name="ck_med_reconciliation_imports_source_type",
        ),
        CheckConstraint(
            "source_context IN ('HOSPITAL_DISCHARGE', 'ED_VISIT', 'INPATIENT_STAY', 'OTHER')",
            name="ck_med_reconciliation_imports_source_context",
        ),
        CheckConstraint(
            "status IN ('PENDING_REVIEW', 'PARTIALLY_REVIEWED', 'FINALIZED')",
            name="ck_med_reconciliation_imports_status",
        ),
        Index(
            "ix_med_reconciliation_imports_patient",
            "patient_id",
        ),
    )


class MedReconciliationItem(TenantScopedMixin, BaseModel):
    __tablename__ = "med_reconciliation_items"

    import_id = Column(
        UUID(as_uuid=True),
        ForeignKey("med_reconciliation_imports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    list_type = Column(String(32), nullable=False)

    med_name_raw = Column(String(255), nullable=False)
    med_name_normalized = Column(String(255), nullable=True)

    dose = Column(String(128), nullable=True)
    route = Column(String(64), nullable=True)
    frequency = Column(String(128), nullable=True)
    indication = Column(String(255), nullable=True)

    dose_normalized = Column(String(128), nullable=True)
    route_normalized = Column(String(64), nullable=True)
    frequency_normalized = Column(String(128), nullable=True)

    signature_hash = Column(String(64), nullable=False, index=True)

    reaction_description = Column(Text, nullable=True)
    severity = Column(String(16), nullable=True)

    reaction_category_suggested = Column(String(32), nullable=True)
    reaction_category_final = Column(String(32), nullable=True)

    is_discharge_candidate = Column(Boolean, nullable=False, server_default="false")
    requires_immediate_review = Column(Boolean, nullable=False, server_default="false")
    is_critical_reaction = Column(Boolean, nullable=False, server_default="false")

    review_status = Column(
        String(32),
        nullable=False,
        server_default="PENDING",
    )

    notes = Column(Text, nullable=True)

    import_record = relationship(
        "MedReconciliationImport",
        back_populates="items",
    )

    patient = relationship("Patient")

    __table_args__ = (
        CheckConstraint(
            "list_type IN ('INPATIENT_HISTORY', 'DISCHARGE_LIST')",
            name="ck_med_reconciliation_items_list_type",
        ),
        CheckConstraint(
            "(severity IS NULL) OR (severity IN ('MILD', 'MODERATE', 'SEVERE'))",
            name="ck_med_reconciliation_items_severity",
        ),
        CheckConstraint(
            "(reaction_category_suggested IS NULL) OR "
            "(reaction_category_suggested IN ('POSSIBLE_ALLERGY', 'POSSIBLE_SIDE_EFFECT', 'POSSIBLE_INTOLERANCE', 'UNKNOWN'))",
            name="ck_med_reconciliation_items_reaction_category_suggested",
        ),
        CheckConstraint(
            "(reaction_category_final IS NULL) OR "
            "(reaction_category_final IN ('ALLERGY', 'SIDE_EFFECT', 'INTOLERANCE'))",
            name="ck_med_reconciliation_items_reaction_category_final",
        ),
        CheckConstraint(
            "review_status IN ('PENDING', 'REVIEWED', 'ACCEPTED', 'REJECTED')",
            name="ck_med_reconciliation_items_review_status",
        ),
        Index(
            "ix_med_reconciliation_items_patient",
            "patient_id",
        ),
        Index(
            "ix_med_reconciliation_items_patient_pending_signature",
            "patient_id",
            "review_status",
            "signature_hash",
        ),
    )