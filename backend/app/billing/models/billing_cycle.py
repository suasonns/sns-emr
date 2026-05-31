from sqlalchemy import Column, String, Integer, Date
from app.db.base import Base


class BillingCycle(Base):
    __tablename__ = "billing_cycles"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)

    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
