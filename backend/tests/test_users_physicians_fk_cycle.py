"""Regression guard for the users<->physicians foreign-key cycle.

users.physician_id -> physicians.id (Physician Identity Mapping, added
2026-08-21) and physicians.created_by / physicians.updated_by -> users.id
(standard audit columns) form a mutual dependency. Before this fix,
SQLAlchemy could not topologically sort these two tables and emitted a
SAWarning every time Alembic autogenerate (or anything calling
Base.metadata.sorted_tables) ran, warning that "this warning may raise an
error in a future release."

The fix marks users.physician_id's ForeignKey with use_alter=True (the same
established pattern already used for other cyclic references in this
codebase, e.g. tenants.default_medical_director_physician_id), which tells
SQLAlchemy to defer that specific edge instead of trying to satisfy both
directions in a single CREATE/DROP ordering. This is metadata-level only:
it changes neither the live database schema nor the FK constraint's name.
"""
from __future__ import annotations

import warnings

from app.db.base import Base


def test_sorted_tables_does_not_warn_on_users_physicians_cycle() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        # This is exactly what Alembic's autogenerate/compare machinery (and
        # metadata.create_all/drop_all) calls internally; it used to raise:
        # "Cannot correctly sort tables; there are unresolvable cycles
        # between tables 'physicians, users'".
        list(Base.metadata.sorted_tables)

    cycle_warnings = [
        w for w in caught
        if "physicians" in str(w.message) and "users" in str(w.message)
        and "cycle" in str(w.message).lower()
    ]
    assert not cycle_warnings, (
        "users<->physicians FK cycle warning reappeared: "
        f"{[str(w.message) for w in cycle_warnings]}"
    )


def test_users_physician_id_fk_constraint_name_unchanged() -> None:
    users_table = Base.metadata.tables["users"]
    fk = next(
        fk for fk in users_table.foreign_keys
        if fk.column.table.name == "physicians"
    )
    # Must match the live database's existing constraint name exactly, or
    # the next `alembic revision --autogenerate` would detect a rename and
    # report false drift.
    assert fk.constraint.name == "fk_users_physician_id_physicians"
    assert fk.constraint.use_alter is True
