from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.icd10_master import ICD10Master
from app.models.icd10_hospice_policy import ICD10HospicePolicy
from app.services.icd10_policy_service import validate_primary_diagnosis


DiagnosisRole = Literal[
    "PRIMARY",
    "SECONDARY",
    "COMORBIDITY",
]

WorkflowContext = Literal[
    "REFERRAL",
    "FACESHEET",
    "RN_ICA",
    "CTI",
    "POC",
]


class ICD10ResolutionError(ValueError):
    """
    Raised when a diagnosis cannot be resolved to the ICD10 SSOT
    or is not allowed for the requested hospice use.
    """


@dataclass(frozen=True)
class ResolvedICD10Diagnosis:
    icd10_code: str
    diagnosis_description: str
    display_name: str

    diagnosis_role: DiagnosisRole
    workflow_context: WorkflowContext

    allow_primary_dx: bool
    allow_secondary_dx: bool
    allow_comorbidity: bool

    billing_primary_allowed: bool

    requires_md_review: bool
    requires_idg_review: bool
    requires_supporting_documentation: bool

    default_terminal_related: bool
    medication_relatedness_relevant: bool

    lcd_category: str | None
    block_reason: str | None
    warning_message: str | None


def _clean_text(value: Any):
    if value is None:
        return None

    cleaned = str(value).strip()

    if not cleaned:
        return None

    return cleaned


def _normalize_code(value: Any):
    return (
        str(value or "")
        .strip()
        .upper()
        .replace(".", "")
        .replace(" ", "")
    )


def _normalize_role(value: Any):
    cleaned = str(value or "").strip().upper()

    if cleaned not in {"PRIMARY", "SECONDARY", "COMORBIDITY"}:
        raise ICD10ResolutionError(
            "Unsupported diagnosis role: " + str(cleaned or value)
        )

    return cleaned


def _normalize_workflow_context(value: Any):
    cleaned = str(value or "").strip().upper()

    if cleaned not in {"REFERRAL", "FACESHEET", "RN_ICA", "CTI", "POC"}:
        raise ICD10ResolutionError(
            "Unsupported workflow context: " + str(cleaned or value)
        )

    return cleaned


def _looks_like_icd10_code(value):
    """
    Conservative ICD10-CM code detector.

    Accepts compact and dotted forms:
        I509
        I50.9
        C3490
        C34.90
        N18.30
        Z51.5
        C7A.090
        U07.1

    Existence is still validated against icd10_master.
    """

    normalized = _normalize_code(value)

    if not normalized:
        return False

    return bool(
        re.fullmatch(
            r"[A-Z][A-Z0-9]{2,6}",
            normalized,
        )
    )


def _extract_code_from_display_name(value: Any):
    """
    Extract ICD10 code from display format:

        End stage heart failure (I50.84)

    The description portion is not authoritative.
    The ICD10 master table remains the SSOT for official description.
    """

    cleaned = str(value or "").strip()

    if "(" not in cleaned or not cleaned.endswith(")"):
        return None

    _, code_part = cleaned.rsplit("(", 1)

    code = code_part.rstrip(")").strip().upper()

    if not code:
        return None

    if not _looks_like_icd10_code(code):
        return None

    return code


def _find_icd10_by_code(
    db: Session,
    *,
    code: str,
):
    normalized_code = _normalize_code(code)

    if not normalized_code:
        return None

    return (
        db.query(ICD10Master)
        .filter(
            ICD10Master.icd10_code == normalized_code,
            ICD10Master.active.is_(True),
        )
        .first()
    )


def _find_icd10_by_text(
    db: Session,
    *,
    query_text: str,
):
    cleaned = str(query_text or "").strip()

    if not cleaned:
        return []

    search_value = "%" + cleaned + "%"

    return (
        db.query(ICD10Master)
        .filter(
            ICD10Master.active.is_(True),
            or_(
                ICD10Master.diagnosis_description.ilike(search_value),
                ICD10Master.display_name.ilike(search_value),
                ICD10Master.search_text.ilike(search_value),
            ),
        )
        .order_by(
            ICD10Master.icd10_code.asc(),
        )
        .limit(25)
        .all()
    )


def _get_policy_for_code(
    db: Session,
    *,
    icd10_code: str,
):
    normalized_code = _normalize_code(icd10_code)

    if not normalized_code:
        return None

    return (
        db.query(ICD10HospicePolicy)
        .filter(
            ICD10HospicePolicy.icd10_code == normalized_code,
            ICD10HospicePolicy.active.is_(True),
        )
        .first()
    )


def _validate_role_allowed(
    *,
    policy: ICD10HospicePolicy,
    diagnosis_role: DiagnosisRole,
):
    if diagnosis_role == "PRIMARY":
        if not policy.allow_primary_dx:
            raise ICD10ResolutionError(
                policy.block_reason
                or "This ICD10 code is not allowed as a primary hospice diagnosis."
            )

        if not policy.billing_primary_allowed:
            raise ICD10ResolutionError(
                policy.block_reason
                or "This ICD10 code is not allowed as a billable primary hospice diagnosis."
            )

        return

    if diagnosis_role == "SECONDARY":
        if not policy.allow_secondary_dx:
            raise ICD10ResolutionError(
                policy.block_reason
                or "This ICD10 code is not allowed as a secondary hospice diagnosis."
            )

        return

    if diagnosis_role == "COMORBIDITY":
        if not policy.allow_comorbidity:
            raise ICD10ResolutionError(
                policy.block_reason
                or "This ICD10 code is not allowed as a hospice comorbidity."
            )

        return

    raise ICD10ResolutionError(
        "Unsupported diagnosis role: " + str(diagnosis_role)
    )


def _validate_workflow_allowed(
    *,
    policy: ICD10HospicePolicy,
    workflow_context: WorkflowContext,
):
    if workflow_context == "REFERRAL":
        if not policy.allow_referral_dx:
            raise ICD10ResolutionError(
                policy.block_reason
                or "This ICD10 code is not allowed during referral/intake."
            )
        return

    if workflow_context == "FACESHEET":
        if not policy.allow_facesheet_dx:
            raise ICD10ResolutionError(
                policy.block_reason
                or "This ICD10 code is not allowed on the facesheet."
            )
        return

    if workflow_context == "RN_ICA":
        if not policy.allow_rn_ica_dx:
            raise ICD10ResolutionError(
                policy.block_reason
                or "This ICD10 code is not allowed during RN ICA."
            )
        return

    if workflow_context == "CTI":
        if not policy.allow_cti_dx:
            raise ICD10ResolutionError(
                policy.block_reason
                or "This ICD10 code is not allowed for CTI."
            )
        return

    if workflow_context == "POC":
        if not policy.allow_poc_dx:
            raise ICD10ResolutionError(
                policy.block_reason
                or "This ICD10 code is not allowed in the Plan of Care."
            )
        return

    raise ICD10ResolutionError(
        "Unsupported workflow context: " + str(workflow_context)
    )


def _validate_primary_policy_if_needed(
    *,
    icd10_code: str,
    diagnosis_role: DiagnosisRole,
):
    """
    JSON-driven primary diagnosis governance.

    This must run after the ICD10 code is resolved from any input path:
        direct code
        display name
        free text single match

    It must only apply to PRIMARY diagnosis selection.
    """

    if diagnosis_role != "PRIMARY":
        return

    primary_policy = validate_primary_diagnosis(
        icd10_code
    )

    if not primary_policy["allowed"]:
        raise ICD10ResolutionError(
            primary_policy["message"]
            or "This ICD10 diagnosis is not allowed as the hospice primary diagnosis."
        )


def resolve_icd10_diagnosis_for_use(
    db: Session,
    *,
    diagnosis_input: Any,
    diagnosis_role: DiagnosisRole,
    workflow_context: WorkflowContext,
):
    """
    Resolve diagnosis input through ICD10 SSOT.

    Accepts:
        I509
        I50.9
        End stage heart failure
        End stage heart failure (I50.84)

    Uses:
        icd10_master
        icd10_hospice_policy when policy rows exist
        app/config/icd10_primary_dx_policy.json for primary diagnosis blocking

    Important:
        If disease-name text matches multiple ICD10 codes, this resolver
        does not guess. It raises an error requiring user ICD10 selection
        or MD / office clarification.
    """

    if db is None:
        raise ICD10ResolutionError(
            "Database session is required for ICD10 resolution."
        )

    normalized_role = _normalize_role(diagnosis_role)
    normalized_context = _normalize_workflow_context(workflow_context)

    cleaned_input = _clean_text(diagnosis_input)

    if not cleaned_input:
        raise ICD10ResolutionError(
            "Diagnosis is required."
        )

    extracted_code = _extract_code_from_display_name(cleaned_input)

    if extracted_code:
        icd10 = _find_icd10_by_code(
            db,
            code=extracted_code,
        )

        if not icd10:
            raise ICD10ResolutionError(
                "ICD10 code not found or inactive: " + str(extracted_code)
            )

    elif _looks_like_icd10_code(cleaned_input):
        normalized_code = _normalize_code(cleaned_input)

        icd10 = _find_icd10_by_code(
            db,
            code=normalized_code,
        )

        if not icd10:
            raise ICD10ResolutionError(
                "ICD10 code not found or inactive: " + str(normalized_code)
            )

    else:
        matches = _find_icd10_by_text(
            db,
            query_text=cleaned_input,
        )

        if not matches:
            raise ICD10ResolutionError(
                "No ICD10 diagnosis found for: " + str(cleaned_input)
            )

        if len(matches) != 1:
            options = [
                match.display_name
                for match in matches[:10]
            ]

            raise ICD10ResolutionError(
                "Multiple ICD10 matches found. "
                "Select the correct ICD10 code. "
                "Options: " + str(options)
            )

        icd10 = matches[0]

    #
    # JSON Primary Diagnosis Governance
    #
    # This is intentionally placed after ICD resolution so it applies
    # to direct code input, display-name input, and free-text resolution.
    #
    _validate_primary_policy_if_needed(
        icd10_code=icd10.icd10_code,
        diagnosis_role=normalized_role,
    )

    policy = _get_policy_for_code(
        db,
        icd10_code=icd10.icd10_code,
    )

    #
    # Temporary fallback during ICD policy table expansion.
    #
    # Current state:
    #     icd10_master contains full CDC dataset
    #     icd10_hospice_policy is not fully populated yet
    #
    # Missing policy rows must not crash valid diagnosis selection.
    #
    if policy:

        _validate_role_allowed(
            policy=policy,
            diagnosis_role=normalized_role,
        )

        _validate_workflow_allowed(
            policy=policy,
            workflow_context=normalized_context,
        )

    return ResolvedICD10Diagnosis(
        icd10_code=icd10.icd10_code,
        diagnosis_description=icd10.diagnosis_description,
        display_name=icd10.display_name,
        diagnosis_role=normalized_role,
        workflow_context=normalized_context,

        allow_primary_dx=(
            policy.allow_primary_dx
            if policy
            else True
        ),

        allow_secondary_dx=(
            policy.allow_secondary_dx
            if policy
            else True
        ),

        allow_comorbidity=(
            policy.allow_comorbidity
            if policy
            else True
        ),

        billing_primary_allowed=(
            policy.billing_primary_allowed
            if policy
            else True
        ),

        requires_md_review=(
            policy.requires_md_review
            if policy
            else False
        ),

        requires_idg_review=(
            policy.requires_idg_review
            if policy
            else False
        ),

        requires_supporting_documentation=(
            policy.requires_supporting_documentation
            if policy
            else False
        ),

        default_terminal_related=(
            policy.default_terminal_related
            if policy
            else False
        ),

        medication_relatedness_relevant=(
            policy.medication_relatedness_relevant
            if policy
            else False
        ),

        lcd_category=(
            policy.lcd_category
            if policy
            else None
        ),

        block_reason=(
            policy.block_reason
            if policy
            else None
        ),

        warning_message=(
            policy.warning_message
            if policy
            else None
        ),
    )


def search_icd10_diagnoses(
    db: Session,
    *,
    query_text: Any,
    limit: int = 25,
):
    """
    Search ICD10 master locally by code, description, display name, or search text.

    This function does not enforce hospice policy.
    Use resolve_icd10_diagnosis_for_use() when selecting a diagnosis
    for PRIMARY / SECONDARY / COMORBIDITY use.
    """

    if db is None:
        raise ICD10ResolutionError(
            "Database session is required for ICD10 search."
        )

    cleaned = _clean_text(query_text)

    if not cleaned:
        return []

    if _looks_like_icd10_code(cleaned):
        icd10 = _find_icd10_by_code(
            db,
            code=cleaned,
        )

        if not icd10:
            return []

        return [
            {
                "icd10_code": icd10.icd10_code,
                "diagnosis_description": icd10.diagnosis_description,
                "display_name": icd10.display_name,
                "chapter_code": icd10.chapter_code,
                "chapter_name": icd10.chapter_name,
            }
        ]

    search_value = "%" + cleaned + "%"

    limit_value = max(
        1,
        min(
            int(limit or 25),
            50,
        ),
    )

    rows = (
        db.query(ICD10Master)
        .filter(
            ICD10Master.active.is_(True),
            or_(
                ICD10Master.icd10_code.ilike(search_value),
                ICD10Master.diagnosis_description.ilike(search_value),
                ICD10Master.display_name.ilike(search_value),
                ICD10Master.search_text.ilike(search_value),
            ),
        )
        .order_by(
            ICD10Master.icd10_code.asc(),
        )
        .limit(limit_value)
        .all()
    )

    return [
        {
            "icd10_code": row.icd10_code,
            "diagnosis_description": row.diagnosis_description,
            "display_name": row.display_name,
            "chapter_code": row.chapter_code,
            "chapter_name": row.chapter_name,
        }
        for row in rows
    ]
