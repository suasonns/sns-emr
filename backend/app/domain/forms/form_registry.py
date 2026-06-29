from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.models.enums import NoteFormFamily, TaskDiscipline


# =========================================================
# VISIT HEADER
# =========================================================

VISIT_HEADER_FIELDS = [
    "created_by",
    "staff_assigned",
    "discipline",
    "care_level",
    "visit_type",
    "visit_schedule_type",
    "visit_date",
    "time_in",
    "time_out",
    "duration",
    "form_type",
]


# =========================================================
# MODULE KEYS
# =========================================================

MOD_PAIN = "pain"
MOD_VITALS = "vitals"
MOD_SYMPTOMS = "symptoms"
MOD_NARRATIVE = "narrative"
MOD_ROS = "review_of_systems"
MOD_ORDERS = "orders"
MOD_FUNCTIONAL_SCORES = "functional_scores"

MOD_PSYCHOSOCIAL = "psychosocial"
MOD_SPIRITUAL = "spiritual"

MOD_CC_ENTRY = "cc_shift_entry"
MOD_CARE_PROVIDED = "care_provided"


# =========================================================
# HELPERS
# =========================================================

def _pkg(
    *,
    form_family,
    primary_form: str,
    modules: list[str],
    attached_forms: list[str] | None = None,
    is_shared_cc_form: bool = False,
):
    return {
        "form_family": form_family,
        "primary_form": primary_form,
        "modules": modules,
        "attached_forms": attached_forms or [],
        "is_shared_cc_form": is_shared_cc_form,
        "visit_header_fields": VISIT_HEADER_FIELDS,
    }


def _value(v):
    if v is None:
        return None
    return str(getattr(v, "value", v)).strip().upper()


# =========================================================
# NORMALIZATION
# =========================================================

DISCIPLINE_ALIASES = {
    "MSW": "SW",
    "BSW": "SW",
    "LCSW": "SW",
    "SC": "CHAPLAIN",
    "CHHA": "AIDE",
}


def normalize_discipline(v):
    return DISCIPLINE_ALIASES.get(_value(v), _value(v))


def normalize_form_type(v):
    return _value(v)


def normalize_event_type(v):
    return _value(v)


def normalize_level_of_care(v):
    return _value(v)


# =========================================================
# TASK DISCIPLINE → FORM FAMILY
# =========================================================

TASK_DISCIPLINE_TO_FORM_FAMILY = {
    TaskDiscipline.RN: NoteFormFamily.CLINICAL,
    TaskDiscipline.LVN: NoteFormFamily.CLINICAL,
    TaskDiscipline.NP: NoteFormFamily.CLINICAL,
    TaskDiscipline.MD: NoteFormFamily.CLINICAL,

    TaskDiscipline.CHHA: NoteFormFamily.SUPPORT,

    TaskDiscipline.SW: NoteFormFamily.PSYCHOSOCIAL,
    TaskDiscipline.MSW: NoteFormFamily.PSYCHOSOCIAL,
    TaskDiscipline.BSW: NoteFormFamily.PSYCHOSOCIAL,
    TaskDiscipline.LCSW: NoteFormFamily.PSYCHOSOCIAL,

    TaskDiscipline.SC: NoteFormFamily.SPIRITUAL,
    TaskDiscipline.CHAPLAIN: NoteFormFamily.SPIRITUAL,
}


def required_form_family_for_task_discipline(discipline):
    if not discipline:
        return None

    normalized = _value(discipline)

    for d, family in TASK_DISCIPLINE_TO_FORM_FAMILY.items():
        if d.value == normalized:
            return family

    return None


def note_matches_task_family(note_form_family, task_discipline):
    required = required_form_family_for_task_discipline(task_discipline)

    if not required:
        return False

    return _value(note_form_family) == required.value


# =========================================================
# FORM REGISTRY (PRODUCTION GRADE)
# =========================================================

FORM_REGISTRY = {
    "RN": {
        "ASSESS": _pkg(
            form_family=NoteFormFamily.CLINICAL,
            primary_form="RN_ASSESS_V1",
            modules=[MOD_PAIN, MOD_VITALS, MOD_ROS, MOD_NARRATIVE, MOD_FUNCTIONAL_SCORES],
            attached_forms=[],
        ),
        "SHORT_FORM": _pkg(
            form_family=NoteFormFamily.CLINICAL,
            primary_form="RN_SHORT_FORM_V1",
            modules=[MOD_PAIN, MOD_VITALS, MOD_NARRATIVE],
            attached_forms=[],
        ),
        "SUPERVISORY": _pkg(
            form_family=NoteFormFamily.CLINICAL,
            primary_form="RN_SUPERVISORY_V1",
            modules=[MOD_NARRATIVE],
            attached_forms=["POC_UPDATE"],
        ),
    },

    "LVN": {
        "SHORT_FORM": _pkg(
            form_family=NoteFormFamily.CLINICAL,
            primary_form="LVN_VISIT_V1",
            modules=[MOD_PAIN, MOD_VITALS, MOD_NARRATIVE],
            attached_forms=[],
        ),
    },

    "AIDE": {
        "SHORT_FORM": _pkg(
            form_family=NoteFormFamily.SUPPORT,
            primary_form="AIDE_VISIT_V1",
            modules=[MOD_CARE_PROVIDED, MOD_NARRATIVE],
            attached_forms=[],
        ),
    },

    "SW": {
        "SHORT_FORM": _pkg(
            form_family=NoteFormFamily.PSYCHOSOCIAL,
            primary_form="SW_VISIT_V1",
            modules=[MOD_PSYCHOSOCIAL, MOD_NARRATIVE],
            attached_forms=[],
        ),
    },

    "CHAPLAIN": {
        "SHORT_FORM": _pkg(
            form_family=NoteFormFamily.SPIRITUAL,
            primary_form="SC_VISIT_V1",
            modules=[MOD_SPIRITUAL, MOD_NARRATIVE],
            attached_forms=[],
        ),
    },
}


# =========================================================
# ACCESS FUNCTIONS (SAFE)
# =========================================================

def get_base_form_config(*, discipline, form_type):
    d = normalize_discipline(discipline)
    f = normalize_form_type(form_type)

    if d not in FORM_REGISTRY:
        raise ValueError(f"No registry for discipline: {d}")

    if f not in FORM_REGISTRY[d]:
        raise ValueError(f"No form type {f} for discipline {d}")

    return deepcopy(FORM_REGISTRY[d][f])


def get_event_form_config(*, discipline, event_type):
    return None


def get_cc_package(discipline: str):
    d = normalize_discipline(discipline)

    if d in {"RN", "LVN"}:
        return deepcopy(
            _pkg(
                form_family=NoteFormFamily.CLINICAL,
                primary_form="CC_SHIFT_LOG",
                modules=[MOD_CC_ENTRY, MOD_PAIN, MOD_SYMPTOMS, MOD_NARRATIVE],
                is_shared_cc_form=True,
            )
        )

    if d == "AIDE":
        return deepcopy(
            _pkg(
                form_family=NoteFormFamily.SUPPORT,
                primary_form="CC_SHIFT_LOG",
                modules=[MOD_CC_ENTRY, MOD_CARE_PROVIDED, MOD_NARRATIVE],
                is_shared_cc_form=True,
            )
        )

    return None