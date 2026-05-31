from sqlalchemy import Column, String
from app.db.base import Base


class AuthorizationRecord(Base):
    __tablename__ = "authorization_records"

    id = Column(String, primary_key=True)
    patient_id = Column(String, nullable=False)

    payer_name = Column(String, nullable=False)
    auth_status = Column(String, nullable=False)