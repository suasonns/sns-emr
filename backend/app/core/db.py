"""
Enterprise DB facade (stable import layer).
"""

from typing import Generator
from sqlalchemy.orm import Session

from app.core.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    ✅ ENTERPRISE SAFE DB SESSION

    Guarantees:
    - per-request isolated session
    - safe rollback on failure
    - connection properly returned to pool
    - no session contamination
    """

    db: Session = SessionLocal()

    try:
        # ✅ provide session to request
        yield db

        # ✅ OPTIONAL (controlled commit pattern)
        # If you want auto-commit per request, enable below:
        # db.commit()

    except Exception:
        # ✅ rollback ONLY IF FAILURE
        try:
            db.rollback()
        except Exception:
            pass
        raise

    finally:
        # ✅ ensure connection cleanup
        try:
            db.close()
        except Exception:
            pass