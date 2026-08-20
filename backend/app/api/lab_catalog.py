# app/api/lab_catalog.py

"""
Serves the CPT-coded lab test catalog for the Orders Hub 'Lab' order type's
categorized test picker (replaces free-text lab order entry with checkboxes
grouped by category, matching HospiceMD's "Lab Tests" modal pattern but
improved with structured JSON instead of a static form).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends

from app.core.security import CurrentUser
from app.core.permissions import require_roles

router = APIRouter(prefix="/lab-catalog", tags=["lab-catalog"])

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "lab_test_catalog.json"

CLINICAL_ROLES = ["LVN", "RN", "NP", "MD", "Surveyor"]


@lru_cache(maxsize=1)
def _load_catalog() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("", summary="Get the categorized lab test catalog (CPT codes + names)")
def get_lab_catalog(
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    return _load_catalog()
