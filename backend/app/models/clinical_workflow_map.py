from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.db.base import Base


class ClinicalWorkflowMap(Base):
    __tablename__ = "clinical_workflow_map"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    discipline = Column(String(10), nullable=False)
    assessment_type = Column(String(50), nullable=False)
    visit_type = Column(String(50), nullable=False)
    form_type = Column(String(50), nullable=False)

    min_day = Column(Integer, nullable=True)
    max_day = Column(Integer, nullable=True)

    requires_separate_visit = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
