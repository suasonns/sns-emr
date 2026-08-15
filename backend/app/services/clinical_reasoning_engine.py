# services/clinical_reasoning_engine.py

from __future__ import annotations

import json
import logging

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.clinical_reasoning_result import (
    ClinicalReasoningResult,
)

from app.services.clinical_reasoning_to_idg_service import (
    create_or_update_from_reasoning_result,
)


logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class FindingCandidate:
    category: str
    finding_type: str
    value_text: Optional[str] = None
    value_numeric: Optional[Decimal] = None
    previous_value_text: Optional[str] = None
    previous_value_numeric: Optional[Decimal] = None
    trend: Optional[str] = None
    severity: Optional[str] = None
    source: str = "RN"
    observed_at: Optional[datetime] = None
    is_significant_change: bool = False


class ClinicalReasoningEngine:
    """
    Sprint 1 engine.

    Responsibilities:
    - Extract findings from assessment data.
    - Save findings.
    - Create significant-change events.
    - Generate interpretations from configured database rules.
    - Link interpretations to source findings.
    """

    GENERATED_BY = "engine"
    DEFAULT_CONFIDENCE = "high"

    def process_assessment(
        self,
        db: Session,
        reasoning_record_id: UUID,
        assessment_data: Dict[str, Any],
        *,
        reset_existing: bool = False,
        commit: bool = False,
    ) -> Dict[str, Any]:
        if reset_existing:
            self.delete_generated_outputs(
                db,
                reasoning_record_id,
                reset_review_flags=True,
            )

        findings = self.extract_findings(assessment_data)
        inserted_findings = self.save_findings(db, reasoning_record_id, findings)
        significant_changes = self.create_significant_change_events(
            db, reasoning_record_id, inserted_findings
        )
        interpretations = self.generate_interpretations(db, reasoning_record_id)
        
        reasoning_results = self.generate_reasoning_results(
            db,
            reasoning_record_id,
        )
        
        if commit:
            db.commit()

        return {
            "reasoning_record_id": str(reasoning_record_id),
            "findings_created": len(inserted_findings),
            "significant_changes_created": len(significant_changes),
            "interpretations_created": len(interpretations),
            "reasoning_results_created": len(reasoning_results),
            "findings": inserted_findings,
            "significant_changes": significant_changes,
            "interpretations": interpretations,
            "reasoning_results": reasoning_results,
        }

    def extract_findings(self, assessment_data: Dict[str, Any]) -> List[FindingCandidate]:
        source = (
            assessment_data.get("source")
            or assessment_data.get("discipline")
            or "UNKNOWN"
        )
        observed_at = self._observed_at(assessment_data.get("observed_at"))

        findings: List[FindingCandidate] = []
        findings.extend(self._extract_weight_findings(assessment_data, source, observed_at))
        findings.extend(self._extract_mac_findings(assessment_data, source, observed_at))
        findings.extend(self._extract_appetite_findings(assessment_data, source, observed_at))
        findings.extend(self._extract_pain_findings(assessment_data, source, observed_at))
        findings.extend(self._extract_functional_findings(assessment_data, source, observed_at))
        findings.extend(self._extract_safety_findings(assessment_data, source, observed_at))
        findings.extend(self._extract_caregiver_findings(assessment_data, source, observed_at))
        findings.extend(self._extract_respiratory_findings(assessment_data, source, observed_at))
        findings.extend(self._extract_cardiac_findings(assessment_data, source, observed_at))
        findings.extend(self._extract_cognitive_behavior_findings(assessment_data, source, observed_at))
        findings.extend(self._extract_spiritual_findings(assessment_data, source, observed_at))

        return self._dedupe_findings(findings)

    def save_findings(
        self,
        db: Session,
        reasoning_record_id: UUID,
        findings: Iterable[FindingCandidate],
    ) -> List[Dict[str, Any]]:
        inserted: List[Dict[str, Any]] = []

        for finding in findings:
            row = db.execute(
                text(
                    """
                    INSERT INTO findings (
                        reasoning_record_id,
                        category,
                        finding_type,
                        value_text,
                        value_numeric,
                        previous_value_text,
                        previous_value_numeric,
                        trend,
                        severity,
                        source,
                        observed_at,
                        is_significant_change
                    )
                    VALUES (
                        :reasoning_record_id,
                        :category,
                        :finding_type,
                        :value_text,
                        :value_numeric,
                        :previous_value_text,
                        :previous_value_numeric,
                        :trend,
                        :severity,
                        :source,
                        :observed_at,
                        :is_significant_change
                    )
                    RETURNING
                        id,
                        category,
                        finding_type,
                        trend,
                        severity,
                        is_significant_change
                    """
                ),
                {
                    "reasoning_record_id": reasoning_record_id,
                    "category": finding.category,
                    "finding_type": finding.finding_type,
                    "value_text": finding.value_text,
                    "value_numeric": finding.value_numeric,
                    "previous_value_text": finding.previous_value_text,
                    "previous_value_numeric": finding.previous_value_numeric,
                    "trend": finding.trend,
                    "severity": finding.severity,
                    "source": finding.source,
                    "observed_at": finding.observed_at or datetime.now(timezone.utc),
                    "is_significant_change": finding.is_significant_change,
                },
            ).mappings().one()

            inserted.append(self._clean_row(dict(row)))

        return inserted

    def create_significant_change_events(
        self,
        db: Session,
        reasoning_record_id: UUID,
        inserted_findings: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        created: List[Dict[str, Any]] = []

        for finding in inserted_findings:
            if not finding.get("is_significant_change"):
                continue

            row = db.execute(
                text(
                    """
                    INSERT INTO significant_change_events (
                        reasoning_record_id,
                        finding_id,
                        trigger_type,
                        description,
                        requires_notification,
                        physician_notified,
                        representative_notified
                    )
                    VALUES (
                        :reasoning_record_id,
                        :finding_id,
                        :trigger_type,
                        :description,
                        TRUE,
                        FALSE,
                        FALSE
                    )
                    RETURNING
                        id,
                        trigger_type,
                        requires_notification
                    """
                ),
                {
                    "reasoning_record_id": reasoning_record_id,
                    "finding_id": finding["id"],
                    "trigger_type": finding["finding_type"],
                    "description": f"Significant change detected from finding: {finding['finding_type']}",
                },
            ).mappings().one()

            created.append(self._clean_row(dict(row)))

        if created:
            db.execute(
                text(
                    """
                    UPDATE clinical_reasoning_records
                    SET
                        requires_poc_update = TRUE,
                        requires_physician_review = TRUE,
                        updated_at = NOW()
                    WHERE id = :reasoning_record_id
                    """
                ),
                {"reasoning_record_id": reasoning_record_id},
            )

        return created

    def generate_interpretations(
        self,
        db: Session,
        reasoning_record_id: UUID,
    ) -> List[Dict[str, Any]]:
        findings = self._load_findings(db, reasoning_record_id)
        finding_types = {finding["finding_type"] for finding in findings}
        rules = self._load_active_interpretation_rules(db)
        created: List[Dict[str, Any]] = []

        for rule in rules:
            required_types = set(rule["required_finding_types"])

            if not required_types:
                continue

            if not required_types.issubset(finding_types):
                continue

            if self._interpretation_exists(
                db=db,
                reasoning_record_id=reasoning_record_id,
                interpretation_code=rule["interpretation_code"],
            ):
                continue

            interpretation = self._insert_interpretation(
                db=db,
                reasoning_record_id=reasoning_record_id,
                rule=rule,
            )

            matched_finding_ids = [
                finding["id"]
                for finding in findings
                if finding["finding_type"] in required_types
            ]

            self._link_interpretation_findings(
                db=db,
                interpretation_id=interpretation["id"],
                finding_ids=matched_finding_ids,
            )

            created.append(interpretation)

        return created
    
    def _resolve_pain_diagnosis_from_evidence(
        self,
        interpretation_code: str,
        evidence_rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if str(interpretation_code or "").upper() != "PAIN_ESCALATION":
            return {
                "recommended_diagnosis": None,
                "recommended_icd10": None,
                "requires_rn_review": False,
            }

        evidence_text_parts: list[str] = []

        for row in evidence_rows:
            finding_type = str(row.get("finding_type") or "").lower()
            value_text = str(row.get("value_text") or "").strip()

            if finding_type in {
                "pain_cause_category",
                "pain_cause_text",
                "assessment_summary",
                "nursing_summary",
                "pain_location",
                "pain_quality",
            } and value_text:
                evidence_text_parts.append(value_text)

        combined = " ".join(evidence_text_parts).lower()

        cancer_related_terms = [
            "cancer-related pain",
            "cancer related pain",
            "neoplasm-related pain",
            "neoplasm related pain",
            "malignancy-related pain",
            "malignancy related pain",
            "pain related to cancer",
            "pain associated with cancer",
            "pain from metastatic",
            "metastatic pain",
            "bone metastasis pain",
            "bone mets pain",
            "tumor pain",
            "tumour pain",
        ]

        unable_to_determine_terms = [
            "unable to determine",
            "cause unclear",
            "etiology unclear",
            "unknown cause",
            "undetermined cause",
            "pain unspecified",
        ]

        if any(term in combined for term in cancer_related_terms):
            return {
                "recommended_diagnosis": "Neoplasm-related pain",
                "recommended_icd10": "G89.3",
                "requires_rn_review": True,
            }

        if any(term in combined for term in unable_to_determine_terms):
            return {
                "recommended_diagnosis": "Pain, unspecified",
                "recommended_icd10": "R52",
                "requires_rn_review": True,
            }

        return {
            "recommended_diagnosis": None,
            "recommended_icd10": None,
            "requires_rn_review": True,
        }
    
    def generate_reasoning_results(
        self,
        db: Session,
        reasoning_record_id: UUID,
    ) -> List[Dict[str, Any]]:
        record = db.execute(
            text(
                """
                SELECT
                    crr.id,
                    crr.patient_id,
                    crr.episode_id,
                    crr.requires_poc_update,
                    crr.requires_physician_review,
                    crr.requires_idg_review,
                    COALESCE(v.tenant_id, p.tenant_id) AS tenant_id
                FROM clinical_reasoning_records crr
                LEFT JOIN visits v
                    ON v.id = crr.episode_id
                LEFT JOIN patients p
                    ON p.id = crr.patient_id
                WHERE crr.id = :reasoning_record_id
                """
            ),
            {"reasoning_record_id": reasoning_record_id},
        ).mappings().first()

        if not record:
            return []

        interpretations = db.execute(
            text(
                """
                SELECT
                    id,
                    interpretation_code,
                    statement,
                    severity,
                    confidence,
                    generated_by
                FROM clinical_interpretations
                WHERE reasoning_record_id = :reasoning_record_id
                ORDER BY created_at ASC
                """
            ),
            {"reasoning_record_id": reasoning_record_id},
        ).mappings().all()

        created: List[Dict[str, Any]] = []

        for interpretation in interpretations:
            existing = db.execute(
                text(
                    """
                    SELECT id
                    FROM clinical_reasoning_results
                    WHERE patient_id = :patient_id
                    AND source_document_id = :source_document_id
                    AND interpretation_key = :interpretation_key
                    LIMIT 1
                    """
                ),
                {
                    "patient_id": record["patient_id"],
                    "source_document_id": record["episode_id"],
                    "interpretation_key": interpretation["interpretation_code"],
                },
            ).scalar_one_or_none()

            if existing:
                reasoning_result = (
                    db.query(ClinicalReasoningResult)
                    .filter(
                        ClinicalReasoningResult.id == existing
                    )
                    .first()
                )

                if reasoning_result:
                    create_or_update_from_reasoning_result(
                        db=db,
                        reasoning=reasoning_result,
                    )

                continue

            evidence_rows = db.execute(
                text(
                    """
                    SELECT
                        f.id,
                        f.category,
                        f.finding_type,
                        f.value_text,
                        f.value_numeric,
                        f.previous_value_text,
                        f.previous_value_numeric,
                        f.trend,
                        f.severity,
                        f.source,
                        f.observed_at,
                        f.is_significant_change
                    FROM interpretation_findings inf
                    JOIN findings f
                        ON f.id = inf.finding_id
                    WHERE inf.interpretation_id = :interpretation_id
                    ORDER BY f.observed_at ASC
                    """
                ),
                {"interpretation_id": interpretation["id"]},
            ).mappings().all()

            matched_evidence = [dict(row) for row in evidence_rows]
            
            if str(interpretation["interpretation_code"] or "").upper() == "PAIN_ESCALATION":
                extra_pain_evidence_rows = db.execute(
                    text(
                        """
                        SELECT
                            f.id,
                            f.category,
                            f.finding_type,
                            f.value_text,
                            f.value_numeric,
                            f.previous_value_text,
                            f.previous_value_numeric,
                            f.trend,
                            f.severity,
                            f.source,
                            f.observed_at,
                            f.is_significant_change
                        FROM findings f
                        WHERE f.reasoning_record_id = :reasoning_record_id
                          AND f.finding_type IN (
                              'pain_cause_category',
                              'pain_cause_text',
                              'assessment_summary',
                              'nursing_summary',
                              'pain_location',
                              'pain_quality'
                          )
                        ORDER BY f.observed_at ASC
                        """
                    ),
                    {
                        "reasoning_record_id": reasoning_record_id,
                    },
                ).mappings().all()

                existing_evidence_ids = {
                    str(row.get("id"))
                    for row in matched_evidence
                }

                for extra_row in extra_pain_evidence_rows:
                    extra_dict = dict(extra_row)
                    if str(extra_dict.get("id")) not in existing_evidence_ids:
                        matched_evidence.append(extra_dict)

            pain_diagnosis = self._resolve_pain_diagnosis_from_evidence(
                interpretation_code=interpretation["interpretation_code"],
                evidence_rows=matched_evidence,
            )

            recommended_diagnosis = pain_diagnosis["recommended_diagnosis"]
            recommended_icd10 = pain_diagnosis["recommended_icd10"]
            requires_rn_review = bool(pain_diagnosis["requires_rn_review"])
            
            try:
                row = db.execute(
                    text(
                        """
                        INSERT INTO clinical_reasoning_results (
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
                        accepted_by,
                        accepted_at,
                        rejected_by,
                        rejected_at,
                        rejection_reason,
                        reasoning_version,
                        created_at
                    )
                    VALUES (
                        gen_random_uuid(),
                        :tenant_id,
                        :patient_id,
                        :source_document_id,
                        :source_document_name,
                        :profile_key,
                        :interpretation_key,
                        :reasoning_category,
                        :severity_level,
                        :confidence,
                        CAST(:matched_evidence AS jsonb),
                        CAST(:missing_evidence AS jsonb),
                        :evidence_count,
                        :rationale,
                        :clinical_summary,
                        :recommended_diagnosis,
                        :recommended_icd10,
                        :requires_rn_review,
                        :requires_md_review,
                        :requires_idg_review,
                        NULL,
                        NULL,
                        NULL,
                        NULL,
                        NULL,
                        :reasoning_version,
                        NOW()
                    )
                    RETURNING
                        id,
                        interpretation_key,
                        reasoning_category,
                        evidence_count
                    """
                    ),
                    {
                        "tenant_id": record["tenant_id"],
                        "patient_id": record["patient_id"],
                        "source_document_id": record["episode_id"],
                        "source_document_name": "Clinical Reasoning Source",
                        "profile_key": "CLINICAL_REASONING",
                        "interpretation_key": interpretation["interpretation_code"],
                        "reasoning_category": str(
                            interpretation["interpretation_code"] or ""
                        ).lower(),
                        "severity_level": interpretation["severity"],
                        "confidence": interpretation["confidence"],
                        "matched_evidence": json.dumps(matched_evidence, default=str),
                        "missing_evidence": json.dumps([]),
                        "evidence_count": len(matched_evidence),
                        "rationale": interpretation["statement"],
                        "clinical_summary": interpretation["statement"],
                        "recommended_diagnosis": recommended_diagnosis,
                        "recommended_icd10": recommended_icd10,
                        "requires_rn_review": requires_rn_review,
                        "requires_md_review": bool(record["requires_physician_review"]),
                        "requires_idg_review": bool(record["requires_idg_review"]),
                        "reasoning_version": "clinical-reasoning-result-v1",
                    },
                ).mappings().one()

                created.append(dict(row))

                reasoning_result = (
                    db.query(ClinicalReasoningResult)
                    .filter(
                        ClinicalReasoningResult.id == row["id"]
                    )
                    .first()
                )

                if reasoning_result:
                    create_or_update_from_reasoning_result(
                        db=db,
                        reasoning=reasoning_result,
                    )
            except Exception:
                logger.exception(
                    "Clinical reasoning result insert failed",
                )
                raise
        return created
    
    def delete_generated_outputs(
        self,
        db: Session,
        reasoning_record_id: UUID,
        *,
        reset_review_flags: bool = False,
    ) -> None:
        db.execute(
            text(
                """
                DELETE FROM interpretation_findings
                WHERE interpretation_id IN (
                    SELECT id
                    FROM clinical_interpretations
                    WHERE reasoning_record_id = :reasoning_record_id
                )
                """
            ),
            {"reasoning_record_id": reasoning_record_id},
        )

        db.execute(
            text(
                """
                DELETE FROM significant_change_events
                WHERE reasoning_record_id = :reasoning_record_id
                """
            ),
            {"reasoning_record_id": reasoning_record_id},
        )

        db.execute(
            text(
                """
                DELETE FROM clinical_interpretations
                WHERE reasoning_record_id = :reasoning_record_id
                """
            ),
            {"reasoning_record_id": reasoning_record_id},
        )

        db.execute(
            text(
                """
                DELETE FROM findings
                WHERE reasoning_record_id = :reasoning_record_id
                """
            ),
            {"reasoning_record_id": reasoning_record_id},
        )

        if reset_review_flags:
            db.execute(
                text(
                    """
                    UPDATE clinical_reasoning_records
                    SET
                        requires_poc_update = FALSE,
                        requires_physician_review = FALSE,
                        requires_idg_review = FALSE,
                        updated_at = NOW()
                    WHERE id = :reasoning_record_id
                    """
                ),
                {"reasoning_record_id": reasoning_record_id},
            )

    def _extract_weight_findings(
        self,
        assessment_data: Dict[str, Any],
        source: str,
        observed_at: datetime,
    ) -> List[FindingCandidate]:
        weight = self._to_decimal(assessment_data.get("weight"))
        previous_weight = self._to_decimal(assessment_data.get("previous_weight"))

        if weight is None or previous_weight is None:
            return []

        if weight < previous_weight:
            return [
                FindingCandidate(
                    category="nutrition",
                    finding_type="weight_loss",
                    value_numeric=weight,
                    previous_value_numeric=previous_weight,
                    trend="declining",
                    source=source,
                    observed_at=observed_at,
                    is_significant_change=True,
                )
            ]

        if weight > previous_weight:
            return [
                FindingCandidate(
                    category="cardiac",
                    finding_type="weight_gain",
                    value_numeric=weight,
                    previous_value_numeric=previous_weight,
                    trend="worsening",
                    source=source,
                    observed_at=observed_at,
                )
            ]

        return []

    def _extract_mac_findings(
        self,
        assessment_data: Dict[str, Any],
        source: str,
        observed_at: datetime,
    ) -> List[FindingCandidate]:
        mac = self._to_decimal(assessment_data.get("mac"))
        previous_mac = self._to_decimal(assessment_data.get("previous_mac"))

        if mac is None or previous_mac is None:
            return []

        if mac < previous_mac:
            return [
                FindingCandidate(
                    category="nutrition",
                    finding_type="mac_decline",
                    value_numeric=mac,
                    previous_value_numeric=previous_mac,
                    trend="declining",
                    source=source,
                    observed_at=observed_at,
                )
            ]

        return []

    def _extract_appetite_findings(
        self,
        assessment_data: Dict[str, Any],
        source: str,
        observed_at: datetime,
    ) -> List[FindingCandidate]:
        appetite = assessment_data.get("appetite")
        previous_appetite = assessment_data.get("previous_appetite")
        appetite_decline = bool(assessment_data.get("appetite_decline"))
        findings: List[FindingCandidate] = []

        if appetite in {"poor", "none"}:
            findings.append(
                FindingCandidate(
                    category="nutrition",
                    finding_type="poor_appetite",
                    value_text=appetite,
                    previous_value_text=previous_appetite,
                    trend="declining",
                    source=source,
                    observed_at=observed_at,
                    is_significant_change=appetite_decline,
                )
            )

        if appetite_decline:
            findings.append(
                FindingCandidate(
                    category="nutrition",
                    finding_type="significant_change_appetite",
                    trend="declining",
                    source=source,
                    observed_at=observed_at,
                    is_significant_change=True,
                )
            )

        return findings

    def _extract_pain_findings(
        self,
        assessment_data: Dict[str, Any],
        source: str,
        observed_at: datetime,
    ) -> List[FindingCandidate]:
        pain_score = self._to_decimal(assessment_data.get("pain_score"))
        previous_pain_score = self._to_decimal(assessment_data.get("previous_pain_score"))
        pain_increase = bool(assessment_data.get("pain_increase"))
        findings: List[FindingCandidate] = []

        if pain_score is not None:
            trend = None
            if previous_pain_score is not None and pain_score > previous_pain_score:
                trend = "worsening"
                pain_increase = True

            findings.append(
                FindingCandidate(
                    category="symptom",
                    finding_type="pain",
                    value_numeric=pain_score,
                    previous_value_numeric=previous_pain_score,
                    trend=trend,
                    severity=self._pain_severity(pain_score),
                    source=source,
                    observed_at=observed_at,
                    is_significant_change=pain_increase,
                )
            )

        if pain_increase:
            findings.append(
                FindingCandidate(
                    category="symptom",
                    finding_type="significant_change_pain",
                    trend="worsening",
                    source=source,
                    observed_at=observed_at,
                    is_significant_change=True,
                )
            )

        # -------------------------------------------------
        # Pain attribution / transcript-derived evidence
        # -------------------------------------------------
        pain_location = assessment_data.get("pain_location")
        if pain_location:
            findings.append(
                FindingCandidate(
                    category="symptom",
                    finding_type="pain_location",
                    value_text=str(pain_location),
                    source=source,
                    observed_at=observed_at,
                )
            )

        pain_quality = assessment_data.get("pain_quality")
        if pain_quality:
            findings.append(
                FindingCandidate(
                    category="symptom",
                    finding_type="pain_quality",
                    value_text=str(pain_quality),
                    source=source,
                    observed_at=observed_at,
                )
            )

        pain_cause_category = (
            assessment_data.get("pain_cause_category")
            or assessment_data.get("cause_determination")
        )

        if pain_cause_category:
            findings.append(
                FindingCandidate(
                    category="symptom",
                    finding_type="pain_cause_category",
                    value_text=str(pain_cause_category),
                    source=source,
                    observed_at=observed_at,
                )
            )

        pain_cause_text = (
            assessment_data.get("pain_cause_text")
            or assessment_data.get("associated_diagnosis_text")
        )

        if pain_cause_text:
            findings.append(
                FindingCandidate(
                    category="symptom",
                    finding_type="pain_cause_text",
                    value_text=str(pain_cause_text),
                    source=source,
                    observed_at=observed_at,
                )
            )

        assessment_summary = assessment_data.get("assessment_summary")
        if assessment_summary:
            findings.append(
                FindingCandidate(
                    category="symptom",
                    finding_type="assessment_summary",
                    value_text=str(assessment_summary),
                    source=source,
                    observed_at=observed_at,
                )
            )

        nursing_summary = assessment_data.get("nursing_summary")
        if nursing_summary:
            findings.append(
                FindingCandidate(
                    category="symptom",
                    finding_type="nursing_summary",
                    value_text=str(nursing_summary),
                    source=source,
                    observed_at=observed_at,
                )
            )

        return findings

    def _extract_functional_findings(
        self,
        assessment_data: Dict[str, Any],
        source: str,
        observed_at: datetime,
    ) -> List[FindingCandidate]:
        findings: List[FindingCandidate] = []

        if assessment_data.get("weakness_increased"):
            findings.append(
                FindingCandidate(
                    category="functional",
                    finding_type="weakness",
                    trend="worsening",
                    source=source,
                    observed_at=observed_at,
                )
            )

        if assessment_data.get("mobility_decline"):
            findings.append(
                FindingCandidate(
                    category="functional",
                    finding_type="mobility_decline",
                    trend="declining",
                    source=source,
                    observed_at=observed_at,
                )
            )

        if assessment_data.get("transfer_assistance_increased"):
            findings.append(
                FindingCandidate(
                    category="functional",
                    finding_type="transfer_dependence",
                    trend="worsening",
                    source=source,
                    observed_at=observed_at,
                )
            )

        return findings

    def _extract_safety_findings(
        self,
        assessment_data: Dict[str, Any],
        source: str,
        observed_at: datetime,
    ) -> List[FindingCandidate]:
        fall_count = self._to_decimal(assessment_data.get("fall_count"))

        if fall_count is None or fall_count <= 0:
            return []

        return [
            FindingCandidate(
                category="safety",
                finding_type="fall",
                value_numeric=fall_count,
                trend="new",
                source=source,
                observed_at=observed_at,
                is_significant_change=True,
            )
        ]

    def _extract_caregiver_findings(
        self,
        assessment_data: Dict[str, Any],
        source: str,
        observed_at: datetime,
    ) -> List[FindingCandidate]:
        findings: List[FindingCandidate] = []

        if assessment_data.get("caregiver_tearful"):
            findings.append(
                FindingCandidate(
                    category="caregiver",
                    finding_type="caregiver_distress",
                    trend="new",
                    source=source,
                    observed_at=observed_at,
                )
            )

        if assessment_data.get("caregiver_overwhelmed"):
            findings.append(
                FindingCandidate(
                    category="caregiver",
                    finding_type="caregiver_overwhelmed",
                    trend="new",
                    source=source,
                    observed_at=observed_at,
                )
            )

        return findings

    def _extract_respiratory_findings(
        self,
        assessment_data: Dict[str, Any],
        source: str,
        observed_at: datetime,
    ) -> List[FindingCandidate]:
        findings: List[FindingCandidate] = []
        respiratory_rate = self._to_decimal(assessment_data.get("respiratory_rate"))
        previous_respiratory_rate = self._to_decimal(
            assessment_data.get("previous_respiratory_rate")
        )

        if respiratory_rate is not None and respiratory_rate >= Decimal("24"):
            trend = None
            if previous_respiratory_rate is not None and respiratory_rate > previous_respiratory_rate:
                trend = "worsening"

            findings.append(
                FindingCandidate(
                    category="respiratory",
                    finding_type="tachypnea",
                    value_numeric=respiratory_rate,
                    previous_value_numeric=previous_respiratory_rate,
                    trend=trend,
                    source=source,
                    observed_at=observed_at,
                )
            )

        if assessment_data.get("accessory_muscle_use"):
            findings.append(
                FindingCandidate(
                    category="respiratory",
                    finding_type="accessory_muscle_use",
                    trend="new",
                    source=source,
                    observed_at=observed_at,
                )
            )

        if assessment_data.get("oxygen_increase"):
            findings.append(
                FindingCandidate(
                    category="respiratory",
                    finding_type="oxygen_increase",
                    trend="worsening",
                    source=source,
                    observed_at=observed_at,
                    is_significant_change=True,
                )
            )

        return findings

    def _extract_cardiac_findings(
        self,
        assessment_data: Dict[str, Any],
        source: str,
        observed_at: datetime,
    ) -> List[FindingCandidate]:
        findings: List[FindingCandidate] = []

        if assessment_data.get("edema_present"):
            findings.append(
                FindingCandidate(
                    category="cardiac",
                    finding_type="edema",
                    trend="worsening" if assessment_data.get("edema_worsening") else "new",
                    source=source,
                    observed_at=observed_at,
                )
            )

        if assessment_data.get("orthopnea"):
            findings.append(
                FindingCandidate(
                    category="cardiac",
                    finding_type="orthopnea",
                    trend="new",
                    source=source,
                    observed_at=observed_at,
                )
            )

        return findings

    def _extract_cognitive_behavior_findings(
        self,
        assessment_data: Dict[str, Any],
        source: str,
        observed_at: datetime,
    ) -> List[FindingCandidate]:
        findings: List[FindingCandidate] = []

        if assessment_data.get("cognitive_decline"):
            findings.append(
                FindingCandidate(
                    category="symptom",
                    finding_type="cognitive_decline",
                    trend="declining",
                    source=source,
                    observed_at=observed_at,
                    is_significant_change=True,
                )
            )

        if assessment_data.get("behavior_change"):
            findings.append(
                FindingCandidate(
                    category="symptom",
                    finding_type="behavior_change",
                    trend="new",
                    source=source,
                    observed_at=observed_at,
                    is_significant_change=True,
                )
            )

        return findings

    def _extract_spiritual_findings(
        self,
        assessment_data: Dict[str, Any],
        source: str,
        observed_at: datetime,
    ) -> List[FindingCandidate]:
        findings: List[FindingCandidate] = []

        if assessment_data.get("spiritual_distress"):
            findings.append(
                FindingCandidate(
                    category="spiritual",
                    finding_type="spiritual_distress",
                    trend="new",
                    source=source,
                    observed_at=observed_at,
                )
            )

        if assessment_data.get("fear_of_dying"):
            findings.append(
                FindingCandidate(
                    category="spiritual",
                    finding_type="fear_of_dying",
                    trend="new",
                    source=source,
                    observed_at=observed_at,
                )
            )

        if assessment_data.get("hopelessness"):
            findings.append(
                FindingCandidate(
                    category="spiritual",
                    finding_type="hopelessness",
                    trend="new",
                    source=source,
                    observed_at=observed_at,
                )
            )

        return findings

    def _load_findings(self, db: Session, reasoning_record_id: UUID) -> List[Dict[str, Any]]:
        rows = db.execute(
            text(
                """
                SELECT id, finding_type
                FROM findings
                WHERE reasoning_record_id = :reasoning_record_id
                """
            ),
            {"reasoning_record_id": reasoning_record_id},
        ).mappings().all()

        return [dict(row) for row in rows]

    def _load_active_interpretation_rules(self, db: Session) -> List[Dict[str, Any]]:
        rows = db.execute(
            text(
                """
                SELECT
                    r.id,
                    r.rule_name,
                    r.interpretation_code,
                    r.interpretation_text,
                    r.severity,
                    COALESCE(
                        ARRAY_AGG(c.required_finding_type ORDER BY c.required_finding_type)
                            FILTER (WHERE c.required_finding_type IS NOT NULL),
                        '{}'
                    ) AS required_finding_types
                FROM interpretation_rules r
                LEFT JOIN interpretation_rule_criteria c
                    ON c.rule_id = r.id
                WHERE r.active = TRUE
                GROUP BY
                    r.id,
                    r.rule_name,
                    r.interpretation_code,
                    r.interpretation_text,
                    r.severity
                """
            )
        ).mappings().all()

        return [dict(row) for row in rows]

    def _interpretation_exists(
        self,
        db: Session,
        reasoning_record_id: UUID,
        interpretation_code: str,
    ) -> bool:
        row = db.execute(
            text(
                """
                SELECT 1
                FROM clinical_interpretations
                WHERE reasoning_record_id = :reasoning_record_id
                  AND interpretation_code = :interpretation_code
                LIMIT 1
                """
            ),
            {
                "reasoning_record_id": reasoning_record_id,
                "interpretation_code": interpretation_code,
            },
        ).first()

        return row is not None

    def _insert_interpretation(
        self,
        db: Session,
        reasoning_record_id: UUID,
        rule: Dict[str, Any],
    ) -> Dict[str, Any]:
        row = db.execute(
            text(
                """
                INSERT INTO clinical_interpretations (
                    reasoning_record_id,
                    interpretation_code,
                    statement,
                    severity,
                    confidence,
                    generated_by
                )
                VALUES (
                    :reasoning_record_id,
                    :interpretation_code,
                    :statement,
                    :severity,
                    :confidence,
                    :generated_by
                )
                RETURNING
                    id,
                    interpretation_code,
                    statement,
                    severity
                """
            ),
            {
                "reasoning_record_id": reasoning_record_id,
                "interpretation_code": rule["interpretation_code"],
                "statement": rule["interpretation_text"],
                "severity": rule["severity"],
                "confidence": self.DEFAULT_CONFIDENCE,
                "generated_by": self.GENERATED_BY,
            },
        ).mappings().one()

        return self._clean_row(dict(row))

    def _link_interpretation_findings(
        self,
        db: Session,
        interpretation_id: UUID,
        finding_ids: List[UUID],
    ) -> None:
        for finding_id in finding_ids:
            db.execute(
                text(
                    """
                    INSERT INTO interpretation_findings (
                        interpretation_id,
                        finding_id
                    )
                    VALUES (
                        :interpretation_id,
                        :finding_id
                    )
                    ON CONFLICT DO NOTHING
                    """
                ),
                {
                    "interpretation_id": interpretation_id,
                    "finding_id": finding_id,
                },
            )

    @staticmethod
    def _to_decimal(value: Any) -> Optional[Decimal]:
        if value is None or value == "":
            return None

        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return None

    @staticmethod
    def _observed_at(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        return datetime.now(timezone.utc)

    @staticmethod
    def _pain_severity(score: Decimal) -> str:
        if score >= Decimal("7"):
            return "severe"
        if score >= Decimal("4"):
            return "moderate"
        return "mild"

    @staticmethod
    def _dedupe_findings(findings: List[FindingCandidate]) -> List[FindingCandidate]:
        seen = set()
        result: List[FindingCandidate] = []

        for finding in findings:
            key = (
                finding.category,
                finding.finding_type,
                finding.value_text,
                finding.value_numeric,
                finding.previous_value_text,
                finding.previous_value_numeric,
            )

            if key in seen:
                continue

            seen.add(key)
            result.append(finding)

        return result

    @staticmethod
    def _clean_row(row: Dict[str, Any]) -> Dict[str, Any]:
        cleaned: Dict[str, Any] = {}

        for key, value in row.items():
            if isinstance(value, UUID):
                cleaned[key] = str(value)
            elif isinstance(value, Decimal):
                cleaned[key] = str(value)
            elif isinstance(value, datetime):
                cleaned[key] = value.isoformat()
            else:
                cleaned[key] = value

        return cleaned
