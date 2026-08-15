import os


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("true", "1", "yes", "on")


class Settings:
    # =========================================
    # SYSTEM MODES
    # =========================================

    RULE_ENFORCEMENT_MODE: str = os.getenv(
        "RULE_ENFORCEMENT_MODE", "EVALUATE_ONLY"
    ).strip().upper()

    # =========================================
    # EXISTING FLAGS (DO NOT BREAK)
    # =========================================

    ALLOW_DEV_DASHBOARD_BYPASS: bool = _bool(
        os.getenv("ALLOW_DEV_DASHBOARD_BYPASS"), False
    )

    ALLOW_RULE_ENFORCEMENT: bool = _bool(
        os.getenv("ALLOW_RULE_ENFORCEMENT"), False
    )

    # =========================================
    # NEW MASTER CONTROL LAYER
    # =========================================

    ENABLE_STRICT_VALIDATION: bool = _bool(
        os.getenv("ENABLE_STRICT_VALIDATION"), False
    )

    ENABLE_COMPLIANCE_RULES: bool = _bool(
        os.getenv("ENABLE_COMPLIANCE_RULES"), False
    )

    ENABLE_AUDIT_TRAIL: bool = _bool(
        os.getenv("ENABLE_AUDIT_TRAIL"), False
    )

    ENABLE_IMMUTABILITY: bool = _bool(
        os.getenv("ENABLE_IMMUTABILITY"), False
    )

    # =========================================
    # DATA CONTROL (CRITICAL)
    # =========================================

    ALLOW_DELETION: bool = _bool(
        os.getenv("ALLOW_DELETION"), True
    )

    ALLOW_FULL_RESET: bool = _bool(
        os.getenv("ALLOW_FULL_RESET"), True
    )


settings = Settings()