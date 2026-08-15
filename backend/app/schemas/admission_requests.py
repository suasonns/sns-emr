from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ChangeStatusRequest(BaseModel):
    new_status: str
    reason: Optional[str] = None
    notes: Optional[str] = None


class StartSocRequest(BaseModel):
    soc_datetime: Optional[datetime] = None
    notes: Optional[str] = None


class CompleteAdmissionRequest(BaseModel):
    admit_datetime: Optional[datetime] = None
    notes: Optional[str] = None


class NonAdmitRequest(BaseModel):
    reason: str
    notes: Optional[str] = None