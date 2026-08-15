# models/hospitalization_prevention.py

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class FamilyConcernCategory(Base):
    __tablename__ = "family_concern_categories"

    category_key = Column(String, primary_key=True)
    display_name = Column(String, nullable=True)
    active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class FamilyConcernItem(Base):
    __tablename__ = "family_concern_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    benefit_period_id = Column(UUID(as_uuid=True), ForeignKey("benefit_periods.id"), nullable=True, index=True)

    concern_category = Column(String, nullable=True, index=True)
    concern_text = Column(Text, nullable=False)
    concern_status = Column(String, nullable=True, index=True)

    source_type = Column(String, nullable=True)
    source_table = Column(String, nullable=True)
    source_record_id = Column(UUID(as_uuid=True), nullable=True)
    source_discipline = Column(String, nullable=True)
    source_author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    source_note_date = Column(DateTime(timezone=True), nullable=True)
    source_excerpt = Column(Text, nullable=True)

    harvest_method = Column(String, nullable=True)
    confidence = Column(String, nullable=True)

    clinician_review_status = Column(String, nullable=True, index=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_note = Column(Text, nullable=True)

    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_note = Column(Text, nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class FamilyConcernCluster(Base):
    __tablename__ = "family_concern_clusters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    benefit_period_id = Column(UUID(as_uuid=True), ForeignKey("benefit_periods.id"), nullable=True, index=True)

    primary_category = Column(
        String,
        ForeignKey("family_concern_categories.category_key"),
        nullable=True,
        index=True,
    )
    cluster_title = Column(String, nullable=True)
    cluster_summary = Column(Text, nullable=True)
    cluster_status = Column(String, nullable=True, index=True)

    occurrence_count = Column(Integer, nullable=True)
    discipline_count = Column(Integer, nullable=True)
    first_concern_at = Column(DateTime(timezone=True), nullable=True)
    last_concern_at = Column(DateTime(timezone=True), nullable=True)

    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_note = Column(Text, nullable=True)

    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_note = Column(Text, nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class FamilyRiskAssessment(Base):
    __tablename__ = "family_risk_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    benefit_period_id = Column(UUID(as_uuid=True), ForeignKey("benefit_periods.id"), nullable=True, index=True)

    risk_level = Column(String, nullable=True, index=True)
    suggested_risk_level = Column(String, nullable=True)
    risk_score = Column(Integer, nullable=True)
    risk_summary = Column(Text, nullable=True)
    source_facts = Column(JSONB, nullable=True)

    clinician_review_required = Column(Boolean, nullable=False, server_default=text("true"))

    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_note = Column(Text, nullable=True)

    followup_required = Column(Boolean, nullable=True)
    resolved = Column(Boolean, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_note = Column(Text, nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class FamilyEducationTask(Base):
    __tablename__ = "family_education_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    benefit_period_id = Column(UUID(as_uuid=True), ForeignKey("benefit_periods.id"), nullable=True, index=True)

    family_risk_assessment_id = Column(UUID(as_uuid=True), ForeignKey("family_risk_assessments.id"), nullable=True, index=True)
    family_concern_cluster_id = Column(UUID(as_uuid=True), ForeignKey("family_concern_clusters.id"), nullable=True, index=True)

    education_topic = Column(String, nullable=True, index=True)
    education_title = Column(String, nullable=True)
    education_summary = Column(Text, nullable=True)

    assigned_discipline = Column(String, nullable=True)
    assigned_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    task_status = Column(String, nullable=True, index=True)
    priority_level = Column(String, nullable=True)
    due_date = Column(Date, nullable=True)

    completed_at = Column(DateTime(timezone=True), nullable=True)
    completion_evidence = Column(Text, nullable=True)
    completion_note = Column(Text, nullable=True)

    followup_required = Column(Boolean, nullable=True)
    followup_due_date = Column(Date, nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class TeachBackRecord(Base):
    __tablename__ = "teach_back_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    benefit_period_id = Column(UUID(as_uuid=True), ForeignKey("benefit_periods.id"), nullable=True, index=True)

    family_education_task_id = Column(UUID(as_uuid=True), ForeignKey("family_education_tasks.id"), nullable=True, index=True)
    family_risk_assessment_id = Column(UUID(as_uuid=True), ForeignKey("family_risk_assessments.id"), nullable=True, index=True)
    family_concern_cluster_id = Column(UUID(as_uuid=True), ForeignKey("family_concern_clusters.id"), nullable=True, index=True)

    participant_name = Column(String, nullable=True)
    participant_relationship = Column(String, nullable=True)

    educator_discipline = Column(String, nullable=True)
    educator_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    comprehension_status = Column(String, nullable=True, index=True)
    teach_back_response = Column(Text, nullable=True)
    knowledge_gaps = Column(Text, nullable=True)

    reinforcement_required = Column(Boolean, nullable=True)
    followup_required = Column(Boolean, nullable=True)
    followup_due_date = Column(Date, nullable=True)

    successful_teach_back = Column(Boolean, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class DiseaseProcessAlignmentReview(Base):
    __tablename__ = "disease_process_alignment_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    benefit_period_id = Column(UUID(as_uuid=True), ForeignKey("benefit_periods.id"), nullable=True, index=True)

    family_concern_cluster_id = Column(UUID(as_uuid=True), ForeignKey("family_concern_clusters.id"), nullable=True, index=True)
    family_risk_assessment_id = Column(UUID(as_uuid=True), ForeignKey("family_risk_assessments.id"), nullable=True, index=True)

    alignment_status = Column(String, nullable=True, index=True)
    disease_process_topic = Column(String, nullable=True)
    family_understanding_level = Column(String, nullable=True)

    misunderstanding_identified = Column(Boolean, nullable=True)
    misunderstanding_summary = Column(Text, nullable=True)
    clinical_alignment_summary = Column(Text, nullable=True)

    education_recommended = Column(Boolean, nullable=True)
    idg_discussion_required = Column(Boolean, nullable=True)
    physician_review_required = Column(Boolean, nullable=True)

    review_status = Column(String, nullable=True, index=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_note = Column(Text, nullable=True)

    resolved = Column(Boolean, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_note = Column(Text, nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class DiseaseProcessInterventionReview(Base):
    __tablename__ = "disease_process_intervention_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    benefit_period_id = Column(UUID(as_uuid=True), ForeignKey("benefit_periods.id"), nullable=True, index=True)

    disease_process_alignment_review_id = Column(UUID(as_uuid=True), ForeignKey("disease_process_alignment_reviews.id"), nullable=True, index=True)
    family_concern_cluster_id = Column(UUID(as_uuid=True), ForeignKey("family_concern_clusters.id"), nullable=True, index=True)

    intervention_type = Column(String, nullable=True, index=True)
    intervention_summary = Column(Text, nullable=True)
    intervention_rationale = Column(Text, nullable=True)
    intervention_status = Column(String, nullable=True, index=True)
    intervention_effective = Column(Boolean, nullable=True)

    followup_required = Column(Boolean, nullable=True)
    followup_due_date = Column(Date, nullable=True)
    education_required = Column(Boolean, nullable=True)
    escalation_required = Column(Boolean, nullable=True)
    idg_review_required = Column(Boolean, nullable=True)
    physician_review_required = Column(Boolean, nullable=True)

    completed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_note = Column(Text, nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class MedicationReconciliationReview(Base):
    __tablename__ = "medication_reconciliation_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    benefit_period_id = Column(UUID(as_uuid=True), ForeignKey("benefit_periods.id"), nullable=True, index=True)

    family_risk_assessment_id = Column(UUID(as_uuid=True), ForeignKey("family_risk_assessments.id"), nullable=True, index=True)

    review_status = Column(String, nullable=True, index=True)
    total_medications = Column(Integer, nullable=True)
    active_medications = Column(Integer, nullable=True)

    duplicate_therapy_detected = Column(Boolean, nullable=True)
    medication_conflicts_detected = Column(Boolean, nullable=True)
    high_risk_medications_detected = Column(Boolean, nullable=True)
    medication_adherence_concern = Column(Boolean, nullable=True)
    caregiver_medication_confusion = Column(Boolean, nullable=True)

    medication_reconciliation_summary = Column(Text, nullable=True)
    identified_issues = Column(JSONB, nullable=True)
    recommended_actions = Column(JSONB, nullable=True)

    physician_review_required = Column(Boolean, nullable=True)
    idg_review_required = Column(Boolean, nullable=True)
    intervention_required = Column(Boolean, nullable=True)
    intervention_completed = Column(Boolean, nullable=True)
    intervention_completed_at = Column(DateTime(timezone=True), nullable=True)

    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_note = Column(Text, nullable=True)

    resolved = Column(Boolean, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_note = Column(Text, nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class BehavioralEscalationReview(Base):
    __tablename__ = "behavioral_escalation_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    benefit_period_id = Column(UUID(as_uuid=True), ForeignKey("benefit_periods.id"), nullable=True, index=True)

    family_concern_cluster_id = Column(UUID(as_uuid=True), ForeignKey("family_concern_clusters.id"), nullable=True, index=True)
    family_risk_assessment_id = Column(UUID(as_uuid=True), ForeignKey("family_risk_assessments.id"), nullable=True, index=True)

    escalation_level = Column(String, nullable=True, index=True)
    escalation_category = Column(String, nullable=True, index=True)
    escalation_summary = Column(Text, nullable=True)
    observed_behavior = Column(Text, nullable=True)
    triggering_event = Column(Text, nullable=True)
    contributing_factors = Column(Text, nullable=True)
    caregiver_impact = Column(Text, nullable=True)

    patient_safety_risk = Column(Boolean, nullable=True)
    caregiver_safety_risk = Column(Boolean, nullable=True)
    hospitalization_risk = Column(Boolean, nullable=True)

    physician_notification_required = Column(Boolean, nullable=True)
    idg_review_required = Column(Boolean, nullable=True)
    intervention_required = Column(Boolean, nullable=True)
    intervention_plan = Column(Text, nullable=True)
    intervention_completed = Column(Boolean, nullable=True)
    intervention_completed_at = Column(DateTime(timezone=True), nullable=True)

    review_status = Column(String, nullable=True, index=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_note = Column(Text, nullable=True)

    resolved = Column(Boolean, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_note = Column(Text, nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class HospitalizationPreventionSummary(Base):
    __tablename__ = "hospitalization_prevention_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    benefit_period_id = Column(UUID(as_uuid=True), ForeignKey("benefit_periods.id"), nullable=True, index=True)

    family_risk_assessment_id = Column(UUID(as_uuid=True), ForeignKey("family_risk_assessments.id"), nullable=True, index=True)

    summary_period_start = Column(DateTime(timezone=True), nullable=True)
    summary_period_end = Column(DateTime(timezone=True), nullable=True)

    risk_level = Column(String, nullable=True, index=True)
    active_concern_count = Column(Integer, nullable=True)
    active_cluster_count = Column(Integer, nullable=True)
    open_education_task_count = Column(Integer, nullable=True)
    completed_education_task_count = Column(Integer, nullable=True)
    successful_teach_back_count = Column(Integer, nullable=True)
    failed_teach_back_count = Column(Integer, nullable=True)
    followup_required_count = Column(Integer, nullable=True)

    hospitalization_risk_summary = Column(Text, nullable=True)
    priority_interventions = Column(JSONB, nullable=True)
    unresolved_barriers = Column(JSONB, nullable=True)
    recommended_actions = Column(JSONB, nullable=True)

    idg_discussion_required = Column(Boolean, nullable=True)
    physician_review_required = Column(Boolean, nullable=True)
    followup_required = Column(Boolean, nullable=True)

    finalized = Column(Boolean, nullable=True)
    finalized_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    finalized_at = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False)