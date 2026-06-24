from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    event,
    text,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship, synonym

from app.models.base import BaseModel


class ClinicalNote(BaseModel):
    """
    Enterprise-grade Clinical Note model.

    PURPOSE
    - Maps the existing clinical_notes table
    - Keeps business logic primarily in services / routers
    - Adds production-safe ORM protections for required fields
    - Preserves compatibility with existing service-layer naming patterns
    """

    __tablename__ = "clinical_notes"

    # ===================================================
    # RELATIONSHIPS / OWNERSHIP
    # ===================================================

    visit_id = Column(
        ForeignKey("visits.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    author_id = Column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # ACTIVE VERSION POINTER
    current_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clinical_note_versions.id", ondelete="RESTRICT"),
        nullable=True,
    )

    # ===================================================
    # CORE CLASSIFICATION
    # ===================================================

    note_type = Column(String, nullable=False)

    care_level = Column(String, nullable=True)
    visit_type = Column(String, nullable=True)
    visit_origin = Column(String, nullable=True)
    note_category = Column(String, nullable=True)
    encounter_type = Column(String, nullable=True)

    # Discipline that owns / authored the note
    discipline = Column(String, nullable=True)

    # ===================================================
    # FORM ENGINE SUPPORT
    # ===================================================

    # High-level family bucket used for routing / discipline ownership
    form_family = Column(String(64), nullable=True)

    # Exact resolved form identity, e.g. HOPE_ADMISSION / ROUTINE_VISIT_NOTE / POC_UPDATE
    form_key = Column(String(128), nullable=True, index=True)

    # Structured modules / attached form metadata
    module_payload = Column(JSON, nullable=True)

    # Primary vs attached form support
    is_primary_form = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    # Self-reference for attached forms
    parent_form_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clinical_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # ===================================================
    # SERVICE-LAYER COMPATIBILITY ALIASES
    # ===================================================
    # Several services are already using:
    # - note.is_primary
    # - note.parent_note_id
    #
    # These synonyms preserve compatibility while keeping the DB column
    # names stable and compliant with the current schema.

    is_primary = synonym("is_primary_form")
    parent_note_id = synonym("parent_form_id")

    # ===================================================
    # LIFECYCLE
    # ===================================================

    status = Column(String, nullable=True)
    encounter_date = Column(Date, nullable=True)

    finalized_at = Column(DateTime(timezone=True), nullable=True)
    finalized_by = Column(UUID(as_uuid=True), nullable=True)
    finalized_role_id = Column(UUID(as_uuid=True), nullable=True)
    finalized_interface_id = Column(UUID(as_uuid=True), nullable=True)

    # ===================================================
    # CLINICAL DATA (STRUCTURED)
    # ===================================================

    # CRITICAL:
    # - NOT NULL at DB level
    # - ORM default protects omitted values
    # - event listeners below protect explicit None
    content = Column(
        Text,
        nullable=False,
        default="",
        server_default=text("''"),
    )

    observed_data = Column(JSON, nullable=True)
    patient_reported = Column(JSON, nullable=True)
    caregiver_reported = Column(JSON, nullable=True)

    assessment = Column(JSON, nullable=True)
    interventions = Column(JSON, nullable=True)
    plan_of_care_updates = Column(JSON, nullable=True)

    # ===================================================
    # VALIDATION / COMPLIANCE
    # ===================================================

    needs_clarification = Column(Boolean, nullable=True)
    red_flags = Column(JSON, nullable=True)
    audit_flags = Column(JSON, nullable=True)

    # ===================================================
    # INCIDENT ENGINE
    # ===================================================

    incident_required = Column(Boolean, nullable=True)
    incident_status = Column(String, nullable=True)
    incident_id = Column(UUID(as_uuid=True), nullable=True)

    # ===================================================
    # AUDIT
    # ===================================================

    created_by = Column(UUID(as_uuid=True), nullable=True)
    signed_by = Column(UUID(as_uuid=True), nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    # ===================================================
    # RELATIONSHIPS
    # ===================================================

    visit = relationship("Visit", foreign_keys=[visit_id])

    current_version = relationship(
        "ClinicalNoteVersion",
        foreign_keys=[current_version_id],
        uselist=False,
        post_update=True,
    )

    versions = relationship(
        "ClinicalNoteVersion",
        foreign_keys="ClinicalNoteVersion.clinical_note_id",
        back_populates="clinical_note",
        order_by="ClinicalNoteVersion.version_number",
        cascade="save-update, merge",
    )

    parent_form = relationship(
        "ClinicalNote",
        remote_side="ClinicalNote.id",
        foreign_keys=[parent_form_id],
        back_populates="child_forms",
        uselist=False,
    )

    child_forms = relationship(
        "ClinicalNote",
        foreign_keys=[parent_form_id],
        back_populates="parent_form",
        cascade="all, delete-orphan",
    )

    # ===================================================
    # FINALIZE METHOD
    # ===================================================

    def finalize(self, *, user_id):
        if self.finalized_at is not None:
            raise ValueError("Clinical note already finalized")

        now = datetime.now(timezone.utc)

        self.status = "SIGNED"
        self.finalized_at = now
        self.finalized_by = user_id
        self.updated_at = now


class ClinicalNoteVersion(BaseModel):
    """
    Immutable version history for clinical notes.

    PURPOSE
    - Supports lock / amend / no-overwrite behavior
    - Each saveable version is recorded independently
    """

    __tablename__ = "clinical_note_versions"

    clinical_note_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clinical_notes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    version_number = Column(Integer, nullable=False)
    content = Column(
        Text,
        nullable=False,
        default="",
        server_default=text("''"),
    )
    amend_reason = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    created_by = Column(UUID(as_uuid=True), nullable=True)

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    clinical_note = relationship(
        "ClinicalNote",
        foreign_keys=[clinical_note_id],
        back_populates="versions",
    )

    __table_args__ = (
        CheckConstraint(
            "version_number >= 1",
            name="ck_clinical_note_versions_version_number_positive",
        ),
    )


# ===================================================
# ORM EVENT SAFETY
# ===================================================

@event.listens_for(ClinicalNote, "before_insert", propagate=True)
def clinical_note_before_insert(mapper, connection, target):
    """
    Production-safe insert guard.

    Prevents DB NOT NULL violations for content and ensures timestamps exist
    even when a service forgets to supply them.

    IMPORTANT:
    This protects current create_visit() paths where attached forms such as
    POC_UPDATE may be created without explicit content.
    """
    now = datetime.now(timezone.utc)

    if getattr(target, "content", None) is None:
        target.content = ""

    if getattr(target, "created_at", None) is None:
        target.created_at = now

    if getattr(target, "updated_at", None) is None:
        target.updated_at = now


@event.listens_for(ClinicalNote, "before_update", propagate=True)
def clinical_note_before_update(mapper, connection, target):
    """
    Production-safe update guard.

    - Keeps updated_at current
    - Prevents accidental NULL content on updates
    """
    if getattr(target, "content", None) is None:
        target.content = ""

    target.updated_at = datetime.now(timezone.utc)


@event.listens_for(ClinicalNoteVersion, "before_insert", propagate=True)
def clinical_note_version_before_insert(mapper, connection, target):
    """
    Version safety guard.
    """
    if getattr(target, "content", None) is None:
        target.content = ""
