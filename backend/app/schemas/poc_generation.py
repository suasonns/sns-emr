from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class POCSource(BaseModel):
    source_type: str
    clinical_note_id: str | None = None
    patient_id: str | None = None
    visit_id: str | None = None
    form_key: str | None = None
    note_type: str | None = None
    discipline: str | None = None


class POCGeneratorMetadata(BaseModel):
    service: str
    version: str
    mode: Literal["draft_only"] = "draft_only"
    requires_clinician_review: bool = True
    auto_finalized: bool = False


class POCEvidence(BaseModel):
    source: str
    value: Any = None


class POCProblem(BaseModel):
    code: str
    label: str


class POCClinicalSummary(BaseModel):
    severity: str | None = None


class POCGoal(BaseModel):
    goal_id: str
    goal_text: str
    status: Literal["DRAFT", "ACCEPTED", "EDITED", "REMOVED"] = "DRAFT"


class POCIntervention(BaseModel):
    discipline: str
    intervention_text: str
    status: Literal["DRAFT", "ACCEPTED", "EDITED", "REMOVED"] = "DRAFT"


class POCDraftItemSource(BaseModel):
    source_type: str
    clinical_note_id: str | None = None


class POCDraftItem(BaseModel):
    poc_id: str
    status: Literal["DRAFT", "ACCEPTED", "EDITED", "REMOVED"] = "DRAFT"

    problem: POCProblem
    clinical_summary: POCClinicalSummary = Field(default_factory=POCClinicalSummary)

    goals: list[POCGoal] = Field(default_factory=list)
    interventions: list[POCIntervention] = Field(default_factory=list)
    evidence: list[POCEvidence] = Field(default_factory=list)

    source: POCDraftItemSource
    created_at: str
    engine_version: str
    requires_clinician_review: bool = True


class POCFunctionalEvidence(BaseModel):
    pps: Any = None
    kps: Any = None
    fast_stage: Any = None
    nyha_class: Any = None


class POCDraft(BaseModel):
    status: Literal[
        "DRAFT_GENERATED",
        "DRAFT_REVIEWED",
        "DRAFT_ACCEPTED",
        "DRAFT_REJECTED",
    ] = "DRAFT_GENERATED"

    source: POCSource

    primary_diagnosis: Any = None
    functional_evidence: POCFunctionalEvidence = Field(
        default_factory=POCFunctionalEvidence
    )

    pocs: list[POCDraftItem] = Field(default_factory=list)

    generated_at: str
    generator: POCGeneratorMetadata


class POCDraftReviewAction(BaseModel):
    poc_id: str
    action: Literal["ACCEPT", "EDIT", "REMOVE"]
    edited_problem_label: str | None = None
    edited_goals: list[POCGoal] | None = None
    edited_interventions: list[POCIntervention] | None = None
    review_note: str | None = None


class POCDraftReviewRequest(BaseModel):
    draft: POCDraft
    reviewer_user_id: str
    actions: list[POCDraftReviewAction] = Field(default_factory=list)


class POCDraftReviewResult(BaseModel):
    status: Literal["REVIEWED"] = "REVIEWED"
    reviewer_user_id: str
    reviewed_pocs: list[POCDraftItem] = Field(default_factory=list)