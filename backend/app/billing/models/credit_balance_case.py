from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

# Case lifecycle -- a system-generated negative claim balance always starts
# POTENTIAL; a qualified billing user must review before it becomes
# CONFIRMED (or NOT_A_CREDIT_BALANCE if the calculation doesn't hold up).
# See app.billing.services.credit_balance_case_service.ALLOWED_TRANSITIONS
# for the full state machine.
CREDIT_BALANCE_STATUSES = {
    "POTENTIAL",
    "UNDER_REVIEW",
    "CONFIRMED",
    "NOT_A_CREDIT_BALANCE",
    "REPAYMENT_REQUIRED",
    "REFUND_PENDING",
    "RECOUPMENT_PENDING",
    "REALLOCATION_PENDING",
    "RESOLVED_REPAID",
    "RESOLVED_RECOUPED",
    "RESOLVED_REALLOCATED",
    "CLOSED",
}

# Whether the credit balance is reportable on CMS-838 (Medicare providers
# only). Derived strictly from real structured payer metadata
# (app.models.patient_payer.PatientPayer.payer_type) via
# credit_balance_service.classify_medicare_reportability -- never guessed
# from the claim's payer_name string. Deliberately simple: only three
# states (MEDICARE_REPORTABLE, NON_MEDICARE, UNKNOWN) per approved
# business rule -- this is not a payer-taxonomy engine. UNKNOWN means no
# matching PatientPayer record was found and a biller must verify
# manually, reachable only via a biller's manual RECLASSIFY_MEDICARE
# action (see credit_balance_case_service).
MEDICARE_CLASSIFICATIONS = {
    "MEDICARE_REPORTABLE",
    "NON_MEDICARE",
    "UNKNOWN",
}


class CreditBalanceCase(Base):
    """
    A tracked investigation/resolution case for one claim-level credit
    balance (overpayment). This is the ONLY new data store the Credit
    Balance Report introduces -- it references the authoritative Claim
    row and does not duplicate claim/payment/adjustment/remittance data.

    A case is only created once a biller opens one from the report (or
    the system auto-opens a POTENTIAL case the first time a claim's
    computed net balance goes negative -- see credit_balance_service).
    Claims with a negative computed balance but no case yet are shown on
    the report as ad-hoc "claim_credit_items" without a case_id.
    """

    __tablename__ = "credit_balance_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    claim_id = Column(
        UUID(as_uuid=True),
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status = Column(
        String(32),
        nullable=False,
        default="POTENTIAL",
        server_default=text("'POTENTIAL'"),
        index=True,
    )

    medicare_classification = Column(
        String(32),
        nullable=False,
        default="UNKNOWN",
        server_default=text("'UNKNOWN'"),
        index=True,
    )

    reason_code = Column(
        String(64),
        nullable=True,
        doc=(
            "Free-text/coded reason once reviewed: DUPLICATE_PAYMENT, "
            "COB_ISSUE, MSP_ISSUE, PATIENT_RESPONSIBILITY_ERROR, "
            "MISPOSTED_PAYMENT, RECOUPMENT_PENDING_REVERSAL, "
            "ADJUSTMENT_ERROR, SERVICE_NOT_COVERED, OTHER."
        ),
    )

    # ---------------------------------------------------------
    # AMOUNTS -- snapshot at detection time + running resolution totals.
    # The authoritative current balance is always recomputed live from
    # Claim/Payment/PaymentAdjustment/Denial (see credit_balance_service);
    # these columns are a point-in-time record for case-history display
    # and CMS-838 export, not a second ledger.
    # ---------------------------------------------------------
    credit_amount_at_detection = Column(Numeric(12, 2), nullable=False)

    amount_repaid = Column(Numeric(12, 2), nullable=False, default=0, server_default=text("0"))

    amount_recouped = Column(Numeric(12, 2), nullable=False, default=0, server_default=text("0"))

    amount_reallocated = Column(Numeric(12, 2), nullable=False, default=0, server_default=text("0"))

    repayment_method = Column(String(64), nullable=True)

    assigned_to = Column(String(255), nullable=True)

    notes = Column(Text, nullable=True)

    # ---------------------------------------------------------
    # LIFECYCLE DATES (tracked separately per business rule -- automated
    # detection is not the same as formal post-review identification, and
    # the overpayment-return deadline only starts at identification).
    # ---------------------------------------------------------
    detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    review_started_at = Column(DateTime(timezone=True), nullable=True)
    identified_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    repayment_due_at = Column(Date, nullable=True)
    repaid_at = Column(DateTime(timezone=True), nullable=True)
    recouped_at = Column(DateTime(timezone=True), nullable=True)
    reallocated_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    tenant = relationship("Tenant")
    claim = relationship("Claim")
    patient = relationship("Patient")
    events = relationship(
        "CreditBalanceCaseEvent",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="CreditBalanceCaseEvent.created_at",
    )

    __table_args__ = (
        Index("ix_credit_balance_case_tenant_status", "tenant_id", "status"),
        Index("ix_credit_balance_case_claim", "claim_id"),
    )


class CreditBalanceCaseEvent(Base):
    """
    Immutable audit-trail entry for every credit-balance case action
    (confirm, reject, refund, recoupment, reallocation, correspondence,
    close, etc). Required because financial/compliance case history must
    be durably persisted with reason + user + timestamp + before/after
    amounts + source transaction reference -- the existing in-memory
    app.billing.audit_store is not durable and is unsuitable here.
    """

    __tablename__ = "credit_balance_case_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("credit_balance_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    action = Column(
        String(64),
        nullable=False,
        doc=(
            "CONFIRM / REJECT / REQUEST_INVESTIGATION / INITIATE_REFUND / "
            "RECORD_REFUND / REQUEST_RECOUPMENT / RECORD_RECOUPMENT / "
            "REALLOCATE_PAYMENT / CORRECT_MISPOSTING / RECORD_CORRESPONDENCE / "
            "CLOSE_CASE / RECLASSIFY_MEDICARE"
        ),
    )

    previous_status = Column(String(32), nullable=True)
    new_status = Column(String(32), nullable=True)

    reason = Column(Text, nullable=False)

    performed_by = Column(String(255), nullable=False)

    source_transaction_reference = Column(
        String(255),
        nullable=True,
        doc="Free-text reference to the source transaction (e.g. a payment id, remittance advice id, or check/EFT number) supporting this action.",
    )

    amount_before = Column(Numeric(12, 2), nullable=True)
    amount_after = Column(Numeric(12, 2), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    case = relationship("CreditBalanceCase", back_populates="events")

    __table_args__ = (
        Index("ix_credit_balance_case_event_case", "case_id"),
    )
