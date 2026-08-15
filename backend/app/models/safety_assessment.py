# models/safety_assessment.py

from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.enums import CareSettingEnum, SafetyResponsibilityEnum


class SafetyAssessment(Base):
    __tablename__ = "safety_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    patient_id = Column(UUID(as_uuid=True), nullable=False)

    care_setting = Column(
        Enum(
            CareSettingEnum,
            name="care_setting_enum",
            create_type=False,
        ),
        nullable=False,
    )

    safety_responsibility = Column(
        Enum(
            SafetyResponsibilityEnum,
            name="safety_responsibility_enum",
            create_type=False,
        ),
        nullable=False,
    )

    data_json = Column(JSON, nullable=True)

    completed_at = Column(DateTime(timezone=True))
    signed_at = Column(DateTime(timezone=True))
    signed_by = Column(UUID(as_uuid=True))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )