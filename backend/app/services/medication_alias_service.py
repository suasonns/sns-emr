# app/services/medication_alias_service.py

"""
Medication alias resolution service.

Bridges:
- utility-level normalization (no DB)
- database-backed alias resolution

Compliance notes:
- Does NOT alter clinical intent
- Deterministic and auditable
- Safe for MAR, POC, IDG, and medication reconciliation
"""

from sqlalchemy.orm import Session

from app.utils.drug_alias import normalize_drug_name
from app.models.drug_alias import DrugAlias


def resolve_canonical_medication_name(
    session: Session,
    raw_name: str,
) -> str:
    """
    Resolve a medication name to its canonical form.

    Steps:
    1. Normalize formatting (utils)
    2. Look up alias in drug_aliases table
    3. Fall back to normalized value if no alias exists
    """

    if not raw_name:
        return raw_name

    normalized = normalize_drug_name(raw_name)
    if not normalized:
        return normalized

    alias = (
        session.query(DrugAlias)
        .filter(DrugAlias.alias_text == normalized)
        .first()
    )
    if alias:
        return alias.canonical_text

    return normalized