"""ADR schema binding map (candidate-based resolver).

Purpose:
- Map audit queries to the real DB schema without hard crashes.
- Prefer explicit configuration later; for now, choose from known candidates.

This file is *not* a policy file. Policy lives in:
- backend/docs/compliance/ADR_AUDIT_RULES.md

Do not add new audit rules here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class TableBinding:
    table: str
    columns: Dict[str, str]


# Candidate tables/columns observed/expected in SNS EMR docs.
# Adjust these lists to your actual schema once confirmed.

PATIENTS_CANDIDATES: List[TableBinding] = [
    TableBinding(table="patients", columns={
        "id": "id",
        "soc": "soc_date",
        "dc": "discharge_date",
        "mrn": "mrn",
        "mrn_not_used": "mrn_not_used",
    }),
]

VISITS_CANDIDATES: List[TableBinding] = [
    TableBinding(table="visits", columns={
        "patient_id": "patient_id",
        "visit_date": "visit_date",      # may be visit_datetime in some schemas
        "status": "status",
    }),
    TableBinding(table="visits", columns={
        "patient_id": "patient_id",
        "visit_date": "visit_datetime",  # fallback
        "status": "status",
    }),
]

DOCUMENTS_CANDIDATES: List[TableBinding] = [
    TableBinding(table="documents", columns={
        "patient_id": "patient_id",
        "doc_category": "doc_category",
        "doc_type": "doc_type",
        "status": "status",
        "document_date": "document_date",
        "included_in_adr": "included_in_adr",
        "signer_is_patient": "signer_is_patient",
        "representative_reason": "representative_reason",
        "noncovered_items_state": "noncovered_items_state",
    }),
    TableBinding(table="document_records", columns={
        "patient_id": "patient_id",
        "doc_category": "category",
        "doc_type": "doc_type",
        "status": "status",
        "document_date": "document_date",
        "included_in_adr": "included_in_adr",
        "signer_is_patient": "signer_is_patient",
        "representative_reason": "representative_reason",
        "noncovered_items_state": "noncovered_items_state",
    }),
]

ASSESSMENTS_CANDIDATES: List[TableBinding] = [
    TableBinding(table="assessments", columns={
        "patient_id": "patient_id",
        "assessment_type": "assessment_type",
        "status": "status",
    }),
]

CERTIFICATIONS_CANDIDATES: List[TableBinding] = [
    TableBinding(table="certifications", columns={
        "patient_id": "patient_id",
        "status": "status",
    }),
    TableBinding(table="eligibility_decisions", columns={
        "patient_id": "patient_id",
        "decision_type": "decision_type",
        "status": "status",
    }),
]

BENEFIT_PERIODS_CANDIDATES: List[TableBinding] = [
    TableBinding(table="benefit_periods", columns={
        "patient_id": "patient_id",
        "period_number": "period_number",
        "start_date": "start_date",
        "end_date": "end_date",
    }),
    TableBinding(table="benefit_periods", columns={
        "patient_id": "patient_id",
        "period_number": "period_number",
        "start_date": "effective_start_date",
        "end_date": "effective_end_date",
    }),
]

F2F_CANDIDATES: List[TableBinding] = [
    TableBinding(table="f2f_encounters", columns={
        "patient_id": "patient_id",
        "status": "status",
        "encounter_date": "encounter_date",
    }),
    TableBinding(table="face_to_face", columns={
        "patient_id": "patient_id",
        "status": "status",
        "encounter_date": "encounter_date",
    }),
]

ORDERS_CANDIDATES: List[TableBinding] = [
    TableBinding(table="orders", columns={
        "patient_id": "patient_id",
        "order_date": "order_date",
        "signature_required": "signature_required",
        "signed_at": "signed_at",
    }),
]

IDG_CANDIDATES: List[TableBinding] = [
    TableBinding(table="idg_meetings", columns={
        "patient_id": "patient_id",
        "posted_date": "posted_date",
        "status": "status",
    }),
]
