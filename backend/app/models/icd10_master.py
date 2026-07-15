from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class ICD10Master(Base):
    """
    ICD10 Master Table.

    This table is the single source of truth for ICD10-CM diagnosis identity.

    Purpose:
    - Stores ICD10 code.
    - Stores diagnosis description.
    - Stores display name.
    - Supports local/offline lookup by ICD10 code or disease name.
    - Does not decide hospice usage rules.

    Hospice usage rules live in:

        icd10_hospice_policy

    This table answers:

        What is this ICD10 code?
    """

    __tablename__ = "icd10_master"

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # ---------------------------------------------------------
    # ICD10 Identity
    # ---------------------------------------------------------

    icd10_code = Column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
    )

    diagnosis_description = Column(
        String(500),
        nullable=False,
        index=True,
    )

    display_name = Column(
        String(550),
        nullable=False,
    )

    # ---------------------------------------------------------
    # ICD10 Classification
    # ---------------------------------------------------------

    chapter_code = Column(
        String(20),
        nullable=True,
    )

    chapter_name = Column(
        String(255),
        nullable=True,
    )

    # ---------------------------------------------------------
    # Coding Status
    # ---------------------------------------------------------

    billable = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    active = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
        index=True,
    )

    effective_date = Column(
        Date,
        nullable=True,
    )

    retired_date = Column(
        Date,
        nullable=True,
    )

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    search_text = Column(
        Text,
        nullable=True,
    )

    # ---------------------------------------------------------
    # Audit
    # ---------------------------------------------------------

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------

    hospice_policy = relationship(
        "ICD10HospicePolicy",
        primaryjoin=(
            "ICD10Master.icd10_code == "
            "foreign(ICD10HospicePolicy.icd10_code)"
        ),
        viewonly=True,
        uselist=False,
    )

    # ---------------------------------------------------------
    # Constraints / Indexes
    # ---------------------------------------------------------

    __table_args__ = (
        CheckConstraint(
            "length(trim(icd10_code)) > 0",
            name="ck_icd10_master_code_not_blank",
        ),
        CheckConstraint(
            "length(trim(diagnosis_description)) > 0",
            name="ck_icd10_master_description_not_blank",
        ),
        CheckConstraint(
            "length(trim(display_name)) > 0",
            name="ck_icd10_master_display_name_not_blank",
        ),
        CheckConstraint(
            (
                "retired_date IS NULL "
                "OR effective_date IS NULL "
                "OR retired_date >= effective_date"
            ),
            name="ck_icd10_master_retired_after_effective",
        ),
        Index(
            "ix_icd10_master_code_active",
            "icd10_code",
            "active",
        ),
        Index(
            "ix_icd10_master_chapter",
            "chapter_code",
            "chapter_name",
        ),
    )