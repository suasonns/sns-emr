from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from app.models.base import BaseModel
from datetime import datetime


class ClinicalNote(BaseModel):
    __tablename__ = "clinical_notes"

    visit_id = Column(
        ForeignKey("visits.id"),
        nullable=False,
    )

    author_id = Column(
        ForeignKey("users.id"),
        nullable=False,
    )

    note_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String, default="draft")
    finalized_at = Column(DateTime, nullable=True)

    def finalize(self):
        if self.status == "finalized":
            raise ValueError("Clinical notes cannot be modified once finalized")

        self.status = "finalized"
        self.finalized_at = datetime.utcnow()