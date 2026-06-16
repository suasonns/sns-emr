"""
BILLING VIEW OF PATIENT PAYERS (ENTERPRISE SAFE)

IMPORTANT:
- Billing MUST NOT define patient_payers schema
- Canonical ORM model lives in app.models.patient_payer
- This file exists ONLY for import compatibility
"""

from __future__ import annotations

from app.models.patient_payer import PatientPayer  # noqa: F401
