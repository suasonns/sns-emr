from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.task_overdue_engine import run_overdue_engine


logger = logging.getLogger("sns_emr")

INTERVAL_SECONDS = 60


async def overdue_scheduler():
    """
    Background overdue scheduler.

    Production-safe behavior:
    - Multi-tenant aware
    - Uses standalone DB session (no request scope)
    - Safe commit/rollback cycle
    - Resilient to failure (never crashes)
    """

    while True:
        db: Session | None = None

        try:
            db = SessionLocal()

            tenant_rows = db.execute(
                text(
                    """
                    SELECT DISTINCT tenant_id
                    FROM tasks
                    WHERE tenant_id IS NOT NULL
                    """
                )
            ).fetchall()

            updated_total = 0

            for row in tenant_rows:
                tenant_id = UUID(str(row[0]))

                updated = run_overdue_engine(
                    db=db,
                    tenant_id=tenant_id,
                )

                if updated > 0:
                    logger.info(
                        "[SCHEDULER] tenant=%s updated=%s",
                        tenant_id,
                        updated,
                    )
                    updated_total += updated

            if updated_total > 0:
                db.commit()
            else:
                db.rollback()

        except Exception:
            if db is not None:
                db.rollback()

            logger.exception("Overdue scheduler failure")

        finally:
            if db is not None:
                db.close()

        await asyncio.sleep(INTERVAL_SECONDS)