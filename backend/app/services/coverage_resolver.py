from __future__ import annotations


class CoverageResolverError(Exception):
    """Raised when coverage resolution fails"""
    pass


def resolve_claim_route(patient: dict | None = None) -> dict:
    """
    ✅ ENTERPRISE-SAFE BASE COVERAGE RESOLVER

    Purpose:
    - Determines where claim goes (Medicare / Commercial / Self Pay)
    - Future: COB (coordination of benefits)
    - Future: eligibility validation

    Current:
    - Safe default behavior (Medicare-first hospice system)
    """

    if not patient:
        raise CoverageResolverError("Missing patient data for coverage resolver")

    # ✅ MINIMAL SAFE LOGIC (DO NOT OVERENGINEER YET)
    return {
        "route": "PRIMARY",
        "payer_type": "MEDICARE",
        "priority": 1,
        "notes": "Default Medicare hospice routing applied",
    }