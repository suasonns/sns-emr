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
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class ICD10HospicePolicy(Base):
    """
    ICD10 Hospice Policy Table.

    This table is the single source of truth for how an ICD10 code may be used
    inside SNS EMR hospice workflows.

    Purpose:
    - Controls whether a code can be used as PRIMARY diagnosis.
    - Controls whether a code can be used as SECONDARY diagnosis.
    - Controls whether a code can be used as COMORBIDITY.
    - Controls workflow-specific use:
        Referral
        Facesheet
        RN ICA
        CTI
        POC
    - Controls billing primary acceptability.
    - Stores hospice governance warnings and block reasons.

    This table answers:

        How may this ICD10 code be used in hospice?
    """

    __tablename__ = "icd10_hospice_policy"

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    icd10_code = Column(
        String(20),
        ForeignKey(
            "icd10_master.icd10_code",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    # ---------------------------------------------------------
    # Diagnosis Role Governance
    # ---------------------------------------------------------

    allow_primary_dx = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    allow_secondary_dx = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    allow_comorbidity = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    # ---------------------------------------------------------
    # Workflow Governance
    # ---------------------------------------------------------

    allow_referral_dx = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    allow_facesheet_dx = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    allow_rn_ica_dx = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    allow_cti_dx = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    allow_poc_dx = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    # ---------------------------------------------------------
    # Billing / Claims Governance
    # ---------------------------------------------------------

    billing_primary_allowed = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    # ---------------------------------------------------------
    # Review / Documentation Governance
    # ---------------------------------------------------------

    requires_md_review = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    requires_idg_review = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    requires_supporting_documentation = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    default_terminal_related = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    medication_relatedness_relevant = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    lcd_category = Column(
        String(100),
        nullable=True,
        index=True,
    )

    block_reason = Column(
        Text,
        nullable=True,
    )

    warning_message = Column(
        Text,
        nullable=True,
    )

    active = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
        index=True,
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

    icd10 = relationship(
        "ICD10Master",
        primaryjoin=(
            "ICD10HospicePolicy.icd10_code == "
            "foreign(ICD10Master.icd10_code)"
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
            name="ck_icd10_hospice_policy_code_not_blank",
        ),
        Index(
            "ix_icd10_hospice_policy_code_active",
            "icd10_code",
            "active",
        ),
        Index(
            "ix_icd10_hospice_policy_role_flags",
            "allow_primary_dx",
            "allow_secondary_dx",
            "allow_comorbidity",
        ),
        Index(
            "ix_icd10_hospice_policy_billing_primary",
            "billing_primary_allowed",
        ),
    )