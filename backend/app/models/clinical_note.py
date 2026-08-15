from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    event,
    text,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON, JSONB, UUID
from sqlalchemy.orm import relationship, synonym

from app.models.base import BaseModel


# ===================================================
# CLINICAL NOTE
# ===================================================

class ClinicalNote(BaseModel):

    __tablename__ = "clinical_notes"

    # ===================================================
    # RELATIONSHIPS
    # ===================================================

    visit_id = Column(ForeignKey("visits.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Primary authorship field (single source of truth)
    author_id = Column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    current_version_id = Column(
        UUID(as_uuid=True),
        # use_alter breaks the clinical_notes <-> clinical_note_versions cycle at create time
        ForeignKey(
            "clinical_note_versions.id",
            ondelete="RESTRICT",
            use_alter=True,
            name="fk_clinical_notes_current_version_id",
        ),
        nullable=True,
    )

    # ===================================================
    # CORE
    # ===================================================

    note_type = Column(String(50), nullable=False)
    discipline = Column(String(10), nullable=False)

    # ===================================================
    # SUPERVISION
    # ===================================================

    requires_countersign = Column(Boolean, nullable=False, default=False)

    countersigned_by = Column(UUID(as_uuid=True), nullable=True)
    countersigned_at = Column(DateTime(timezone=True), nullable=True)

    # ===================================================
    # FORM ENGINE
    # ===================================================

    form_family = Column(String(64))
    form_key = Column(String(128), index=True)

    module_payload = Column(JSON)

    is_primary_form = Column(Boolean, nullable=False, server_default=text("true"))

    parent_form_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clinical_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    is_primary = synonym("is_primary_form")
    parent_note_id = synonym("parent_form_id")

    # ===================================================
    # LIFECYCLE
    # ===================================================

    status = Column(String(20))
    encounter_date = Column(Date)

    finalized_at = Column(DateTime(timezone=True))
    finalized_by = Column(UUID(as_uuid=True))
    
    entered_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    is_late_entry = Column(
        Boolean,
        nullable=False,
        server_default=text("false")
    )

    late_entry_reason = Column(String(255), nullable=True)

    # ===================================================
    # CONTENT
    # ===================================================

    content = Column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    plan_of_care_updates = Column(JSON)
    
    raw_transcript = Column(JSONB, nullable=True)
    
    # ===================================================
    # AUDIT
    # ===================================================
    # Legacy compatibility field (do not use as primary authorship)
    created_by = Column(UUID(as_uuid=True))
    signed_by = Column(UUID(as_uuid=True))
    signed_at = Column(DateTime(timezone=True))

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
    
    updated_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    
    # ===================================================
    # CONSTRAINTS
    # ===================================================

    __table_args__ = (

        CheckConstraint(
            "discipline IN ('RN','LVN','NP','MD','SC','MSW','LCSW','BSW')",
            name="ck_discipline_valid"
        ),

        CheckConstraint(
            "(discipline != 'BSW') OR (requires_countersign = true)",
            name="ck_bsw_requires_flag"
        ),

        CheckConstraint(
            "(countersigned_by IS NULL AND countersigned_at IS NULL) OR "
            "(countersigned_by IS NOT NULL AND countersigned_at IS NOT NULL)",
            name="ck_countersign_pair"
        ),

        CheckConstraint(
            "(discipline != 'BSW') OR "
            "(finalized_at IS NULL OR countersigned_by IS NOT NULL)",
            name="ck_bsw_finalize_requires_countersign"
        ),

        CheckConstraint(
            "(countersigned_at IS NULL OR finalized_at IS NULL OR countersigned_at <= finalized_at)",
            name="ck_countersign_before_finalize"
        ),
        
        CheckConstraint(
            "(is_late_entry = false) OR (late_entry_reason IS NOT NULL)",
            name="ck_late_entry_requires_reason"
        ),
    )

    # ===================================================
    # ORM RELATIONSHIPS
    # ===================================================

    visit = relationship("Visit")

    current_version = relationship(
        "ClinicalNoteVersion",
        foreign_keys=[current_version_id],
        uselist=False,
        post_update=True,
    )

    versions = relationship(
        "ClinicalNoteVersion",
        back_populates="clinical_note",
        foreign_keys="ClinicalNoteVersion.clinical_note_id",
    )

    # ===================================================
    # FINALIZE
    # ===================================================

    def finalize(self, *, user_id: uuid.UUID):

        if self.finalized_at:
            raise ValueError("Already finalized")

        if not self.current_version_id:
            raise ValueError("Cannot finalize note without version")

        if self.discipline == "BSW" and not self.countersigned_by:
            raise ValueError("BSW requires countersign")

        now = datetime.now(timezone.utc)

        self.status = "FINALIZED"
        self.finalized_at = now
        self.finalized_by = user_id
        self.updated_at = now


# ===================================================
# VERSION MODEL
# ===================================================

class ClinicalNoteVersion(BaseModel):

    __tablename__ = "clinical_note_versions"

    __table_args__ = (
        UniqueConstraint(
            "clinical_note_id",
            "version_number",
            name="uq_note_version_per_note"
        ),
    )

    clinical_note_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clinical_notes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    version_number = Column(Integer, nullable=False)

    content = Column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    clinical_note = relationship(
        "ClinicalNote",
        back_populates="versions",
        foreign_keys=[clinical_note_id],
    )


# ===================================================
# INDEXES
# ===================================================

Index("idx_clinical_note_countersign", "countersigned_by")

Index(
    "idx_clinical_note_versions_note_version",
    "clinical_note_id",
    "version_number"
)


# ===================================================
# EVENTS
# ===================================================

@event.listens_for(ClinicalNote, "before_insert", propagate=True)
def before_insert(mapper, connection, target):

    now = datetime.now(timezone.utc)

    if not target.content:
        target.content = {}

    target.created_at = target.created_at or now
    target.updated_at = target.updated_at or now

    if target.discipline == "BSW":
        target.requires_countersign = True

    if (target.countersigned_by and not target.countersigned_at) or \
       (target.countersigned_at and not target.countersigned_by):
        raise ValueError("Invalid countersign state")


@event.listens_for(ClinicalNote, "before_update", propagate=True)
def before_update(mapper, connection, target):

    if not target.content:
        target.content = {}

    if target.finalized_at:
        raise ValueError("Cannot modify finalized note")

    if (target.countersigned_by and not target.countersigned_at) or \
       (target.countersigned_at and not target.countersigned_by):
        raise ValueError("Invalid countersign state")

    target.updated_at = datetime.now(timezone.utc)