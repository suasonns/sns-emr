# app/models/drug_alias.py
from sqlalchemy import Column, String, DateTime, text
from app.models.base import BaseModel

class DrugAlias(BaseModel):
    __tablename__ = "drug_aliases"

    alias_text = Column(String(255), primary_key=True, index=True)
    canonical_text = Column(String(255), nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )