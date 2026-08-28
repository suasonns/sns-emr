"""Phase A durability: periodic background sweep that re-drives any
document stuck in PENDING/PROCESSING/FAILED, so structured-finding
generation and RNICA population eventually complete even if the initial
BackgroundTasks run never happened or failed (server restart, transient
AI-service outage, etc). See recovery_service.py for the recovery logic
itself -- this module only owns the "run it periodically, forever,
without ever crashing the app" scheduling loop, mirroring
task_scheduler.overdue_scheduler.
"""

from __future__ import annotations

import asyncio
import logging

from app.db.session import SessionLocal
from app.services.evidence.recovery_service import recover_documents

logger = logging.getLogger("sns_emr")

# Deliberately more frequent than a nightly job -- a hospice RN
# reconnecting mid-afternoon should not have to wait until a nightly
# batch for their morning visits' documents to finish processing.
INTERVAL_SECONDS = 300


async def document_recovery_scheduler():
    """Background loop: sweep for recoverable documents across all
    tenants every INTERVAL_SECONDS. Never raises -- any failure is caught,
    logged, and the loop continues on the next interval.
    """

    while True:
        db = None
        try:
            db = SessionLocal()
            result = recover_documents(db)
            if result["examined"]:
                logger.info(
                    "[DOC_RECOVERY_SCHEDULER] examined=%s recovered=%s still_failed=%s",
                    result["examined"],
                    len(result["recovered"]),
                    len(result["still_failed"]),
                )
        except Exception:
            logger.exception("Document recovery scheduler failure")
        finally:
            if db is not None:
                db.close()

        await asyncio.sleep(INTERVAL_SECONDS)
