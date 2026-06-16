import os
from typing import Set
from dotenv import load_dotenv

load_dotenv(".env.local")
load_dotenv()


def _env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Missing required env var: {name}")
    return val


# ⚠️ DEV / SAFETY GUARDS ONLY
TENANT_REAL = _env("DEV_TENANT_REAL_ID")
TENANT_TRAINING_A = _env("DEV_TENANT_DUMMY_A")
TENANT_TRAINING_B = _env("DEV_TENANT_DUMMY_B")
TENANT_LEGACY_A = _env("DEV_TENANT_A_ID")
TENANT_LEGACY_B = _env("DEV_TENANT_B_ID")

ALL_KNOWN_TENANTS: Set[str] = {
    TENANT_REAL,
    TENANT_TRAINING_A,
    TENANT_TRAINING_B,
    TENANT_LEGACY_A,
    TENANT_LEGACY_B,
}

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


def assert_known_tenant_dev(tenant_id: str) -> None:
    """
    DEV safety guard only — NOT the tenant registry.
    """
    if tenant_id not in ALL_KNOWN_TENANTS:
        raise ValueError(f"Unknown tenant_id (dev guard): {tenant_id}")