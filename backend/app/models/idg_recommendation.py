from __future__ import annotations

"""
IDG recommendation (MSW / CHAPLAIN continuity workflow). Reuses the
existing idg_reviews table as the review container (per the existing
app.services.idg_follow_up_service "extend, don't duplicate" convention)
-- an IDGRecommendation always belongs to exactly one IDGReview.

Distinct from IDGReview.summary / idg_follow_up_service.record_
idg_recommendation(), which store a single free-text recommendation
per review. This table supports MULTIPLE, independently tracked,
typed recommendations per review, each with its own accept/decline
lifecycle -- required because MSW and CHAPLAIN may each contribute a
recommendation without a visit, billable encounter, discipline
assessment, or face-to-face visit, and each must be individually
accepted/declined by an authorized clinician before any POC action is
taken (no_direct_visit is always true for recommendations created this
way; the UI must display "IDG RECOMMENDATION / NO DIRECT VISIT").
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel
from app.models.tenant_mixin import TenantScopedMixin


class IDGRecommendation(TenantScopedMixin, BaseModel):
    __tablename__ = "idg_recommendations"

    # id / created_at / created_by are inherited from BaseModel.
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    idg_review_id = Column(UUID(as_uuid=True), ForeignKey("idg_reviews.id", ondelete="CASCADE"), nullable=False, index=True)

    # Continuity episode-scoping. Nullable for the same legacy reason as
    # PatientDisciplineService.admission_id / IDGReview.admission_id --
    # never inferred, only ever set at creation time from the validated
    # parent IDGReview/PatientDisciplineService admission.
    admission_id = Column(UUID(as_uuid=True), ForeignKey("admissions.id", ondelete="SET NULL"), nullable=True, index=True)

    discipline_service_id = Column(
        UUID(as_uuid=True), ForeignKey("patient_discipline_services.id", ondelete="SET NULL"), nullable=True, index=True
    )
    discipline = Column(String(16), nullable=True)  # MSW / CHAPLAIN -- recommending discipline

    recommendation_type = Column(String(32), nullable=False)
    recommendation_text = Column(Text, nullable=False)

    no_direct_visit = Column(Boolean, nullable=False, server_default=text("true"))

    status = Column(String(16), nullable=False, server_default=text("'PENDING'"), index=True)

    related_patient_issue_id = Column(
        UUID(as_uuid=True), ForeignKey("patient_issues.id", ondelete="SET NULL"), nullable=True
    )

    # True Plan-of-Care linkage (reuses the existing POCProblem/POCGoal/
    # POCIntervention tables -- never a second/competing POC system).
    # Independently nullable: a recommendation may link zero, one, or
    # more of these. Every value is set ONLY at creation time after
    # server-side ownership validation (tenant/patient/current-Admission
    # match via PlanOfCare) -- never inferred, never backfilled, never
    # client-trusted without that validation. requires_poc_change flags
    # that an authorized clinician's review/acceptance is still pending;
    # acceptance of the recommendation itself is NOT equivalent to
    # applying a POC change -- that remains a separate, existing,
    # authorized POC workflow action.
    requires_poc_change = Column(Boolean, nullable=False, server_default=text("false"))
    linked_poc_problem_id = Column(UUID(as_uuid=True), ForeignKey("poc_problems.id", ondelete="SET NULL"), nullable=True, index=True)
    linked_poc_goal_id = Column(UUID(as_uuid=True), ForeignKey("poc_goals.id", ondelete="SET NULL"), nullable=True, index=True)
    linked_poc_intervention_id = Column(
        UUID(as_uuid=True), ForeignKey("poc_interventions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    reviewed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_idg_recommendations_tenant_patient", "tenant_id", "patient_id"),
        Index("ix_idg_recommendations_idg_review", "idg_review_id"),
    )
