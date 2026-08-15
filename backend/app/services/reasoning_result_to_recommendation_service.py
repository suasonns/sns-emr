# app/services/reasoning_result_to_recommendation_service.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.services.icd10_resolver_service import (
    ICD10ResolutionError,
    resolve_icd10_diagnosis_for_use,
)


@dataclass(frozen=True)
class ReasoningResultRecommendationCandidate:
    tenant_id: UUID
    patient_id: UUID
    representative_reasoning_result_id: UUID
    reasoning_result_ids: list[UUID]

    recommendation_source: str
    diagnosis_type: str
    recommended_status: str
    recommendation_status: str

    diagnosis_keyword: str | None
    confidence: str
    priority_score: int

    is_terminal_candidate: bool
    is_related_to_terminal_candidate: bool

    supporting_evidence_summary: str
    clinical_rationale: str
    audit_rationale: str

    source_document_id: UUID | None
    source_document_name: str | None

    requires_rn_review: bool
    requires_md_review: bool
    requires_idg_review: bool

    reasoning_version: str | None
    recommendation_group_key: str


class ReasoningResultToRecommendationService:
    """
    Converts clinical_reasoning_results into diagnosis_recommendations.

    This service does NOT:
    - accept recommendations
    - reject recommendations
    - promote recommendations
    - write patient_diagnoses
    - replace MD review
    """

    DEFAULT_REASONING_VERSION = "icd-reasoning-result-to-recommendation-v1"

    def generate_for_patient(
        self,
        db: Session,
        *,
        tenant_id: UUID,
        patient_id: UUID,
        commit: bool = False,
    ) -> dict[str, Any]:
        results = self._load_candidate_reasoning_results(
            db=db,
            tenant_id=tenant_id,
            patient_id=patient_id,
        )

        grouped = self._group_results_by_icd10(results)

        created_recommendation_ids: list[str] = []
        skipped_groups: list[dict[str, Any]] = []

        for group_key, group_results in grouped.items():
            if not group_results:
                continue

            representative = group_results[0]

            if self._recommendation_exists(
                db=db,
                patient_id=patient_id,
                group_key=group_key,
            ):
                skipped_groups.append(
                    {
                        "reason": "RECOMMENDATION_ALREADY_EXISTS",
                        "recommendation_group_key": group_key,
                    }
                )
                continue

            try:
                resolved = resolve_icd10_diagnosis_for_use(
                    db,
                    diagnosis_input=representative["recommended_icd10"],
                    diagnosis_role="PRIMARY",
                    workflow_context="RN_ICA",
                )
            except ICD10ResolutionError as exc:
                skipped_groups.append(
                    {
                        "reason": "ICD10_RESOLUTION_FAILED",
                        "recommendation_group_key": group_key,
                        "detail": str(exc),
                    }
                )
                continue

            candidate = self._build_candidate(
                tenant_id=tenant_id,
                patient_id=patient_id,
                group_key=group_key,
                group_results=group_results,
                resolved_display_name=resolved.display_name,
                resolved_requires_md_review=bool(
                    getattr(resolved, "requires_md_review", False)
                ),
                resolved_requires_idg_review=bool(
                    getattr(resolved, "requires_idg_review", False)
                ),
                resolved_default_terminal_related=bool(
                    getattr(resolved, "default_terminal_related", False)
                ),
            )

            recommendation_id = self._insert_recommendation(
                db=db,
                candidate=candidate,
            )

            self._insert_reasoning_links_if_supported(
                db=db,
                recommendation_id=recommendation_id,
                reasoning_result_ids=candidate.reasoning_result_ids,
            )

            created_recommendation_ids.append(str(recommendation_id))

        if commit:
            db.commit()

        return {
            "patient_id": str(patient_id),
            "reasoning_results_considered": len(results),
            "recommendations_created": len(created_recommendation_ids),
            "created_recommendation_ids": created_recommendation_ids,
            "skipped_groups": skipped_groups,
        }

    def generate_for_reasoning_result(
        self,
        db: Session,
        *,
        reasoning_result_id: UUID,
        commit: bool = False,
    ) -> dict[str, Any]:
        row = db.execute(
            text(
                """
                SELECT
                    id,
                    tenant_id,
                    patient_id
                FROM clinical_reasoning_results
                WHERE id = :reasoning_result_id
                """
            ),
            {
                "reasoning_result_id": reasoning_result_id,
            },
        ).mappings().first()

        if not row:
            return {
                "reasoning_result_id": str(reasoning_result_id),
                "recommendations_created": 0,
                "reason": "REASONING_RESULT_NOT_FOUND",
            }

        return self.generate_for_patient(
            db=db,
            tenant_id=row["tenant_id"],
            patient_id=row["patient_id"],
            commit=commit,
        )

    def _load_candidate_reasoning_results(
        self,
        db: Session,
        *,
        tenant_id: UUID,
        patient_id: UUID,
    ) -> list[dict[str, Any]]:
        rows = db.execute(
            text(
                """
                SELECT
                    id,
                    tenant_id,
                    patient_id,
                    source_document_id,
                    source_document_name,
                    profile_key,
                    interpretation_key,
                    reasoning_category,
                    severity_level,
                    confidence,
                    matched_evidence,
                    missing_evidence,
                    evidence_count,
                    rationale,
                    clinical_summary,
                    recommended_diagnosis,
                    recommended_icd10,
                    requires_rn_review,
                    requires_md_review,
                    requires_idg_review,
                    reasoning_version,
                    created_at
                FROM clinical_reasoning_results
                WHERE tenant_id = :tenant_id
                  AND patient_id = :patient_id
                  AND recommended_icd10 IS NOT NULL
                  AND trim(recommended_icd10) <> ''
                ORDER BY
                    recommended_icd10 ASC,
                    created_at ASC
                """
            ),
            {
                "tenant_id": tenant_id,
                "patient_id": patient_id,
            },
        ).mappings().all()

        return [dict(row) for row in rows]

    def _group_results_by_icd10(
        self,
        rows: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}

        for row in rows:
            icd10 = str(row.get("recommended_icd10") or "").strip().upper()
            diagnosis = str(row.get("recommended_diagnosis") or "").strip()

            if not icd10:
                continue

            group_key = f"{row['patient_id']}:{icd10}:{diagnosis}".lower()
            grouped.setdefault(group_key, []).append(row)

        return grouped

    def _recommendation_exists(
        self,
        db: Session,
        *,
        patient_id: UUID,
        group_key: str,
    ) -> bool:
        existing = db.execute(
            text(
                """
                SELECT id
                FROM diagnosis_recommendations
                WHERE patient_id = :patient_id
                  AND recommendation_group_key = :recommendation_group_key
                LIMIT 1
                """
            ),
            {
                "patient_id": patient_id,
                "recommendation_group_key": group_key,
            },
        ).scalar_one_or_none()

        return existing is not None

    def _build_candidate(
        self,
        *,
        tenant_id: UUID,
        patient_id: UUID,
        group_key: str,
        group_results: list[dict[str, Any]],
        resolved_display_name: str,
        resolved_requires_md_review: bool,
        resolved_requires_idg_review: bool,
        resolved_default_terminal_related: bool,
    ) -> ReasoningResultRecommendationCandidate:
        representative = group_results[0]

        reasoning_categories = [
            str(row.get("reasoning_category") or "").strip()
            for row in group_results
            if str(row.get("reasoning_category") or "").strip()
        ]

        rationales = [
            str(row.get("rationale") or "").strip()
            for row in group_results
            if str(row.get("rationale") or "").strip()
        ]

        summaries = [
            str(row.get("clinical_summary") or "").strip()
            for row in group_results
            if str(row.get("clinical_summary") or "").strip()
        ]

        evidence_count = sum(
            int(row.get("evidence_count") or 0)
            for row in group_results
        )

        confidence = self._combine_confidence(
            [
                str(row.get("confidence") or "").strip().lower()
                for row in group_results
            ]
        )

        source_document_id = representative.get("source_document_id")
        source_document_name = representative.get("source_document_name")

        requires_rn_review = any(
            bool(row.get("requires_rn_review"))
            for row in group_results
        )

        requires_md_review = (
            resolved_requires_md_review
            or any(bool(row.get("requires_md_review")) for row in group_results)
            or True
        )

        requires_idg_review = (
            resolved_requires_idg_review
            or any(bool(row.get("requires_idg_review")) for row in group_results)
        )

        supporting_evidence_summary = self._build_evidence_summary(
            diagnosis=resolved_display_name,
            reasoning_categories=reasoning_categories,
            evidence_count=evidence_count,
            summaries=summaries,
        )

        clinical_rationale = self._build_clinical_rationale(
            diagnosis=resolved_display_name,
            rationales=rationales,
            summaries=summaries,
        )

        audit_rationale = self._build_audit_rationale(
            reasoning_result_ids=[row["id"] for row in group_results],
            reasoning_categories=reasoning_categories,
            evidence_count=evidence_count,
        )

        return ReasoningResultRecommendationCandidate(
            tenant_id=tenant_id,
            patient_id=patient_id,
            representative_reasoning_result_id=representative["id"],
            reasoning_result_ids=[row["id"] for row in group_results],
            recommendation_source="CLINICAL_REASONING_RESULT",
            diagnosis_type="PRIMARY",
            recommended_status="PROPOSED",
            recommendation_status="PENDING_REVIEW",
            diagnosis_keyword=resolved_display_name,
            confidence=confidence,
            priority_score=self._priority_score(
                evidence_count=evidence_count,
                confidence=confidence,
                requires_md_review=requires_md_review,
                requires_idg_review=requires_idg_review,
            ),
            is_terminal_candidate=True,
            is_related_to_terminal_candidate=bool(
                resolved_default_terminal_related
            ),
            supporting_evidence_summary=supporting_evidence_summary,
            clinical_rationale=clinical_rationale,
            audit_rationale=audit_rationale,
            source_document_id=source_document_id,
            source_document_name=source_document_name,
            requires_rn_review=requires_rn_review,
            requires_md_review=requires_md_review,
            requires_idg_review=requires_idg_review,
            reasoning_version=(
                representative.get("reasoning_version")
                or self.DEFAULT_REASONING_VERSION
            ),
            recommendation_group_key=group_key,
        )

    def _insert_recommendation(
        self,
        db: Session,
        candidate: ReasoningResultRecommendationCandidate,
    ) -> UUID:
        row = db.execute(
            text(
                """
                INSERT INTO diagnosis_recommendations (
                    id,
                    tenant_id,
                    patient_id,
                    reasoning_result_id,
                    recommendation_source,
                    diagnosis_type,
                    recommended_status,
                    recommendation_status,
                    diagnosis_keyword,
                    confidence,
                    priority_score,
                    is_terminal_candidate,
                    is_related_to_terminal_candidate,
                    supporting_evidence_summary,
                    clinical_rationale,
                    audit_rationale,
                    source_document_id,
                    source_document_name,
                    requires_rn_review,
                    requires_md_review,
                    requires_idg_review,
                    reviewed_by,
                    reviewed_at,
                    accepted_by,
                    accepted_at,
                    rejected_by,
                    rejected_at,
                    rejection_reason,
                    promoted_patient_diagnosis_id,
                    reasoning_version,
                    created_at,
                    updated_at,
                    recommendation_group_key
                )
                VALUES (
                    gen_random_uuid(),
                    :tenant_id,
                    :patient_id,
                    :reasoning_result_id,
                    :recommendation_source,
                    :diagnosis_type,
                    :recommended_status,
                    :recommendation_status,
                    :diagnosis_keyword,
                    :confidence,
                    :priority_score,
                    :is_terminal_candidate,
                    :is_related_to_terminal_candidate,
                    :supporting_evidence_summary,
                    :clinical_rationale,
                    :audit_rationale,
                    :source_document_id,
                    :source_document_name,
                    :requires_rn_review,
                    :requires_md_review,
                    :requires_idg_review,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    :reasoning_version,
                    :now,
                    :now,
                    :recommendation_group_key
                )
                RETURNING id
                """
            ),
            {
                "tenant_id": candidate.tenant_id,
                "patient_id": candidate.patient_id,
                "reasoning_result_id": candidate.representative_reasoning_result_id,
                "recommendation_source": candidate.recommendation_source,
                "diagnosis_type": candidate.diagnosis_type,
                "recommended_status": candidate.recommended_status,
                "recommendation_status": candidate.recommendation_status,
                "diagnosis_keyword": candidate.diagnosis_keyword,
                "confidence": candidate.confidence,
                "priority_score": candidate.priority_score,
                "is_terminal_candidate": candidate.is_terminal_candidate,
                "is_related_to_terminal_candidate": (
                    candidate.is_related_to_terminal_candidate
                ),
                "supporting_evidence_summary": (
                    candidate.supporting_evidence_summary
                ),
                "clinical_rationale": candidate.clinical_rationale,
                "audit_rationale": candidate.audit_rationale,
                "source_document_id": candidate.source_document_id,
                "source_document_name": candidate.source_document_name,
                "requires_rn_review": candidate.requires_rn_review,
                "requires_md_review": candidate.requires_md_review,
                "requires_idg_review": candidate.requires_idg_review,
                "reasoning_version": candidate.reasoning_version,
                "recommendation_group_key": candidate.recommendation_group_key,
                "now": datetime.now(timezone.utc),
            },
        ).scalar_one()

        return row

    def _insert_reasoning_links_if_supported(
        self,
        db: Session,
        *,
        recommendation_id: UUID,
        reasoning_result_ids: list[UUID],
    ) -> None:
        inspector = inspect(db.get_bind())

        if not inspector.has_table("diagnosis_recommendation_reasoning_links"):
            return

        columns = {
            column["name"]
            for column in inspector.get_columns(
                "diagnosis_recommendation_reasoning_links"
            )
        }

        recommendation_column = self._resolve_existing_column(
            columns,
            [
                "diagnosis_recommendation_id",
                "recommendation_id",
            ],
        )

        reasoning_result_column = self._resolve_existing_column(
            columns,
            [
                "reasoning_result_id",
                "clinical_reasoning_result_id",
            ],
        )

        if not recommendation_column or not reasoning_result_column:
            return

        id_column = "id" if "id" in columns else None
        created_at_column = "created_at" if "created_at" in columns else None

        for reasoning_result_id in reasoning_result_ids:
            existing = db.execute(
                text(
                    f"""
                    SELECT 1
                    FROM diagnosis_recommendation_reasoning_links
                    WHERE {recommendation_column} = :recommendation_id
                      AND {reasoning_result_column} = :reasoning_result_id
                    LIMIT 1
                    """
                ),
                {
                    "recommendation_id": recommendation_id,
                    "reasoning_result_id": reasoning_result_id,
                },
            ).scalar_one_or_none()

            if existing:
                continue

            insert_columns = [
                recommendation_column,
                reasoning_result_column,
            ]

            insert_values = [
                ":recommendation_id",
                ":reasoning_result_id",
            ]

            params = {
                "recommendation_id": recommendation_id,
                "reasoning_result_id": reasoning_result_id,
            }

            if id_column:
                insert_columns.insert(0, id_column)
                insert_values.insert(0, "gen_random_uuid()")

            if created_at_column:
                insert_columns.append(created_at_column)
                insert_values.append(":created_at")
                params["created_at"] = datetime.now(timezone.utc)

            db.execute(
                text(
                    f"""
                    INSERT INTO diagnosis_recommendation_reasoning_links (
                        {", ".join(insert_columns)}
                    )
                    VALUES (
                        {", ".join(insert_values)}
                    )
                    """
                ),
                params,
            )

    def _resolve_existing_column(
        self,
        columns: set[str],
        candidates: list[str],
    ) -> str | None:
        for candidate in candidates:
            if candidate in columns:
                return candidate
        return None

    def _combine_confidence(
        self,
        confidence_values: list[str],
    ) -> str:
        values = {value for value in confidence_values if value}

        if "high" in values:
            return "high"
        if "medium" in values:
            return "medium"
        if "low" in values:
            return "low"

        return "unknown"

    def _priority_score(
        self,
        *,
        evidence_count: int,
        confidence: str,
        requires_md_review: bool,
        requires_idg_review: bool,
    ) -> int:
        score = 0

        score += min(evidence_count, 10)

        if confidence == "high":
            score += 5
        elif confidence == "medium":
            score += 3
        elif confidence == "low":
            score += 1

        if requires_md_review:
            score += 3

        if requires_idg_review:
            score += 2

        return score

    def _build_evidence_summary(
        self,
        *,
        diagnosis: str,
        reasoning_categories: list[str],
        evidence_count: int,
        summaries: list[str],
    ) -> str:
        category_text = ", ".join(sorted(set(reasoning_categories))) or "unspecified"

        summary_parts = [
            f"Recommended diagnosis: {diagnosis}.",
            f"Reasoning categories: {category_text}.",
            f"Evidence count: {evidence_count}.",
        ]

        if summaries:
            summary_parts.append(
                "Clinical summaries: " + " | ".join(summaries[:5])
            )

        return " ".join(summary_parts)

    def _build_clinical_rationale(
        self,
        *,
        diagnosis: str,
        rationales: list[str],
        summaries: list[str],
    ) -> str:
        parts = [
            f"Clinical reasoning supports consideration of {diagnosis}."
        ]

        if rationales:
            parts.append("Rationale: " + " | ".join(rationales[:5]))
        elif summaries:
            parts.append("Summary: " + " | ".join(summaries[:5]))

        return " ".join(parts)

    def _build_audit_rationale(
        self,
        *,
        reasoning_result_ids: list[UUID],
        reasoning_categories: list[str],
        evidence_count: int,
    ) -> str:
        return (
            "Generated from clinical_reasoning_results. "
            f"Reasoning result ids: {[str(x) for x in reasoning_result_ids]}. "
            f"Reasoning categories: {sorted(set(reasoning_categories))}. "
            f"Evidence count: {evidence_count}. "
            "Recommendation requires clinical review before promotion."
        )