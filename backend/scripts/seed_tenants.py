"""
Seed the tenant roster.

Ids come from the environment so nothing agency-specific is compiled into the
application. Safe to re-run: existing tenants are updated in place.

    Love & Faith Hospice   PRODUCTION   real agency
    Angela Hospice         TRAINING     permanent training tenant
    Silva Hospice          TRAINING     permanent training tenant
    Dev Tenant A / B       DEV          removed at pre-production cutover

Usage (PowerShell, from backend/):

    python scripts/seed_tenants.py
    python scripts/seed_tenants.py --drop-temporary    # after field testing
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env.local", override=False)
load_dotenv(override=False)

from app.core.database import SessionLocal  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402

# environment_tag marks which rows may be removed at cutover.
PERMANENT = "PERMANENT"
TEMPORARY = "TEMPORARY"

TENANTS = [
    {
        "env_var": "DEV_TENANT_REAL_ID",
        "legal_name": "Love & Faith Hospice Services, Inc.",
        "display_name": "Love & Faith Hospice Services, Inc.",
        "npi": "1275143653",
        "ein": "851033525",
        "ptan": "B51771",
        "tenant_type": "PRODUCTION",
        "environment_tag": PERMANENT,
        "ai_enabled": True,
        "billing_enabled": True,
    },
    {
        "env_var": "DEV_TENANT_DUMMY_A",
        "legal_name": "Angela Hospice",
        "display_name": "Angela Hospice (Training)",
        # npi is required; training agencies get an obviously non-real placeholder.
        "npi": "0000000001",
        "ein": None,
        "ptan": None,
        "tenant_type": "TRAINING",
        "environment_tag": PERMANENT,
        "ai_enabled": True,
        "billing_enabled": False,
    },
    {
        "env_var": "DEV_TENANT_DUMMY_B",
        "legal_name": "Silva Hospice",
        "display_name": "Silva Hospice (Training)",
        "npi": "0000000002",
        "ein": None,
        "ptan": None,
        "tenant_type": "TRAINING",
        "environment_tag": PERMANENT,
        "ai_enabled": True,
        "billing_enabled": False,
    },
    {
        "env_var": "DEV_TENANT_A_ID",
        "legal_name": "Dev Tenant A",
        "display_name": "Dev Tenant A",
        "npi": "0000000003",
        "ein": None,
        "ptan": None,
        "tenant_type": "DEV",
        "environment_tag": TEMPORARY,
        "ai_enabled": True,
        "billing_enabled": False,
    },
    {
        "env_var": "DEV_TENANT_B_ID",
        "legal_name": "Dev Tenant B",
        "display_name": "Dev Tenant B",
        "npi": "0000000004",
        "ein": None,
        "ptan": None,
        "tenant_type": "DEV",
        "environment_tag": TEMPORARY,
        "ai_enabled": True,
        "billing_enabled": False,
    },
]


def seed(db) -> None:
    created = updated = skipped = 0

    for spec in TENANTS:
        raw_id = os.getenv(spec["env_var"])
        if not raw_id:
            print(f"skipped: {spec['legal_name']} ({spec['env_var']} not set)")
            skipped += 1
            continue

        tenant_id = uuid.UUID(raw_id.split()[0])
        tenant = db.get(Tenant, tenant_id)

        if tenant is None:
            tenant = Tenant(id=tenant_id)
            db.add(tenant)
            created += 1
        else:
            updated += 1

        tenant.legal_name = spec["legal_name"]
        tenant.display_name = spec["display_name"]
        tenant.npi = spec["npi"]
        tenant.ein = spec["ein"]
        tenant.ptan = spec["ptan"]
        tenant.tenant_type = spec["tenant_type"]
        tenant.environment_tag = spec["environment_tag"]
        tenant.status = "ACTIVE"
        tenant.ai_enabled = spec["ai_enabled"]
        tenant.billing_enabled = spec["billing_enabled"]

    db.commit()
    print(f"created: {created}, updated: {updated}, skipped: {skipped}")


def drop_temporary(db) -> None:
    rows = db.query(Tenant).filter(Tenant.environment_tag == TEMPORARY).all()

    if not rows:
        print("no temporary tenants to remove")
        return

    for tenant in rows:
        print(f"removing {tenant.legal_name} ({tenant.id})")
        db.delete(tenant)

    db.commit()
    print(f"removed {len(rows)} temporary tenants")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--drop-temporary",
        action="store_true",
        help="Delete tenants tagged TEMPORARY (pre-production cutover).",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.drop_temporary:
            drop_temporary(db)
        else:
            seed(db)

        print()
        for tenant in db.query(Tenant).order_by(Tenant.legal_name).all():
            print(
                f"  {tenant.tenant_type:<11} {str(tenant.environment_tag or '-'):<10} "
                f"{tenant.legal_name}"
            )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
