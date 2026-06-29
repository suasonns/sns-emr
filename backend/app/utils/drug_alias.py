"""
Utility functions for medication name normalization.

IMPORTANT:
- No database access
- No SQLAlchemy imports
- No FastAPI dependencies
- Deterministic and audit-safe
"""

from __future__ import annotations

from typing import Optional


def normalize_drug_name(name: Optional[str]) -> str:
    """
    Normalize a medication name for consistent comparison and matching.

    Rules:
    - Preserve clinical meaning
    - Do NOT infer dosage, route, or frequency
    - Do NOT change intent, only formatting
    - Safe for MAR, POC, IDG, and reconciliation workflows

    Behavior:
    - Returns empty string for None or invalid input
    - Lowercases for consistent matching (not for display)
    - Collapses whitespace
    - Removes surrounding punctuation noise

    Examples:
    - " Tylenol " -> "tylenol"
    - "Morphine Sulfate" -> "morphine sulfate"
    - None -> ""
    """

    # ---------------------------------------------------------
    # SAFE INPUT HANDLING
    # ---------------------------------------------------------
    if not name:
        return ""

    # ensure string input
    value = str(name)

    # ---------------------------------------------------------
    # BASIC NORMALIZATION
    # ---------------------------------------------------------
    normalized = value.strip().lower()

    # collapse internal whitespace
    normalized = " ".join(normalized.split())

    # ---------------------------------------------------------
    # CLEAN COMMON NON-CLINICAL CHARACTERS
    # ---------------------------------------------------------
    # remove trademark symbols and common noise
    normalized = normalized.replace("®", "").replace("™", "")

    # strip leftover outer punctuation
    normalized = normalized.strip(".,;:()[]{}")

    return normalized
