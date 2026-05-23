from app.core.db import Base

# Import ALL models here so Alembic sees them
from app.models.eligibility_decision import EligibilityDecision  # noqa: F401