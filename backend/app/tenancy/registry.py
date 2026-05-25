import os
from typing import Set

from dotenv import load_dotenv

# ---------------------------------------------------------
# Ensure local env is available for CLI/tests
# ---------------------------------------------------------
load_dotenv(".env.local")
load_dotenv()


def _env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Missing required env var: {name}")
    return val


# ---------------------------------------------------------
# CANONICAL TENANT REGISTRY (DO NOT GUESS, DO NOT GENERATE)
# ---------------------------------------------------------

TENANT_REAL = _env("DEV_TENANT_REAL_ID")  # LOVE AND FAITH HOSPICE SERVICES INC.

TENANT_TRAINING_A = _env("DEV_TENANT_DUMMY_A")  # Angela Hospice
TENANT_TRAINING_B = _env("DEV_TENANT_DUMMY_B")  # Silva Hospice

TENANT_LEGACY_A = _env("DEV_TENANT_A_ID")  # Temporary legacy
TENANT_LEGACY_B = _env("DEV_TENANT_B_ID")  # Temporary legacy


ALL_KNOWN_TENANTS: Set[str] = {
    TENANT_REAL,
    TENANT_TRAINING_A,
    TENANT_TRAINING_B,
    TENANT_LEGACY_A,
    TENANT_LEGACY_B,
}


# ---------------------------------------------------------
# TENANT CLASSIFICATION
# ---------------------------------------------------------

PROTECTED_TENANTS: Set[str] = {
    TENANT_REAL,
    TENANT_TRAINING_A,
    TENANT_TRAINING_B,
}

TRAINING_TENANTS: Set[str] = {
    TENANT_TRAINING_A,
    TENANT_TRAINING_B,
}

LEGACY_TENANTS: Set[str] = {
    TENANT_LEGACY_A,
    TENANT_LEGACY_B,
}


# ---------------------------------------------------------
# ASSERTIONS (HARD GUARDS)
# ---------------------------------------------------------

def assert_known_tenant(tenant_id: str) -> None:
    """
    Hard guard: reject any tenant not explicitly registered.
    """
    if tenant_id not in ALL_KNOWN_TENANTS:
        raise ValueError(f"Unknown tenant_id: {tenant_id}")


def assert_protected_tenant(tenant_id: str) -> None:
    """
    Guard for tenants that must never be deleted or modified destructively.
    """
    if tenant_id not in PROTECTED_TENANTS:
        raise ValueError("Tenant is not protected")


def assert_training_or_legacy_tenant(tenant_id: str) -> None:
    """
    Guard for tenants where patient data may be reset (training + legacy only).
    """
    allowed = TRAINING_TENANTS | LEGACY_TENANTS
    if tenant_id not in allowed:
        raise ValueError("Tenant is not training or legacy")