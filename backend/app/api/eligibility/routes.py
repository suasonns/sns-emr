from types import SimpleNamespace
from typing import Any, Dict, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.config.lcd.loader import load_lcd_configs
from app.services.eligibility.engine import (
    detect_lcd_config,
    evaluate_hospice_eligibility,
    get_lcd_config_for_disease,
)

router = APIRouter(
    prefix="/eligibility",
    tags=["Eligibility"],
)


# ---------------------------------------------------------------------
# REQUEST / RESPONSE MODELS
# ---------------------------------------------------------------------

class LCDEvaluateRequest(BaseModel):
    patient: Dict[str, Any] = Field(default_factory=dict)
    facts: Dict[str, Any] = Field(default_factory=dict)
    admission_date: Optional[str] = None


class LCDDetectResponse(BaseModel):
    disease: str
    lcd_reference: str
    source_document: str


# ---------------------------------------------------------------------
# ELIGIBILITY EVALUATION (LCD ENGINE — the real, disease-specific engine
# used by the frontend; see app/services/eligibility/engine.py and the 12
# disease configs under app/config/lcd/)
# ---------------------------------------------------------------------

@router.post(
    "/lcd-evaluate",
    status_code=status.HTTP_200_OK,
)
def evaluate_lcd(
    payload: LCDEvaluateRequest,
    db: Session = Depends(get_db),
):
    """Evaluate the selected hospice LCD against the supplied patient and evidence facts."""
    del db
    patient_data = dict(payload.patient or {})
    patient_data["facts"] = dict(payload.facts or {})
    for key, value in (payload.facts or {}).items():
        if key not in patient_data:
            patient_data[key] = value

    patient_obj = SimpleNamespace(**patient_data)
    admission_date = payload.admission_date or datetime.utcnow().date().isoformat()

    return evaluate_hospice_eligibility(patient_obj, admission_date)


@router.get(
    "/lcd-config/detect",
    response_model=LCDDetectResponse,
    status_code=status.HTTP_200_OK,
)
def detect_lcd_rule(
    text: str,
    db: Session = Depends(get_db),
):
    del db
    config = detect_lcd_config(text, load_lcd_configs())
    if not config:
        raise HTTPException(status_code=404, detail="No LCD config found")

    return {
        "disease": config["disease"],
        "lcd_reference": config["lcd_reference"],
        "source_document": config["source_document"],
    }


@router.get(
    "/lcd-config/{disease}",
    status_code=status.HTTP_200_OK,
)
def get_lcd_rule_config(
    disease: str,
    db: Session = Depends(get_db),
):
    del db
    config = get_lcd_config_for_disease(disease, load_lcd_configs())
    if not config:
        raise HTTPException(status_code=404, detail=f"LCD config not found: {disease}")
    return config
