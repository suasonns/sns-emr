from sqlalchemy import Column, String
from app.db.base import Base


class PayerContract(Base):
    __tablename__ = "payer_contracts"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)

    payer_name = Column(String, nullable=False)
    has_contract = Column(String)