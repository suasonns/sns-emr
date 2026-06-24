from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class CHHAVisitTaskResult(Base):
    __tablename__ = "chha_visit_task_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outcome_id = Column(UUID(as_uuid=True), ForeignKey("chha_visit_outcomes.id"), nullable=False, index=True)

    # Mirrors your sections in the UI
    section_code = Column(String(100), nullable=False, index=True)
    task_code = Column(String(100), nullable=False, index=True)

    # Assigned/completed state
    was_assigned = Column(Boolean, nullable=False, default=True)
    completed = Column(Boolean, nullable=False, default=False)
    refused = Column(Boolean, nullable=False, default=False)
    not_done = Column(Boolean, nullable=False, default=False)

    # Optional detail
    observation_code = Column(String(100), nullable=True)
    result_note = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    outcome = relationship("CHHAVisitOutcome", back_populates="task_results")