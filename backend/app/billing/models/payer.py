"""
BILLING VIEW OF PAYER (ENTERPRISE SAFE)

Purpose:
- Provides billing module access to Payer
- DOES NOT define schema
- Prevents duplicate ORM model definitions
- Ensures single source of truth in app.models.payer

RULES:
- DO NOT MODIFY SCHEMA HERE
- DO NOT ADD BUSINESS LOGIC
- RE-EXPORT ONLY
"""

from __future__ import annotations

from app.models.payer import Payer

__all__ = ["Payer"]