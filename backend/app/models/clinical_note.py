from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
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

    # Draft / finalized indicator (secondary)
    status = Column(String, default="draft")

    # ✅ Authoritative finalization boundary
    finalized_at = Column(DateTime, nullable=True)
    finalized_by = Column(UUID(as_uuid=True), nullable=True)

    def finalize(self, *, finalized_by):
        """
        Finalize the clinical note.
        This is a one-way operation.
        """
        # ✅ Authoritative guard (timestamp-based, survey-defensible)
        if self.finalized_at is not None:
            raise ValueError("Clinical note already finalized")

        self.status = "finalized"
        self.finalized_at = datetime.utcnow()
        self.finalized_by = finalized_by
