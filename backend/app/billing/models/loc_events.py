from sqlalchemy import Column, String, Date
from app.db.base import Base


class GIPPeriod(Base):
    __tablename__ = "gip_periods"

    id = Column(String, primary_key=True)
    patient_id = Column(String, nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    reason = Column(String)


class RespitePeriod(Base):
    __tablename__ = "respite_periods"

    id = Column(String, primary_key=True)
    patient_id = Column(String, nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    reason = Column(String)


class ContinuousCareEvent(Base):
    __tablename__ = "continuous_care_events"

    id = Column(String, primary_key=True)
    patient_id = Column(String, nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    reason = Column(String)