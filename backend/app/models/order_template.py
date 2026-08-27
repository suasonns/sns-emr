from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class OrderTemplate(BaseModel):
    """
    Reusable, named order-set ("pack") a clinician can import into a real
    patient chart and edit, instead of retyping the same admission/comfort
    orders every time. Modeled on the "Comfort Pack" / "Standard Admission
    Pack" concept.

    tenant_id is nullable so a template can be a shared "system" starter
    pack (is_system=True, tenant_id=NULL, visible to every tenant, read-only)
    or a tenant-owned custom pack that an agency builds for itself.
    """

    __tablename__ = "order_templates"

    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    is_system = Column(Boolean, nullable=False, server_default="false")

    items = relationship(
        "OrderTemplateItem",
        back_populates="template",
        order_by="OrderTemplateItem.sort_order",
        cascade="all, delete-orphan",
    )


class OrderTemplateItem(BaseModel):
    __tablename__ = "order_template_items"

    template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("order_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # MEDICATION | DME | SUPPLY | LAB | TREATMENT | DIET | OTHER
    order_type = Column(String(32), nullable=False)

    # NEW | REFILL | DC | PRE_ADMIT
    sub_type = Column(String(32), nullable=False, server_default="NEW")

    order_text = Column(Text, nullable=False)

    strength = Column(String(128), nullable=True)
    dosage = Column(String(128), nullable=True)
    route = Column(String(64), nullable=True)
    frequency = Column(String(128), nullable=True)
    indication = Column(String(255), nullable=True)
    quantity = Column(String(64), nullable=True)

    payer = Column(String(64), nullable=True)
    vendor = Column(String(128), nullable=True)
    administered_by = Column(String(64), nullable=True)
    special_instruction = Column(Text, nullable=True)

    start_date = Column(Date, nullable=True)
    stop_date = Column(Date, nullable=True)

    sort_order = Column(Integer, nullable=False, server_default="0")

    template = relationship("OrderTemplate", back_populates="items")
