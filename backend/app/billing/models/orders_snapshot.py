from sqlalchemy import Column, String, Integer, Date
from app.db.base import Base


class OrdersSnapshot(Base):
    __tablename__ = "orders_snapshot"

    id = Column(String, primary_key=True)
    patient_id = Column(String, nullable=False)

    discipline = Column(String, nullable=False)
    visits_per_week = Column(Integer, nullable=False)

    effective_date = Column(Date, nullable=False)
    end_date = Column(Date)
