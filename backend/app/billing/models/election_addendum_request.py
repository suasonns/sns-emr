from __future__ import annotations

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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


# FY2027 (CMS-1851-F) mandatory-addendum trigger values, alongside the
# pre-existing request-triggered values. See
# election_addendum_service.compute_addendum_compliance() (pre-10/1/2026
# request-triggered rule) and compute_mandatory_addendum_requirement()
# (on/after 10/1/2026 mandatory-election rule) -- both read/write this
# same table; a record's trigger_type says which rule created it.
ELECTION_ADDENDUM_TRIGGER_TYPES = (
    "BENEFICIARY_REQUEST",
    "REPRESENTATIVE_REQUEST",
    "NON_HOSPICE_PROVIDER_REQUEST",
    "MANDATORY_INITIAL_ELECTION",
    "PLAN_OF_CARE_CHANGE",
)

ELECTION_ADDENDUM_FURNISHED_TO_TYPES = ("BENEFICIARY", "REPRESENTATIVE")

# Relatedness-determination-centered workflow status (workflow-owner
# decision: the operational risk is delayed relatedness determination,
# not document finalization -- unusual cases (dialysis, specialty
# medications, transplant-related therapies, unusual DME) enter
# PENDING_RELATEDNESS_REVIEW; the 5-day/3-day compliance clock (see
# required_by_at) is NEVER stopped by this status -- only ADDENDUM_FURNISHED
# or a documented EXCEPTION_CLOSED closes it).
ELECTION_ADDENDUM_WORKFLOW_STATUSES = (
    "REQUIREMENT_CREATED",
    "PENDING_RELATEDNESS_REVIEW",
    "READY_FOR_GENERATION",
    "ADDENDUM_GENERATED",
    "ADDENDUM_FURNISHED",
    "EXCEPTION_CLOSED",
)

# Widened determination_type vocabulary for ElectionAddendumDetermination
# (the pre-existing item-level relatedness/coverage child table -- reused,
# not duplicated, per architecture decision: do not create a second
# "relatedness item" table alongside election_addendum_determinations).
ELECTION_ADDENDUM_DETERMINATION_TYPES = (
    "CONDITION",
    "ITEM",
    "SERVICE",
    "DRUG",
    "SUPPLY",
    "DME",
    "DIALYSIS_TREATMENT",
    "TRANSPORTATION",
    "PROVIDER_SERVICE",
    "OTHER",
)

# relationship_status now includes PENDING_REVIEW so the parent
# ElectionAddendumRequest can programmatically detect an incomplete
# relatedness review (relatedness review is not complete until every
# determination row has left PENDING_REVIEW).
ELECTION_ADDENDUM_RELATIONSHIP_STATUSES = ("PENDING_REVIEW", "RELATED", "UNRELATED")

ELECTION_ADDENDUM_COVERAGE_OWNERS = (
    "HOSPICE",
    "NON_HOSPICE_MEDICARE",
    "OTHER_PAYER",
    "PATIENT_RESPONSIBILITY",
    "UNDETERMINED",
)

ELECTION_ADDENDUM_FURNISHED_TO = ("PATIENT", "REPRESENTATIVE")

ELECTION_ADDENDUM_FURNISHING_METHODS = ("IN_PERSON", "PAPER_PACKET", "ELECTRONIC", "MAIL", "OTHER")

ELECTION_ADDENDUM_EXCEPTION_TYPES = (
    "PATIENT_DIED",
    "ELECTION_REVOKED",
    "PATIENT_DISCHARGED",
    "OTHER_ALLOWED_EXCEPTION",
)

ELECTION_ADDENDUM_ACKNOWLEDGMENT_STATUSES = (
    "PENDING",
    "SIGNED_BY_PATIENT",
    "SIGNED_BY_REPRESENTATIVE",
    "REFUSED",
    "UNABLE_TO_SIGN",
    "NOT_REQUIRED_DUE_TO_EXCEPTION",
)


class ElectionAddendumRequest(Base):
    """
    Single addendum requirement/lifecycle record for the CMS Hospice
    Election Statement Addendum (42 CFR 418.24(b)), covering BOTH:

      - PRE-10/1/2026: the original request-triggered workflow (5-day/
        72-hour furnishing deadline measured from a real logged request --
        see election_addendum_service.compute_addendum_compliance()).
      - ON/AFTER 10/1/2026: the CMS FY2027 mandatory-for-every-Medicare-
        election workflow (5-day furnishing deadline from the election
        start date, regardless of request; 3-day update deadline on an
        applicable Plan-of-Care change -- see
        compute_mandatory_addendum_requirement()).

    This is intentionally the single addendum authority for both rules
    (per architecture decision: do not create a second, parallel
    `hospice_election_addendum` table). `trigger_type` distinguishes which
    rule produced a given row. `requested_date`/`requested_by` remain
    nullable because a MANDATORY_INITIAL_ELECTION row is never triggered by
    a request.
    """

    __tablename__ = "election_addendum_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    admission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("admissions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="The care episode (admission) this addendum requirement belongs to.",
    )

    benefit_period_id = Column(
        UUID(as_uuid=True),
        ForeignKey("benefit_periods.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc=(
            "The specific benefit_periods row whose election_date supplied "
            "election_effective_date. Required (non-null) whenever "
            "trigger_type=MANDATORY_INITIAL_ELECTION -- there is no FK from "
            "admissions to benefit_periods, so this column is the explicit, "
            "auditable record of which benefit period was used; the source "
            "must never be re-derived by silent lookup at read time."
        ),
    )

    # ---------------------------------------------------------
    # Pre-existing request-triggered workflow (PRESERVED AS-IS)
    # ---------------------------------------------------------
    requested_date = Column(Date, nullable=True)

    requested_by = Column(
        String(32),
        nullable=True,
        doc="PATIENT_OR_REPRESENTATIVE / NON_HOSPICE_PROVIDER / MEDICARE_CONTRACTOR",
    )

    delivered_date = Column(Date, nullable=True)

    not_required_reason = Column(
        String(255),
        nullable=True,
        doc="Documented reason the furnishing requirement no longer applies (e.g. request withdrawn).",
    )

    # ---------------------------------------------------------
    # FY2027 mandatory-election workflow (NEW)
    # ---------------------------------------------------------
    trigger_type = Column(
        String(40),
        nullable=False,
        server_default="BENEFICIARY_REQUEST",
        doc="What created this requirement row -- see ELECTION_ADDENDUM_TRIGGER_TYPES.",
    )

    workflow_status = Column(
        String(40),
        nullable=False,
        server_default="REQUIREMENT_CREATED",
        doc=(
            "Relatedness-determination-centered workflow status -- see "
            "ELECTION_ADDENDUM_WORKFLOW_STATUSES. The operational risk this "
            "tracks is delayed relatedness determination (e.g. dialysis, "
            "specialty medications, transplant-related therapies, unusual "
            "DME, complex coverage determinations requiring physician "
            "review), not document finalization. PENDING_RELATEDNESS_REVIEW "
            "never stops the 5-day/3-day compliance clock (required_by_at)."
        ),
    )

    triggered_at = Column(DateTime(timezone=True), nullable=True)

    election_effective_date = Column(
        Date,
        nullable=True,
        doc=(
            "Verified election start date sourced from benefit_periods."
            "election_date for the patient's INITIAL benefit period -- the "
            "FY2027 5-day mandatory-furnishing clock starts here, not from "
            "admissions.election_signed_at (a separate signature-completion "
            "timestamp)."
        ),
    )

    required_by_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Computed deadline: election_effective_date + 5 days (initial) or trigger + 3 days (POC change).",
    )

    mandatory_rule_applies = Column(
        Boolean,
        nullable=False,
        server_default="false",
        doc="True when election_effective_date >= 2026-10-01 (CMS FY2027 rule).",
    )

    version_number = Column(Integer, nullable=False, server_default="1")

    supersedes_request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("election_addendum_requests.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ---- Unusual-case relatedness review ----
    relatedness_review_started_at = Column(DateTime(timezone=True), nullable=True)
    relatedness_review_started_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    relatedness_review_reason = Column(Text, nullable=True)

    relatedness_determined_at = Column(DateTime(timezone=True), nullable=True)
    relatedness_determined_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    clinical_rationale = Column(
        Text,
        nullable=True,
        doc="Overall clinical rationale recorded when the relatedness review is completed.",
    )

    physician_review_required = Column(Boolean, nullable=False, server_default="false")
    physician_review_requested_at = Column(DateTime(timezone=True), nullable=True)
    physician_reviewer_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    physician_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    physician_review_rationale = Column(Text, nullable=True)

    # ---- Generation ----
    generated_at = Column(DateTime(timezone=True), nullable=True)
    document_reference = Column(
        String(255),
        nullable=True,
        doc="Immutable reference to the generated, patient-specific addendum document.",
    )
    document_version = Column(Integer, nullable=True)

    # ---- Furnishing (evidence of actual receipt, not generation/assignment) ----
    furnished_at = Column(DateTime(timezone=True), nullable=True)
    furnished_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    furnished_to = Column(String(40), nullable=True, doc="PATIENT / REPRESENTATIVE")
    furnishing_method = Column(String(40), nullable=True)

    bfcc_qio_information_furnished = Column(Boolean, nullable=False, server_default="false")

    # ---- Acknowledgment (packet-level signature linked to this version) ----
    acknowledgment_status = Column(String(40), nullable=True)
    acknowledgment_at = Column(DateTime(timezone=True), nullable=True)
    acknowledgment_document_reference = Column(Text, nullable=True)
    signature_exception_reason = Column(Text, nullable=True)

    # ---- Regulatory exception (death / revocation / discharge before furnishing) ----
    exception_type = Column(String(40), nullable=True)
    exception_occurred_at = Column(DateTime(timezone=True), nullable=True)

    finalized_at = Column(DateTime(timezone=True), nullable=True)
    finalized_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_by = Column(String(255), nullable=True)

    # ---- Deprecated (superseded by relatedness_determined_*/furnished_to/
    # furnishing_method/acknowledgment_at/signature_exception_reason above).
    # Left mapped, unused-by-new-code, and NOT dropped from the database:
    # this repo's Alembic safety guard blocks destructive ops in
    # upgrade(), so these are retained in-place rather than dropped, and
    # kept mapped here so the ORM model matches the live schema (no
    # autogenerate drift). A future, separately-reviewed cleanup migration
    # may drop them once no code/reporting path still reads them.
    determination_completed_at = Column(DateTime(timezone=True), nullable=True)
    determined_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    determined_by_account_discipline = Column(String(50), nullable=True)
    furnished_to_type = Column(String(20), nullable=True)
    furnished_to_name = Column(String(255), nullable=True)
    delivery_method = Column(String(40), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    refusal_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    patient = relationship("Patient")
    determinations = relationship(
        "ElectionAddendumDetermination",
        back_populates="addendum_request",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_election_addendum_requests_tenant_patient", "tenant_id", "patient_id"),
        Index("ix_election_addendum_requests_tenant_admission", "tenant_id", "admission_id"),
        Index("ix_election_addendum_requests_workflow_status", "workflow_status"),
        CheckConstraint(
            "workflow_status IN ("
            "'REQUIREMENT_CREATED','PENDING_RELATEDNESS_REVIEW','READY_FOR_GENERATION',"
            "'ADDENDUM_GENERATED','ADDENDUM_FURNISHED','EXCEPTION_CLOSED'"
            ")",
            name="ck_ear_workflow_status",
        ),
        UniqueConstraint(
            "tenant_id",
            "admission_id",
            "version_number",
            name="uq_election_addendum_requests_tenant_admission_version",
        ),
        CheckConstraint("version_number > 0", name="ck_election_addendum_requests_version_positive"),
        CheckConstraint(
            "supersedes_request_id IS NULL OR supersedes_request_id != id",
            name="ck_election_addendum_requests_no_self_supersede",
        ),
        CheckConstraint(
            "furnished_to IS NULL OR furnished_to IN ('PATIENT','REPRESENTATIVE')",
            name="ck_ear_furnished_to",
        ),
        CheckConstraint(
            "furnishing_method IS NULL OR furnishing_method IN "
            "('IN_PERSON','PAPER_PACKET','ELECTRONIC','MAIL','OTHER')",
            name="ck_ear_furnishing_method",
        ),
        CheckConstraint(
            "exception_type IS NULL OR exception_type IN "
            "('PATIENT_DIED','ELECTION_REVOKED','PATIENT_DISCHARGED','OTHER_ALLOWED_EXCEPTION')",
            name="ck_ear_exception_type",
        ),
        CheckConstraint(
            "acknowledgment_status IS NULL OR acknowledgment_status IN ("
            "'PENDING','SIGNED_BY_PATIENT','SIGNED_BY_REPRESENTATIVE','REFUSED',"
            "'UNABLE_TO_SIGN','NOT_REQUIRED_DUE_TO_EXCEPTION'"
            ")",
            name="ck_ear_acknowledgment_status",
        ),
        CheckConstraint("document_version IS NULL OR document_version > 0", name="ck_ear_document_version_positive"),
        CheckConstraint(
            "workflow_status NOT IN ('ADDENDUM_GENERATED','ADDENDUM_FURNISHED') "
            "OR (document_reference IS NOT NULL AND generated_at IS NOT NULL)",
            name="ck_ear_generated_requires_document",
        ),
        CheckConstraint(
            "workflow_status != 'ADDENDUM_FURNISHED' OR ("
            "furnished_at IS NOT NULL AND furnished_to IS NOT NULL AND furnishing_method IS NOT NULL"
            ")",
            name="ck_ear_furnished_requires_evidence",
        ),
        CheckConstraint(
            "furnished_at IS NULL OR generated_at IS NULL OR furnished_at >= generated_at",
            name="ck_ear_furnished_after_generated",
        ),
        CheckConstraint(
            "workflow_status != 'EXCEPTION_CLOSED' OR ("
            "exception_type IS NOT NULL AND exception_occurred_at IS NOT NULL"
            ")",
            name="ck_ear_exception_requires_evidence",
        ),
        CheckConstraint(
            "acknowledgment_status NOT IN ('SIGNED_BY_PATIENT','SIGNED_BY_REPRESENTATIVE','REFUSED','UNABLE_TO_SIGN')"
            " OR acknowledgment_at IS NOT NULL",
            name="ck_ear_ack_requires_timestamp",
        ),
        CheckConstraint(
            "acknowledgment_status != 'REFUSED' OR signature_exception_reason IS NOT NULL",
            name="ck_ear_refusal_requires_reason",
        ),
        CheckConstraint(
            "finalized_at IS NULL OR document_reference IS NOT NULL",
            name="ck_election_addendum_requests_finalize_requires_document",
        ),
        CheckConstraint(
            "finalized_at IS NULL OR bfcc_qio_information_furnished = true",
            name="ck_election_addendum_requests_finalize_requires_bfcc_qio",
        ),
        # Deprecated constraints from 23062ecb4fd9, referencing the
        # deprecated acknowledged_at/refusal_reason columns above. Not
        # dropped (see note on the deprecated columns); kept mapped here
        # to match the live schema exactly (no autogenerate drift).
        CheckConstraint(
            "acknowledgment_status != 'ACKNOWLEDGED' OR acknowledged_at IS NOT NULL",
            name="ck_election_addendum_requests_ack_requires_timestamp",
        ),
        CheckConstraint(
            "acknowledgment_status != 'REFUSED' OR refusal_reason IS NOT NULL",
            name="ck_election_addendum_requests_refusal_requires_reason",
        ),
    )


class ElectionAddendumDetermination(Base):
    """
    Item-level relatedness/coverage determination (a condition, item,
    service, or drug) attached to an ElectionAddendumRequest version. This
    IS the item-level relatedness-review table for the unusual-case
    workflow -- there is exactly one addendum parent authority
    (ElectionAddendumRequest) and exactly one item-level child table; do
    not create a second "relatedness item" table alongside this one.

    relationship_status starts at PENDING_REVIEW; the parent addendum's
    relatedness review is not complete (cannot transition to
    READY_FOR_GENERATION) until every determination row for the current
    version has left PENDING_REVIEW.
    """

    __tablename__ = "election_addendum_determinations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    addendum_request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("election_addendum_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    determination_type = Column(
        String(20),
        nullable=False,
        doc="CONDITION / ITEM / SERVICE / DRUG / SUPPLY / DME / DIALYSIS_TREATMENT / TRANSPORTATION / PROVIDER_SERVICE / OTHER",
    )
    description = Column(Text, nullable=False)
    relationship_status = Column(
        String(20),
        nullable=False,
        server_default="PENDING_REVIEW",
        doc="PENDING_REVIEW / RELATED / UNRELATED",
    )
    coverage_status = Column(
        String(20),
        nullable=True,
        doc="COVERED / NOT_COVERED -- required once relationship_status leaves PENDING_REVIEW.",
    )
    coverage_owner = Column(
        String(30),
        nullable=True,
        doc="HOSPICE / NON_HOSPICE_MEDICARE / OTHER_PAYER / PATIENT_RESPONSIBILITY / UNDETERMINED",
    )
    clinical_rationale = Column(Text, nullable=True)
    effective_date = Column(Date, nullable=False)

    current_provider_or_supplier = Column(
        String(255),
        nullable=True,
        doc="Name of the current non-hospice provider/supplier for this item, when applicable (e.g. dialysis center, DME supplier).",
    )

    source_record_type = Column(String(50), nullable=True)
    source_record_id = Column(UUID(as_uuid=True), nullable=True)

    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    addendum_request = relationship("ElectionAddendumRequest", back_populates="determinations")

    __table_args__ = (
        Index("ix_election_addendum_determinations_tenant_id", "tenant_id"),
        CheckConstraint(
            "relationship_status IN ('PENDING_REVIEW','RELATED','UNRELATED')",
            name="ck_eadetermination_relationship_status",
        ),
        CheckConstraint(
            "relationship_status != 'UNRELATED' OR clinical_rationale IS NOT NULL",
            name="ck_election_addendum_determinations_unrelated_requires_rationale",
        ),
        CheckConstraint(
            "relationship_status = 'PENDING_REVIEW' OR coverage_status IS NOT NULL",
            name="ck_eadetermination_reviewed_requires_coverage_status",
        ),
        CheckConstraint(
            "relationship_status != 'PENDING_REVIEW' OR (reviewed_at IS NULL AND reviewed_by_user_id IS NULL)",
            name="ck_eadetermination_pending_has_no_review",
        ),
        CheckConstraint(
            "relationship_status = 'PENDING_REVIEW' OR (reviewed_at IS NOT NULL AND reviewed_by_user_id IS NOT NULL)",
            name="ck_eadetermination_reviewed_requires_actor",
        ),
    )


class ElectionAddendumAuditEvent(Base):
    """Domain-specific append-style audit trail for addendum lifecycle events."""

    __tablename__ = "election_addendum_audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    addendum_request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("election_addendum_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    admission_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    event_type = Column(String(50), nullable=False, index=True)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    actor_account_discipline = Column(
        String(50),
        nullable=True,
        doc="Snapshot of the acting user's account discipline at event time (never client-supplied).",
    )
    prior_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    reason = Column(Text, nullable=True)
    event_metadata = Column("metadata", JSONB, nullable=True)
    correlation_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    __table_args__ = (
        Index(
            "ix_election_addendum_audit_events_tenant_event_created",
            "tenant_id",
            "event_type",
            "created_at",
        ),
        CheckConstraint(
            "event_type IN ("
            "'REQUIREMENT_CREATED','RELATEDNESS_REVIEW_STARTED','RELATEDNESS_ITEM_CREATED',"
            "'RELATEDNESS_ITEM_DETERMINED','DETERMINATION_RECORDED','PHYSICIAN_REVIEW_REQUESTED',"
            "'PHYSICIAN_REVIEW_COMPLETED','RELATEDNESS_DETERMINED','RELATEDNESS_REVIEW_COMPLETED',"
            "'ADDENDUM_GENERATED','ADDENDUM_FURNISHED','ACKNOWLEDGMENT_RECORDED','ACKNOWLEDGMENT_REFUSED',"
            "'ADDENDUM_ACKNOWLEDGED','ADDENDUM_REFUSED','ADDENDUM_SUPERSEDED','ADDENDUM_UPDATE_REQUIRED',"
            "'EXCEPTION_RECORDED','DEADLINE_MISSED','RECORD_CORRECTED','RECORD_FINALIZED','RECORD_REOPENED'"
            ")",
            name="ck_election_addendum_audit_events_type",
        ),
    )
