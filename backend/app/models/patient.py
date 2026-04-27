from sqlalchemy import Column, String, Date
from app.models.base import BaseModel


class Patient(BaseModel):
    __tablename__ = "patients"

    mrn = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    primary_diagnosis = Column(String, nullable=False)
    status = Column(String, nullable=False)