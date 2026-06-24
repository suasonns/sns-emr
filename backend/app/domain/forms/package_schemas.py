from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel

from .enums import FormFamily


class ResolvedFormPackage(BaseModel):
    form_family: FormFamily
    form_key: str
    primary_modules: List[str]
    required_modules: List[str]
    forbidden_modules: List[str]
    attached_form_keys: List[str]
    notes: Optional[str] = None