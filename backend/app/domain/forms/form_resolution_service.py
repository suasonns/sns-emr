from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.form_module import FormModule
from app.models.form_package_module import FormPackageModule
from app.models.form_registry_model import FormRegistryModel

from .package_schemas import ResolvedFormPackage


# =====================================================
# LEVEL OF CARE (CMS / OPERATIONS MODEL)
# =====================================================

LEVEL_OF_CARE: dict[str, dict[str, Any]] = {
    "ROUTINE": {
        "allowed_settings": {"HOME", "ALF", "BOARD_AND_CARE", "SNF"},
        "requires_daily_rn_visit": False,
        "requires_md_review": False,
    },
    "RC": {
        "allowed_settings": {"HOME", "ALF", "BOARD_AND_CARE", "SNF"},
        "requires_daily_rn_visit": False,
        "requires_md_review": False,
    },
    "CC": {
        "allowed_settings": {"HOME", "ALF", "BOARD_AND_CARE"},
        "forbidden_settings": {"SNF", "HOSPITAL"},
        "requires_daily_rn_visit": True,
        "requires_md_review": False,
    },
    "GIP": {
        "allowed_settings": {"HOSPITAL", "SNF"},
        "requires_daily_rn_visit": True,
        "requires_md_review": True,
    },
    "IP": {
        "allowed_settings": {"HOSPITAL", "SNF"},
        "requires_daily_rn_visit": True,
        "requires_md_review": True,
    },
    "RESPITE": {
        "allowed_settings": {"SNF"},
        "requires_daily_rn_visit": False,
        "requires_md_review": False,
    },
    "RSP": {
        "allowed_settings": {"SNF"},
        "requires_daily_rn_visit": False,
        "requires_md_review": False,
    },
}


# =====================================================
# CLINICAL GOVERNANCE RULES
# =====================================================

CLINICAL_PROVIDERS = {"RN", "NP"}

RN_ONLY_FORMS = {
    "RN_ASSESS",
}

DISCIPLINE_ALIASES = {
    "MSW": "MSW",
    "SW": "MSW",
    "BSW": "MSW",
    "LCSW": "MSW",
    "SC": "CHAPLAIN",
    "CHHA": "AIDE",
}

FORM_TYPE_ALIASES = {
    "ROUTINE": "ROUTINE_VISIT",
    "ROUTINE_VISIT": "ROUTINE_VISIT",
    "SHORT_FORM": "SHORT_FORM",
    "ASSESS": "ASSESS",
    "SUPV_VISIT": "SUPV_VISIT_ONLY",
    "SUPV_VISIT_ONLY": "SUPV_VISIT_ONLY",
}


# =====================================================
# NORMALIZATION HELPERS
# =====================================================

def normalize_discipline(value: str | None) -> str:
    normalized = (value or "").strip().upper()
    return DISCIPLINE_ALIASES.get(normalized, normalized)


def normalize_form_type(value: str | None) -> str:
    normalized = (value or "").strip().upper()
    return FORM_TYPE_ALIASES.get(normalized, normalized)


def normalize_level_of_care(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().upper()
    return normalized or None


def normalize_event_type(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().upper()
    return normalized or None


def normalize_care_setting(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().upper()
    return normalized or None


# =====================================================
# VALIDATION HELPERS
# =====================================================

def _validate_level_of_care_setting(loc: str, care_setting: str | None) -> None:
    config = LEVEL_OF_CARE.get(loc)
    if not config:
        raise ValueError(f"Invalid level_of_care: {loc}")

    if care_setting:
        forbidden_settings = config.get("forbidden_settings", set())
        allowed_settings = config.get("allowed_settings", set())

        if care_setting in forbidden_settings:
            raise ValueError(f"{loc} cannot be used in {care_setting}")

        if allowed_settings and care_setting not in allowed_settings:
            raise ValueError(f"{care_setting} not valid for {loc}")


def _evaluate_loc_requirements(loc: str | None) -> dict[str, Any]:
    config = LEVEL_OF_CARE.get(loc or "", {})
    return {
        "requires_daily_rn_visit": config.get("requires_daily_rn_visit", False),
        "requires_md_review": config.get("requires_md_review", False),
    }


def _enforce_clinical_rules(discipline: str, primary_form: str) -> None:
    if primary_form in RN_ONLY_FORMS and discipline not in CLINICAL_PROVIDERS:
        raise ValueError(f"{discipline} cannot use {primary_form}")

    if discipline == "LVN" and primary_form == "RN_ASSESS":
        raise ValueError("LVN cannot perform RN comprehensive assessment")


# =====================================================
# DB LIFECYCLE HELPERS
# =====================================================

def _open_db_if_needed(db: Optional[Session]) -> tuple[Session, bool]:
    if db is not None:
        return db, False
    return SessionLocal(), True


def _close_db_if_owned(db: Session, owned: bool) -> None:
    if owned:
        db.close()


# =====================================================
# DB LOOKUP HELPERS
# =====================================================

def _fetch_modules_for_form(db: Session, form_registry_id: Any) -> list[str]:
    rows = (
        db.query(FormModule.module_key)
        .join(
            FormPackageModule,
            FormPackageModule.module_id == FormModule.id,
        )
        .filter(FormPackageModule.form_registry_id == form_registry_id)
        .order_by(FormModule.module_key.asc())
        .all()
    )
    return [row.module_key for row in rows]


def _find_active_form_by_key(
    db: Session,
    *,
    form_key: str,
) -> FormRegistryModel | None:
    return (
        db.query(FormRegistryModel)
        .filter(FormRegistryModel.form_key == form_key)
        .filter(FormRegistryModel.is_active.is_(True))
        .first()
    )


# =====================================================
# REQUEST -> DB FORM KEY MAPPING
# =====================================================

def _mapped_form_key_for_request(
    *,
    discipline: str,
    form_type: str,
    level_of_care: str | None,
    event_type: str | None,
) -> str:
    """
    Map request semantics -> canonical live DB-backed form_key.

    This mapping is intentionally explicit to prevent drift.
    """

    d = normalize_discipline(discipline)
    f = normalize_form_type(form_type)
    
    
    if d == "RN":
        if f == "ASSESS":
            return "RN_ASSESS"
        if f == "ROUTINE_VISIT":
            return "RN_ROUTINE"
        if f == "SHORT_FORM":
            return "RN_ROUTINE"
        if f == "SUPV_VISIT_ONLY":
            return "RN_SUPV"
        raise ValueError(
            f"RN form_type '{f}' is not configured in the DB-backed form engine yet"
        )

    if d == "LVN":
        if f == "ROUTINE_VISIT":
            return "LVN_ROUTINE"
        if f == "SHORT_FORM":
            return "LVN_ROUTINE"
        raise ValueError(
            f"LVN form_type '{f}' is not configured in the DB-backed form engine yet"
        )

    if d == "MSW":
        if f == "ROUTINE_VISIT":
            return "MSW_ROUTINE"
        if f == "SHORT_FORM":
            return "MSW_ROUTINE"
        raise ValueError(
            f"MSW form_type '{f}' is not configured in the DB-backed form engine yet"
        )

    if d == "CHAPLAIN":
        if f == "ROUTINE_VISIT":
            return "CHAPLAIN_ROUTINE"
        if f == "SHORT_FORM":
            return "CHAPLAIN_ROUTINE"
        raise ValueError(
            f"CHAPLAIN form_type '{f}' is not configured in the DB-backed form engine yet"
        )

    if d == "AIDE":
        if f == "ROUTINE_VISIT":
            return "HHA_VISIT"
        if f == "SHORT_FORM":
            return "HHA_VISIT"
        raise ValueError(
            f"AIDE form_type '{f}' is not configured in the DB-backed form engine yet"
        )

    raise ValueError(
        f"No DB-backed form mapping exists for discipline={d}, form_type={f}"
    )


def _attached_form_keys_for_request(
    *,
    discipline: str,
    form_type: str,
    primary_form_key: str,
) -> list[str]:
    """
    Minimal explicit attached-form mapping until attached forms are fully DB-driven.
    """

    d = normalize_discipline(discipline)
    f = normalize_form_type(form_type)

    if d == "RN" and f == "SUPV_VISIT_ONLY" and primary_form_key == "RN_SUPV":
        return ["POC_UPDATE"]

    return []


# =====================================================
# MAIN RESOLVER (DB-DRIVEN CANONICAL)
# =====================================================

def resolve_form_package(
    *,
    discipline: str,
    form_type: str,
    level_of_care: str | None = None,
    event_type: str | None = None,
    care_setting: str | None = None,
    db: Optional[Session] = None,
) -> dict[str, Any]:
    """
    Canonical DB-driven form resolver.

    Returns:
        {
            "form_family": str,
            "form_key": str,
            "primary_modules": list[str],
            "required_modules": list[str],
            "forbidden_modules": list[str],
            "attached_form_keys": list[str],
            "notes": str | None,
            "resolved_by": "db_engine",
            "level_of_care": str | None,
            "event_type": str | None,
            "requires_daily_rn_visit": bool,
            "requires_md_review": bool,
        }
    """

    d = normalize_discipline(discipline)
    f = normalize_form_type(form_type)
    loc = normalize_level_of_care(level_of_care)
    e = normalize_event_type(event_type)
    setting = normalize_care_setting(care_setting)
    
    # ✅ CRITICAL SAFETY RULE: CHANGE OF CONDITION
    
    if f == "SHORT_FORM" and e is not None:
        if d == "RN":
            f = "ASSESS"       # ✅ RN comprehensive
        elif d == "LVN":
            f = "ROUTINE_VISIT"  # ✅ LVN routine
        
    loc_validation = {
        "RC": "ROUTINE",
        "IP": "GIP",
        "RSP": "RESPITE",
    }.get(loc, loc)

    if loc_validation:
        _validate_level_of_care_setting(loc_validation, setting)

    db_session, owned = _open_db_if_needed(db)

    try:
        target_form_key = _mapped_form_key_for_request(
            discipline=d,
            form_type=f,
            level_of_care=loc,
            event_type=e,
        )

        form = _find_active_form_by_key(
            db_session,
            form_key=target_form_key,
        )

        if not form:
            raise ValueError(
                f"Configured form_key '{target_form_key}' does not exist or is inactive"
            )

        modules = _fetch_modules_for_form(db_session, form.id)

        if not modules:
            raise ValueError(
                f"Form '{form.form_key}' has no mapped modules in form_package_modules"
            )

        # ✅ SHORT_FORM override (CRITICAL BUSINESS RULE)
        if f == "SHORT_FORM":
            modules = [
                "narrative",
                "visit_summary",
                "vitals",
                "pain_assessment",
                "symptom_follow_up",
                "teaching",
            ]

        # ✅ enforce after override (correct order)
        _enforce_clinical_rules(d, form.form_key)

        resolved = ResolvedFormPackage(
            form_family=form.form_family,
            form_key=form.form_key,
            primary_modules=modules,
            required_modules=list(modules),
            forbidden_modules=[],
            attached_form_keys=_attached_form_keys_for_request(
                discipline=d,
                form_type=f,
                primary_form_key=form.form_key,
            ),
            notes=None,
        )

        payload = resolved.model_dump()
        payload["resolved_by"] = "db_engine"
        payload["form_type"] = f
        payload["level_of_care"] = loc
        payload["event_type"] = e
        payload.update(_evaluate_loc_requirements(loc_validation))

        return payload

    finally:
        _close_db_if_owned(db_session, owned)