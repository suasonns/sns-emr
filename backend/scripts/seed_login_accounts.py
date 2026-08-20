"""Provision environment-configured development login identities."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env.local", override=False)
load_dotenv(override=False)

from app.core.database import SessionLocal  # noqa: E402
from app.services.admin_bootstrap_service import provision_development_logins  # noqa: E402


def main() -> int:
    db = SessionLocal()
    try:
        provisioned = provision_development_logins(db)
        print(f"development identities provisioned: {provisioned}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
