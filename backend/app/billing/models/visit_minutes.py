from sqlalchemy import Column, String, Integer
from app.db.base import Base


class VisitMinutes(Base):
    __tablename__ = "visit_minutes"

    id = Column(String, primary_key=True)
    visit_id = Column(String, nullable=False)

    discipline = Column(String, nullable=False)

    minutes = Column(Integer, nullable=False)
    units = Column(Integer, nullable=False)