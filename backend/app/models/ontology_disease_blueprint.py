# models/ontology_disease_blueprint.py
"""
SNS Clinical Ontology -- Disease Blueprint (Phase 1 / 1A / 1B).

Disease-agnostic clinical intelligence knowledge base. These tables store
authored clinical knowledge (which body systems exist, what a disease is,
what findings/symptoms/labs/complications/etc it is commonly associated
with) -- NEVER patient-specific facts.

Hard rules enforced by this design (per SNS Ontology Build spec):
    - No patient_id / tenant_id anywhere in this file. This is reference
      data, shared system-wide, identical to how `icd10_master` works.
    - Ontology relationships and evidence rules may only ever produce
      review prompts / documentation support -- never write a patient
      fact directly. That constraint is enforced in the service layer,
      not the schema, but the schema keeps concept knowledge and patient
      evidence (`patient_evidence_records` / `patient_harvested_signals`)
      in entirely separate tables so the two can never be confused.

Organization (Level 1 -> Level 2):
    OntologyBodySystem (Cardiovascular, Neurologic, ...)
        -> OntologyDisease (CHF, CAD, Stroke, ...)
            -> OntologyDiseaseSymptom
            -> OntologyDiseaseFinding
            -> OntologyDiseaseLab
            -> OntologyDiseaseDiagnosticTest
            -> OntologyDiseaseComplication
            -> OntologyDiseaseFunctionalImpact
            -> OntologyDiseaseNutritionalImpact
            -> OntologyDiseasePrognosticIndicator
            -> OntologyDiseaseTreatment
            -> OntologyDiseaseMedication
            -> OntologyDiseasePsychosocialConcern
            -> OntologyDiseaseSpiritualConcern
            -> OntologyDiseaseInterdisciplinaryTrigger

Cross-cutting (Section 15 / 16):
    OntologyRelationship -- generic SOURCE_CONCEPT / RELATIONSHIP_TYPE /
        TARGET_CONCEPT edges for relationships that are not a simple
        "disease owns this row" link (e.g. Complication -> Functional
        Impact, Psychosocial Concern -> Interdisciplinary Trigger).
    OntologyEvidenceRule -- generic evidence/confidence/review-trigger
        metadata attachable to any concept row above.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import Base

# ---------------------------------------------------------------------------
# LEVEL 1: BODY SYSTEM
# ---------------------------------------------------------------------------


class OntologyBodySystem(Base):
    """Top-level grouping (Cardiovascular, Neurologic, ...). Reference data."""

    __tablename__ = "ontology_body_system"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    system_name = Column(String(128), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, server_default=text("true"))

    disease_families = relationship("OntologyDiseaseFamily", back_populates="body_system")

    __table_args__ = (
        CheckConstraint("length(trim(system_name)) > 0", name="ck_ontology_body_system_name_not_blank"),
    )


# ---------------------------------------------------------------------------
# LEVEL 2: DISEASE FAMILY (Tier 2)
# ---------------------------------------------------------------------------


class OntologyDiseaseFamily(Base):
    """Disease family grouping within a body system (e.g. Cerebrovascular
    Disease, Dementia Disorders within Neurologic System). Reference data."""

    __tablename__ = "ontology_disease_family"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    body_system_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ontology_body_system.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    family_name = Column(String(128), nullable=False, index=True)
    description = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, server_default=text("true"))

    body_system = relationship("OntologyBodySystem", back_populates="disease_families")
    diseases = relationship("OntologyDisease", back_populates="disease_family")

    __table_args__ = (
        UniqueConstraint("body_system_id", "family_name", name="uq_ontology_disease_family_system_name"),
        CheckConstraint("length(trim(family_name)) > 0", name="ck_ontology_disease_family_name_not_blank"),
    )


# ---------------------------------------------------------------------------
# LEVEL 3: DISEASE IDENTITY (Section 1)
# ---------------------------------------------------------------------------


class OntologyDisease(Base):
    """Disease identity + description (Section 1). One row per disease."""

    __tablename__ = "ontology_disease"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    disease_family_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ontology_disease_family.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    disease_name = Column(String(255), nullable=False, unique=True, index=True)
    disease_category = Column(String(64), nullable=True, index=True)
    primary_organ = Column(String(128), nullable=True)
    disease_type = Column(String(128), nullable=True)

    disease_description = Column(Text, nullable=True)
    clinical_purpose = Column(Text, nullable=True)
    hospice_relevance = Column(Text, nullable=True)

    active = Column(Boolean, nullable=False, server_default=text("true"))

    disease_family = relationship("OntologyDiseaseFamily", back_populates="diseases")
    symptoms = relationship("OntologyDiseaseSymptom", back_populates="disease", cascade="all, delete-orphan")
    findings = relationship("OntologyDiseaseFinding", back_populates="disease", cascade="all, delete-orphan")
    labs = relationship("OntologyDiseaseLab", back_populates="disease", cascade="all, delete-orphan")
    diagnostic_tests = relationship(
        "OntologyDiseaseDiagnosticTest", back_populates="disease", cascade="all, delete-orphan"
    )
    complications = relationship(
        "OntologyDiseaseComplication", back_populates="disease", cascade="all, delete-orphan"
    )
    functional_impacts = relationship(
        "OntologyDiseaseFunctionalImpact", back_populates="disease", cascade="all, delete-orphan"
    )
    nutritional_impacts = relationship(
        "OntologyDiseaseNutritionalImpact", back_populates="disease", cascade="all, delete-orphan"
    )
    prognostic_indicators = relationship(
        "OntologyDiseasePrognosticIndicator", back_populates="disease", cascade="all, delete-orphan"
    )
    treatments = relationship("OntologyDiseaseTreatment", back_populates="disease", cascade="all, delete-orphan")
    medications = relationship("OntologyDiseaseMedication", back_populates="disease", cascade="all, delete-orphan")
    psychosocial_concerns = relationship(
        "OntologyDiseasePsychosocialConcern", back_populates="disease", cascade="all, delete-orphan"
    )
    spiritual_concerns = relationship(
        "OntologyDiseaseSpiritualConcern", back_populates="disease", cascade="all, delete-orphan"
    )
    interdisciplinary_triggers = relationship(
        "OntologyDiseaseInterdisciplinaryTrigger", back_populates="disease", cascade="all, delete-orphan"
    )
    hospice_eligibility_support = relationship(
        "OntologyDiseaseHospiceEligibilitySupport", back_populates="disease", cascade="all, delete-orphan"
    )
    treatment_limitations = relationship(
        "OntologyDiseaseTreatmentLimitation", back_populates="disease", cascade="all, delete-orphan"
    )
    end_stage_findings = relationship(
        "OntologyDiseaseEndStageFinding", back_populates="disease", cascade="all, delete-orphan"
    )
    validation_results = relationship(
        "OntologyDiseaseValidationResult", back_populates="disease", cascade="all, delete-orphan"
    )
    variants = relationship(
        "OntologyDiseaseVariant", back_populates="disease", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("length(trim(disease_name)) > 0", name="ck_ontology_disease_name_not_blank"),
    )


# ---------------------------------------------------------------------------
# Section 2: EXPECTED SYMPTOMS
# ---------------------------------------------------------------------------


class OntologyDiseaseSymptom(Base):
    __tablename__ = "ontology_disease_symptom"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id = Column(
        UUID(as_uuid=True), ForeignKey("ontology_disease.id", ondelete="CASCADE"), nullable=False, index=True
    )

    symptom_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    hospice_relevance = Column(Text, nullable=True)
    severity_scale = Column(String(128), nullable=True)

    disease = relationship("OntologyDisease", back_populates="symptoms")

    __table_args__ = (
        UniqueConstraint("disease_id", "symptom_name", name="uq_ontology_disease_symptom_disease_name"),
    )


# ---------------------------------------------------------------------------
# Section 3: EXPECTED CLINICAL FINDINGS
# ---------------------------------------------------------------------------


class OntologyDiseaseFinding(Base):
    __tablename__ = "ontology_disease_finding"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id = Column(
        UUID(as_uuid=True), ForeignKey("ontology_disease.id", ondelete="CASCADE"), nullable=False, index=True
    )

    finding_name = Column(String(255), nullable=False)
    finding_description = Column(Text, nullable=True)
    severity_levels = Column(JSONB, nullable=True)
    supporting_evidence_types = Column(JSONB, nullable=True)

    disease = relationship("OntologyDisease", back_populates="findings")

    __table_args__ = (
        UniqueConstraint("disease_id", "finding_name", name="uq_ontology_disease_finding_disease_name"),
    )


# ---------------------------------------------------------------------------
# Section 4: EXPECTED LABORATORY FINDINGS
# ---------------------------------------------------------------------------


class OntologyDiseaseLab(Base):
    __tablename__ = "ontology_disease_lab"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id = Column(
        UUID(as_uuid=True), ForeignKey("ontology_disease.id", ondelete="CASCADE"), nullable=False, index=True
    )

    lab_name = Column(String(255), nullable=False)
    normal_range = Column(String(255), nullable=True)
    expected_abnormal_range = Column(String(255), nullable=True)
    clinical_significance = Column(Text, nullable=True)
    hospice_significance = Column(Text, nullable=True)

    disease = relationship("OntologyDisease", back_populates="labs")

    __table_args__ = (
        UniqueConstraint("disease_id", "lab_name", name="uq_ontology_disease_lab_disease_name"),
    )


# ---------------------------------------------------------------------------
# Section 5: EXPECTED DIAGNOSTIC TESTS
# ---------------------------------------------------------------------------


class OntologyDiseaseDiagnosticTest(Base):
    __tablename__ = "ontology_disease_diagnostic_test"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id = Column(
        UUID(as_uuid=True), ForeignKey("ontology_disease.id", ondelete="CASCADE"), nullable=False, index=True
    )

    test_name = Column(String(255), nullable=False)
    purpose = Column(Text, nullable=True)
    expected_findings = Column(Text, nullable=True)
    evidence_weight = Column(String(64), nullable=True)

    disease = relationship("OntologyDisease", back_populates="diagnostic_tests")

    __table_args__ = (
        UniqueConstraint("disease_id", "test_name", name="uq_ontology_disease_diagnostic_test_disease_name"),
    )


# ---------------------------------------------------------------------------
# Section 6: EXPECTED COMPLICATIONS
# ---------------------------------------------------------------------------


class OntologyDiseaseComplication(Base):
    __tablename__ = "ontology_disease_complication"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id = Column(
        UUID(as_uuid=True), ForeignKey("ontology_disease.id", ondelete="CASCADE"), nullable=False, index=True
    )

    complication_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    common_occurrence = Column(String(64), nullable=True)
    clinical_significance = Column(Text, nullable=True)

    disease = relationship("OntologyDisease", back_populates="complications")

    __table_args__ = (
        UniqueConstraint("disease_id", "complication_name", name="uq_ontology_disease_complication_disease_name"),
    )


# ---------------------------------------------------------------------------
# Section 7: EXPECTED FUNCTIONAL IMPACTS
# ---------------------------------------------------------------------------


class OntologyDiseaseFunctionalImpact(Base):
    __tablename__ = "ontology_disease_functional_impact"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id = Column(
        UUID(as_uuid=True), ForeignKey("ontology_disease.id", ondelete="CASCADE"), nullable=False, index=True
    )

    impact_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(64), nullable=True)

    disease = relationship("OntologyDisease", back_populates="functional_impacts")

    __table_args__ = (
        UniqueConstraint("disease_id", "impact_name", name="uq_ontology_disease_functional_impact_disease_name"),
    )


# ---------------------------------------------------------------------------
# Section 8: EXPECTED NUTRITIONAL IMPACTS
# ---------------------------------------------------------------------------


class OntologyDiseaseNutritionalImpact(Base):
    __tablename__ = "ontology_disease_nutritional_impact"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id = Column(
        UUID(as_uuid=True), ForeignKey("ontology_disease.id", ondelete="CASCADE"), nullable=False, index=True
    )

    impact_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    clinical_significance = Column(Text, nullable=True)

    disease = relationship("OntologyDisease", back_populates="nutritional_impacts")

    __table_args__ = (
        UniqueConstraint("disease_id", "impact_name", name="uq_ontology_disease_nutritional_impact_disease_name"),
    )


# ---------------------------------------------------------------------------
# Section 9: EXPECTED PROGNOSTIC INDICATORS
# ---------------------------------------------------------------------------


class OntologyDiseasePrognosticIndicator(Base):
    __tablename__ = "ontology_disease_prognostic_indicator"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id = Column(
        UUID(as_uuid=True), ForeignKey("ontology_disease.id", ondelete="CASCADE"), nullable=False, index=True
    )

    indicator_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    supporting_evidence = Column(Text, nullable=True)

    disease = relationship("OntologyDisease", back_populates="prognostic_indicators")

    __table_args__ = (
        UniqueConstraint(
            "disease_id", "indicator_name", name="uq_ontology_disease_prognostic_indicator_disease_name"
        ),
    )


# ---------------------------------------------------------------------------
# Section 9B: HOSPICE ELIGIBILITY SUPPORT
# ---------------------------------------------------------------------------


class OntologyDiseaseHospiceEligibilitySupport(Base):
    """
    Disease-specific evidence indicators that may support (never determine)
    hospice terminal-prognosis review, distinct from general prognostic
    decline indicators (Section 9). This table never produces an
    eligibility decision itself -- eligibility_decisions / LCD pathway
    review remain the sole authority for that; this is documentation
    support only.
    """

    __tablename__ = "ontology_disease_hospice_eligibility_support"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id = Column(
        UUID(as_uuid=True), ForeignKey("ontology_disease.id", ondelete="CASCADE"), nullable=False, index=True
    )

    indicator_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    supporting_evidence = Column(Text, nullable=True)
    lcd_reference = Column(String(255), nullable=True)

    disease = relationship("OntologyDisease", back_populates="hospice_eligibility_support")

    __table_args__ = (
        UniqueConstraint(
            "disease_id",
            "indicator_name",
            name="uq_ontology_disease_hospice_eligibility_support_disease_name",
        ),
    )


# ---------------------------------------------------------------------------
# Section 10: EXPECTED TREATMENTS
# ---------------------------------------------------------------------------


class OntologyDiseaseTreatment(Base):
    __tablename__ = "ontology_disease_treatment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id = Column(
        UUID(as_uuid=True), ForeignKey("ontology_disease.id", ondelete="CASCADE"), nullable=False, index=True
    )

    treatment_name = Column(String(255), nullable=False)
    # DISEASE_DIRECTED | SUPPORTIVE | HOSPICE
    treatment_category = Column(String(32), nullable=False)
    description = Column(Text, nullable=True)

    disease = relationship("OntologyDisease", back_populates="treatments")

    __table_args__ = (
        UniqueConstraint(
            "disease_id", "treatment_name", "treatment_category", name="uq_ontology_disease_treatment_disease_name"
        ),
        CheckConstraint(
            "treatment_category IN ('DISEASE_DIRECTED', 'SUPPORTIVE', 'HOSPICE')",
            name="ck_ontology_disease_treatment_category",
        ),
    )


# ---------------------------------------------------------------------------
# Section 11: EXPECTED MEDICATIONS
# ---------------------------------------------------------------------------


class OntologyDiseaseMedication(Base):
    __tablename__ = "ontology_disease_medication"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id = Column(
        UUID(as_uuid=True), ForeignKey("ontology_disease.id", ondelete="CASCADE"), nullable=False, index=True
    )

    medication_name = Column(String(255), nullable=False)
    drug_class = Column(String(255), nullable=True)
    purpose = Column(Text, nullable=True)
    expected_benefits = Column(Text, nullable=True)
    common_side_effects = Column(Text, nullable=True)
    hospice_relevance = Column(Text, nullable=True)

    disease = relationship("OntologyDisease", back_populates="medications")

    __table_args__ = (
        UniqueConstraint("disease_id", "medication_name", name="uq_ontology_disease_medication_disease_name"),
    )


# ---------------------------------------------------------------------------
# Section 12: PSYCHOSOCIAL CONSIDERATIONS
# ---------------------------------------------------------------------------


class OntologyDiseasePsychosocialConcern(Base):
    __tablename__ = "ontology_disease_psychosocial_concern"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id = Column(
        UUID(as_uuid=True), ForeignKey("ontology_disease.id", ondelete="CASCADE"), nullable=False, index=True
    )

    concern_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    disease = relationship("OntologyDisease", back_populates="psychosocial_concerns")

    __table_args__ = (
        UniqueConstraint(
            "disease_id", "concern_name", name="uq_ontology_disease_psychosocial_concern_disease_name"
        ),
    )


# ---------------------------------------------------------------------------
# Section 13: SPIRITUAL CONSIDERATIONS
# ---------------------------------------------------------------------------


class OntologyDiseaseSpiritualConcern(Base):
    __tablename__ = "ontology_disease_spiritual_concern"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id = Column(
        UUID(as_uuid=True), ForeignKey("ontology_disease.id", ondelete="CASCADE"), nullable=False, index=True
    )

    concern_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    disease = relationship("OntologyDisease", back_populates="spiritual_concerns")

    __table_args__ = (
        UniqueConstraint("disease_id", "concern_name", name="uq_ontology_disease_spiritual_concern_disease_name"),
    )


# ---------------------------------------------------------------------------
# Section 14: INTERDISCIPLINARY TRIGGERS
# ---------------------------------------------------------------------------


class OntologyDiseaseInterdisciplinaryTrigger(Base):
    __tablename__ = "ontology_disease_interdisciplinary_trigger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id = Column(
        UUID(as_uuid=True), ForeignKey("ontology_disease.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # RN | PHYSICIAN | MSW | BSW | CHAPLAIN | VOLUNTEER | BEREAVEMENT | DIETICIAN | PT | OT | IDG
    discipline = Column(String(64), nullable=False)
    trigger_condition = Column(Text, nullable=False)

    disease = relationship("OntologyDisease", back_populates="interdisciplinary_triggers")

    __table_args__ = (
        CheckConstraint(
            "discipline IN ('RN', 'PHYSICIAN', 'MSW', 'BSW', 'CHAPLAIN', 'VOLUNTEER', "
            "'BEREAVEMENT', 'DIETICIAN', 'PT', 'OT', 'IDG')",
            name="ck_ontology_disease_interdisciplinary_trigger_discipline",
        ),
    )


# ---------------------------------------------------------------------------
# Section 15: ONTOLOGY RELATIONSHIPS (generic, cross-domain edges)
# ---------------------------------------------------------------------------


class OntologyRelationship(Base):
    """
    Generic SOURCE_CONCEPT -> RELATIONSHIP_TYPE -> TARGET_CONCEPT edge for
    relationships that cross domains and are not already expressed by a
    disease_id foreign key above (e.g. Complication -> Functional Impact,
    Psychosocial Concern -> Interdisciplinary Trigger).

    concept_type values match the table each concept row lives in, e.g.
    DISEASE, FINDING, SYMPTOM, COMPLICATION, FUNCTIONAL_IMPACT,
    NUTRITIONAL_IMPACT, PSYCHOSOCIAL_CONCERN, SPIRITUAL_CONCERN,
    INTERDISCIPLINARY_TRIGGER, PROGNOSTIC_INDICATOR.
    """

    __tablename__ = "ontology_relationship"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    source_concept_type = Column(String(64), nullable=False, index=True)
    source_concept_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    relationship_type = Column(String(64), nullable=False, index=True)

    target_concept_type = Column(String(64), nullable=False, index=True)
    target_concept_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    description = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, server_default=text("true"))

    __table_args__ = (
        UniqueConstraint(
            "source_concept_type",
            "source_concept_id",
            "relationship_type",
            "target_concept_type",
            "target_concept_id",
            name="uq_ontology_relationship_edge",
        ),
    )


# ---------------------------------------------------------------------------
# Section 16: EVIDENCE RULES (generic, attachable to any concept row above)
# ---------------------------------------------------------------------------


class OntologyEvidenceRule(Base):
    """
    Evidence/confidence/review-trigger metadata attachable to any ontology
    concept row. Never a patient fact. `patient_fact_requires_evidence`
    documents that if this concept is ever surfaced for a specific patient,
    it must be backed by patient_evidence_records / patient_harvested_signals
    before being treated as documented -- undocumented stays UNANSWERED,
    contradictory stays CONFLICTING, and this rule can never itself flip
    either state to YES.
    """

    __tablename__ = "ontology_evidence_rule"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    concept_type = Column(String(64), nullable=False, index=True)
    concept_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    evidence_source = Column(String(255), nullable=True)
    evidence_type = Column(String(64), nullable=True)
    confidence = Column(String(32), nullable=True)
    review_trigger = Column(String(128), nullable=True)

    patient_fact_requires_evidence = Column(Boolean, nullable=False, server_default=text("true"))
    notes = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("concept_type", "concept_id", name="uq_ontology_evidence_rule_concept"),
    )


# ---------------------------------------------------------------------------
# Section 17: TREATMENT LIMITATIONS (A-K domain E)
# ---------------------------------------------------------------------------


class OntologyDiseaseTreatmentLimitation(Base):
    """
    Disease-specific treatment limitations (A-K domain E): failure,
    intolerance, refusal, non-candidacy, discontinuation, contraindication,
    or comfort-focused transition. Distinct from OntologyDiseaseTreatment,
    which represents recommended treatments, not their limitations.
    """

    __tablename__ = "ontology_disease_treatment_limitation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id = Column(
        UUID(as_uuid=True), ForeignKey("ontology_disease.id", ondelete="CASCADE"), nullable=False, index=True
    )

    limitation_name = Column(String(255), nullable=False)
    # OPTIMALLY_TREATED | TREATMENT_FAILED | TREATMENT_INTOLERANT | NOT_A_CANDIDATE |
    # TREATMENT_DECLINED | TREATMENT_DISCONTINUED | TREATMENT_CONTRAINDICATED | COMFORT_FOCUSED
    limitation_category = Column(String(32), nullable=False)
    description = Column(Text, nullable=True)
    evidence_requirement = Column(Text, nullable=True)
    hospice_relevance = Column(Text, nullable=True)

    active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    disease = relationship("OntologyDisease", back_populates="treatment_limitations")

    __table_args__ = (
        UniqueConstraint(
            "disease_id", "limitation_name", "limitation_category",
            name="uq_ontology_disease_treatment_limitation_disease_name",
        ),
        CheckConstraint(
            "limitation_category IN ("
            "'OPTIMALLY_TREATED', 'TREATMENT_FAILED', 'TREATMENT_INTOLERANT', 'NOT_A_CANDIDATE', "
            "'TREATMENT_DECLINED', 'TREATMENT_DISCONTINUED', 'TREATMENT_CONTRAINDICATED', 'COMFORT_FOCUSED'"
            ")",
            name="ck_ontology_disease_treatment_limitation_category",
        ),
    )


# ---------------------------------------------------------------------------
# Section 18: END-STAGE FINDINGS (A-K domain H)
# ---------------------------------------------------------------------------


class OntologyDiseaseEndStageFinding(Base):
    """
    Disease-specific advanced/end-stage/refractory/terminal manifestations
    (A-K domain H). Distinct from OntologyDiseaseFinding, which represents
    generic clinical findings across all disease stages.
    """

    __tablename__ = "ontology_disease_end_stage_finding"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id = Column(
        UUID(as_uuid=True), ForeignKey("ontology_disease.id", ondelete="CASCADE"), nullable=False, index=True
    )

    finding_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    evidence_requirement = Column(Text, nullable=True)
    clinical_significance = Column(Text, nullable=True)
    hospice_relevance = Column(Text, nullable=True)

    active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    disease = relationship("OntologyDisease", back_populates="end_stage_findings")

    __table_args__ = (
        UniqueConstraint(
            "disease_id", "finding_name", name="uq_ontology_disease_end_stage_finding_disease_name"
        ),
    )


# ---------------------------------------------------------------------------
# Section 19: VALIDATION RESULTS (A-K domain K)
# ---------------------------------------------------------------------------


class OntologyDiseaseValidationResult(Base):
    """
    Persistent validation run results per disease (A-K domain K). A
    validation run is never "complete" from terminal output alone -- it
    must leave a queryable record here.
    """

    __tablename__ = "ontology_disease_validation_result"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id = Column(
        UUID(as_uuid=True), ForeignKey("ontology_disease.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # DUPLICATE | ORPHAN | HIERARCHY | DOMAIN_COMPLETENESS | EVIDENCE_COVERAGE |
    # RELATIONSHIP_INTEGRITY | SOURCE_PROVENANCE
    validation_type = Column(String(64), nullable=False)
    # PASS | FAIL | WARNING
    validation_status = Column(String(16), nullable=False)
    details = Column(Text, nullable=True)
    error_count = Column(Integer, nullable=False, server_default=text("0"))
    warning_count = Column(Integer, nullable=False, server_default=text("0"))
    validated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    validator_version = Column(String(32), nullable=True)

    active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    disease = relationship("OntologyDisease", back_populates="validation_results")

    __table_args__ = (
        CheckConstraint(
            "validation_type IN ("
            "'DUPLICATE', 'ORPHAN', 'HIERARCHY', 'DOMAIN_COMPLETENESS', 'EVIDENCE_COVERAGE', "
            "'RELATIONSHIP_INTEGRITY', 'SOURCE_PROVENANCE'"
            ")",
            name="ck_ontology_disease_validation_result_type",
        ),
        CheckConstraint(
            "validation_status IN ('PASS', 'FAIL', 'WARNING')",
            name="ck_ontology_disease_validation_result_status",
        ),
    )


# ---------------------------------------------------------------------------
# Section 20: FIVE-TIER FOUNDATION -- TIER 4 (DISEASE VARIANT / CLINICAL
# CONTEXT) AND THE TIER 5 APPLICABILITY EDGE TABLE
# ---------------------------------------------------------------------------
#
# Universal, body-system-agnostic extension of the ontology hierarchy:
#
#   Tier 1  OntologyBodySystem
#     Tier 2  OntologyDiseaseFamily
#       Tier 3  OntologyDisease            (canonical disease -- unchanged)
#         Tier 4  OntologyDiseaseVariant   (disease variant / clinical context)
#           Tier 5  existing atomic concept tables (symptom, finding, lab,
#                   diagnostic test, complication, prognostic indicator,
#                   treatment limitation, functional impact, nutritional
#                   impact, end-stage finding, hospice eligibility support,
#                   treatment, medication, psychosocial concern, spiritual
#                   concern) -- unchanged, linked to Tier 4 only through
#                   OntologyConceptVariantApplicability, never through a
#                   new foreign key column on the Tier 5 tables themselves.
#
# Tier 4 is intentionally one generic table for every body system (Stroke
# mechanism/territory/laterality today; Oncology primary site/histology/
# stage/metastatic destination tomorrow) -- never a disease-specific or
# system-specific column or table. A Tier 4 row may recursively nest under
# another Tier 4 row via parent_variant_id (e.g. "Middle Cerebral Artery
# Stroke" as a child of "Ischemic Stroke") without requiring a new table.
#
# A single Tier 5 concept may be clinically applicable to more than one
# Tier 4 variant at once (e.g. a finding that is both left-hemisphere- and
# MCA-territory-specific) -- so the association is stored as a many-to-many
# edge (OntologyConceptVariantApplicability), never as a single variant_id
# column bolted onto each Tier 5 table.
#
# Both tables carry the same evidence/patient-fact safeguard as the rest of
# the ontology: they store general clinical-reasoning knowledge only.
# `evidence_requirement` documents what patient-record evidence would be
# needed before treating the association as a documented patient fact --
# consistent with `patient_fact_requires_evidence = true` on
# OntologyEvidenceRule for every Tier 5 concept row.
# ---------------------------------------------------------------------------


class OntologyDiseaseVariant(Base):
    """
    Tier 4: Disease Variant / Clinical Context. A universal, dimension-
    tagged sub-classification of a Tier 3 canonical disease (mechanism,
    anatomical location, vascular territory, hemisphere, dominance,
    laterality, disease phase, stage, histology, molecular subtype, etc.)
    Never a new canonical disease row, never a body-system- or disease-
    specific column/table.
    """

    __tablename__ = "ontology_disease_variant"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id = Column(
        UUID(as_uuid=True), ForeignKey("ontology_disease.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_variant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ontology_disease_variant.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    variant_name = Column(String(255), nullable=False)
    normalized_name = Column(String(255), nullable=False, index=True)

    # MECHANISM | PATHOLOGICAL_SUBTYPE | HISTOLOGY | MOLECULAR_SUBTYPE |
    # ANATOMICAL_LOCATION | PRIMARY_SITE | VASCULAR_TERRITORY | HEMISPHERE |
    # DOMINANCE | LATERALITY | CORTICAL_LOCATION | SUBCORTICAL_LOCATION |
    # DEEP_STRUCTURE | BRAINSTEM_LEVEL | CEREBELLAR_LOCATION | CARDIAC_SIDE |
    # CARDIAC_CHAMBER | PHYSIOLOGICAL_PHENOTYPE | SEVERITY_CLASS | STAGE |
    # GRADE | DISEASE_PHASE | RECURRENCE_STATE | METASTATIC_STATE |
    # METASTATIC_DESTINATION | TREATMENT_STATE | RESIDUAL_DEFICIT_STATE
    variant_dimension = Column(String(32), nullable=False, index=True)
    variant_code = Column(String(64), nullable=True)

    description = Column(Text, nullable=True)
    clinical_significance = Column(Text, nullable=True)
    hospice_relevance = Column(Text, nullable=True)
    evidence_requirement = Column(Text, nullable=True)
    source_reference = Column(Text, nullable=True)

    active = Column(Boolean, nullable=False, server_default=text("true"), index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    disease = relationship("OntologyDisease", back_populates="variants")
    parent_variant = relationship("OntologyDiseaseVariant", remote_side=[id], back_populates="child_variants")
    child_variants = relationship(
        "OntologyDiseaseVariant", back_populates="parent_variant", cascade="all, delete-orphan"
    )
    applicability_edges = relationship(
        "OntologyConceptVariantApplicability", back_populates="variant", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "disease_id", "variant_dimension", "normalized_name",
            name="uq_ontology_disease_variant_disease_dimension_name",
        ),
        CheckConstraint("length(trim(variant_name)) > 0", name="ck_ontology_disease_variant_name_not_blank"),
        CheckConstraint(
            "variant_dimension IN ("
            "'MECHANISM', 'PATHOLOGICAL_SUBTYPE', 'HISTOLOGY', 'MOLECULAR_SUBTYPE', "
            "'ANATOMICAL_LOCATION', 'PRIMARY_SITE', 'VASCULAR_TERRITORY', 'HEMISPHERE', "
            "'DOMINANCE', 'LATERALITY', 'CORTICAL_LOCATION', 'SUBCORTICAL_LOCATION', "
            "'DEEP_STRUCTURE', 'BRAINSTEM_LEVEL', 'CEREBELLAR_LOCATION', 'CARDIAC_SIDE', "
            "'CARDIAC_CHAMBER', 'PHYSIOLOGICAL_PHENOTYPE', 'SEVERITY_CLASS', 'STAGE', "
            "'GRADE', 'DISEASE_PHASE', 'RECURRENCE_STATE', 'METASTATIC_STATE', "
            "'METASTATIC_DESTINATION', 'TREATMENT_STATE', 'RESIDUAL_DEFICIT_STATE'"
            ")",
            name="ck_ontology_disease_variant_dimension",
        ),
    )


class OntologyConceptVariantApplicability(Base):
    """
    Tier 5 <-> Tier 4 many-to-many applicability edge. Links an existing
    atomic concept row (identified generically by concept_type/concept_id,
    the same pattern already used by OntologyRelationship and
    OntologyEvidenceRule) to one or more OntologyDiseaseVariant rows.

    Stores general AI clinical-knowledge applicability only -- never a
    patient fact. `evidence_requirement` documents what patient-record
    evidence would be needed before the applicability could ever be
    treated as a documented patient-specific finding.
    """

    __tablename__ = "ontology_concept_variant_applicability"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disease_id = Column(
        UUID(as_uuid=True), ForeignKey("ontology_disease.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # SYMPTOM | FINDING | LAB | DIAGNOSTIC_TEST | COMPLICATION |
    # PROGNOSTIC_INDICATOR | TREATMENT_LIMITATION | FUNCTIONAL_IMPACT |
    # NUTRITIONAL_IMPACT | END_STAGE_FINDING | HOSPICE_ELIGIBILITY_SUPPORT |
    # TREATMENT | MEDICATION | PSYCHOSOCIAL_CONCERN | SPIRITUAL_CONCERN
    concept_type = Column(String(64), nullable=False, index=True)
    concept_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    variant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ontology_disease_variant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # APPLIES_TO | EXPECTED_WITH | STRONGLY_ASSOCIATED_WITH | MAY_OCCUR_WITH |
    # SUPPORTS_DIFFERENTIATION | CONTRAINDICATED_FOR | TREATMENT_SPECIFIC_TO |
    # PROGNOSTIC_FOR | END_STAGE_SUPPORT_FOR | HOSPICE_SUPPORT_FOR
    applicability_type = Column(String(32), nullable=False, index=True)

    description = Column(Text, nullable=True)
    evidence_requirement = Column(Text, nullable=True)

    active = Column(Boolean, nullable=False, server_default=text("true"), index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    variant = relationship("OntologyDiseaseVariant", back_populates="applicability_edges")

    __table_args__ = (
        UniqueConstraint(
            "concept_type", "concept_id", "variant_id", "applicability_type",
            name="uq_ontology_concept_variant_applicability_edge",
        ),
        CheckConstraint(
            "applicability_type IN ("
            "'APPLIES_TO', 'EXPECTED_WITH', 'STRONGLY_ASSOCIATED_WITH', 'MAY_OCCUR_WITH', "
            "'SUPPORTS_DIFFERENTIATION', 'CONTRAINDICATED_FOR', 'TREATMENT_SPECIFIC_TO', "
            "'PROGNOSTIC_FOR', 'END_STAGE_SUPPORT_FOR', 'HOSPICE_SUPPORT_FOR'"
            ")",
            name="ck_ontology_concept_variant_applicability_type",
        ),
    )
