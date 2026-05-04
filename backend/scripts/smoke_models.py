"""
Smoke test: verify ORM models import and SQLAlchemy mappers configure cleanly.
Safe to run anytime. No DB writes.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy.orm import configure_mappers
from app import models  # loads app/models/__init__.py  # noqa: F401

configure_mappers()

import app
print("OK: models import and mappers configured successfully")
print("app loaded from:", app.__file__)
