# backend/app/billing/models/eligibility_source_document.py
"""
Eligibility, Admission, Benefit-Period, and Billing-Readiness Workflow
Correction -- Directive item 3: eligibility source document.

The uploaded payer eligibility response (270/271 print-out, portal PDF,
Medicare beneficiary eligibility report, etc.) is the evidence source for
everything downstream: structured findings (EligibilityVerification) and
the benefit-period determination (BenefitPeriodDetermination) both link
back to the exact document a human read to produce them.

This table is deliberately a thin *domain* wrapper, not a duplicate
storage layer: the actual file bytes, malware scanning, permission-
checked download, and sanitized-filename handling all continue to live
in the existing `app.models.document_record.DocumentRecord` +
`app.services.document_storage` pipeline (see backend/app/api/documents.py)
-- reused here via `document_record_id` rather than re-implemented, per
the directive's explicit "do not create duplicate storage" instruction.
This table only adds the eligibility-specific facts a generic document
record has no place for: which payer coverage it's about, the service
date range and verification date it applies to, superseding chains for
document versioning, and parser status when automated extraction is
added later (Directive item 5).
"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import BaseModel

# MEDICARE_BENEFICIARY_ELIGIBILITY_REPORT | PAYER_ELIGIBILITY_RESPONSE |
# AUTHORIZATION_DOCUMENT | ELIGIBILITY_SUPPORTING_DOCUMENT |
# NON_AUTH_VERIFICATION | TRANSFER_EVIDENCE | OTHER
ELIGIBILITY_DOCUMENT_TYPES = {
    "MEDICARE_BENEFICIARY_ELIGIBILITY_REPORT",
    "PAYER_ELIGIBILITY_RESPONSE",
    "AUTHORIZATION_DOCUMENT",
    "ELIGIBILITY_SUPPORTING_DOCUMENT",
    # Evidence that a staff member verified/confirmed authorization is NOT
    # required for this payer/coverage -- required whenever
    # PatientFaceSheet.authorization_required_status == "NO"
    # (docs/workflows/AuthorizationWorkflow.md). Never assumed absent this.
    "NON_AUTH_VERIFICATION",
    # Transfer packet / prior certification history supporting a
    # TRANSFER_FROM_ANOTHER_HOSPICE admit type
    # (docs/workflows/AdmissionTypesWorkflow.md). Required by the SOC
    # gate only for that admit type.
    "TRANSFER_EVIDENCE",
    # Payer verification evidence classifications (Priority 4 -- Payer
    # Review Workflow). SNS EMR does NOT perform eligibility verification
    # itself (no NGS Connex / CMS / payer-database integration); staff
    # verify coverage externally (NGS Connex, Availity, payer portal,
    # phone) and upload the resulting evidence here for review and audit.
    # See docs/workflows/PayerDeterminationWorkflow.md.
    "ELIGIBILITY_VERIFICATION",
    "MEDICARE_VERIFICATION",
    "MEDICAID_VERIFICATION",
    "COMMERCIAL_PAYER_VERIFICATION",
    "INSURANCE_CARD",
    "PAYER_SCREENSHOT",
    "OTHER_INSURANCE_EVIDENCE",
    "OTHER",
}

# ACTIVE (current evidence of record) | SUPERSEDED (replaced by a newer
# upload, kept for traceability, never deleted) | ARCHIVED (authorized
# records-management removal from active view, row retained)
ELIGIBILITY_DOCUMENT_STATUSES = {"ACTIVE", "SUPERSEDED", "ARCHIVED"}

# UNPARSED (no automated extraction attempted -- manual entry only,
# the only mode implemented in this phase) | PENDING | COMPLETE | FAILED
PARSER_STATUSES = {"UNPARSED", "PENDING", "COMPLETE", "FAILED"}


class EligibilitySourceDocument(BaseModel):
    __tablename__ = "eligibility_source_documents"

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        nullable=False,
        index=True,
    )

    # The specific payer coverage (PatientInsurance row) this eligibility
    # document is about. Nullable only because intake may upload a
    # general Medicare eligibility report before a specific coverage row
    # has been entered yet.
    payer_coverage_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patient_insurances.id"),
        nullable=True,
        index=True,
    )

    # Reuses the existing document storage/malware-scan/permission
    # pipeline -- see module docstring. This is where the actual bytes,
    # file_name, file_path, content_hash, and uploaded_by/uploaded_at
    # already live; not duplicated here.
    document_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_records.id"),
        nullable=False,
        index=True,
    )

    document_type = Column(String(48), nullable=False, index=True)

    service_date_from = Column(Date, nullable=True)
    service_date_to = Column(Date, nullable=True)

    # The date the payer/clearinghouse response itself represents (i.e.
    # "as of" date on the eligibility report), distinct from
    # created_at/uploaded_at which is when SNS received the file.
    verification_date = Column(Date, nullable=True)

    uploaded_by_user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    uploaded_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Version chain: uploading a newer eligibility response for the same
    # coverage creates a NEW row and points it at the row it replaces --
    # the original upload is never overwritten or deleted (append-only).
    supersedes_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("eligibility_source_documents.id"),
        nullable=True,
        index=True,
    )

    status = Column(String(16), nullable=False, server_default="ACTIVE", index=True)

    # Phase A -- operational upload workflow. version is 1 for a brand
    # new document, prior.version + 1 when supersedes_document_id is set
    # -- an explicit column so callers never have to walk the
    # supersession chain just to label "which version is this".
    notes = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, server_default="1")

    parser_status = Column(
        String(16), nullable=False, server_default="UNPARSED", index=True
    )
    parser_version = Column(String(32), nullable=True)

    __table_args__ = (
        Index("ix_esd_tenant_patient", "tenant_id", "patient_id"),
        Index("ix_esd_patient_status", "patient_id", "status"),
    )
