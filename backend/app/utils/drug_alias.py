"""
Utility functions for medication name normalization.

IMPORTANT:
- No database access
- No SQLAlchemy imports
- No FastAPI dependencies
- Deterministic and audit-safe
"""

from typing import Optional


def normalize_drug_name(name: Optional[str]) -> Optional[str]:
    """
    Normalize a medication name for consistent comparison and matching.

    Rules:
    - Preserve original clinical meaning
    - Do NOT infer dosage, route, or frequency
    - Do NOT change intent, only formatting
    - Safe for MAR, POC, IDG, and reconciliation workflows

    Examples:
    - " Tylenol " -> "tylenol"
    - "Morphine Sulfate" -> "morphine sulfate"
    - None -> None
    """

    if not name:
        return name

    # Basic normalization only
    normalized = name.strip().lower()

    # Collapse internal whitespace
    normalized = " ".join(normalized.split())

    return normalized