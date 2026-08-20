from __future__ import annotations

from sqlalchemy import func


def format_person_name(person, fallback: str = "") -> str:
    parts = (
        getattr(person, "first_name", None),
        getattr(person, "middle_name", None),
        getattr(person, "last_name", None),
    )
    return " ".join(str(part).strip() for part in parts if part and str(part).strip()) or fallback


def person_name_expression(model, fallback):
    return func.coalesce(
        func.nullif(
            func.trim(func.concat_ws(" ", model.first_name, model.middle_name, model.last_name)),
            "",
        ),
        fallback,
    )