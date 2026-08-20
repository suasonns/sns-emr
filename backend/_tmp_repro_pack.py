import uuid
from types import SimpleNamespace

from app.core.database import SessionLocal
from app.services import order_template_service as svc
from app.services import physician_order_service

db = SessionLocal()

TENANT_ID = uuid.UUID("01271980-0000-0000-0000-000005101977")
PATIENT_ID = uuid.UUID("9c9ff4bd-f866-5bf9-aa5b-08e26384a40d")
USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

user = SimpleNamespace(tenant_id=TENANT_ID, user_id=USER_ID, role="RN")

# 1. create a NEW custom (non-system) pack, like the admin UI does
template = svc.create_template(
    db, tenant_id=TENANT_ID, name="Debug Test Pack", description="repro", created_by=USER_ID, is_system=False
)
print("template:", template.id, template.name, template.tenant_id)

# 2. add a MEDICATION item exactly like OrderPackManagement.jsx's itemForm would submit
item = svc.add_template_item(
    db,
    template.id,
    {
        "order_type": "MEDICATION",
        "sub_type": "NEW",
        "order_text": "Morphine Sulfate Oral Concentrate (Roxanol) 20 MG/ML",
        "strength": "20MG/ML",
        "dosage": "0.25 mL",
        "route": "Sublingual",
        "frequency": "Q1-2H PRN",
        "indication": "Pain / air hunger",
        "quantity": "1 bottle",
        "payer": "Medicare Hospice Benefit",
        "vendor": "",
        "administered_by": "Hospice Nurse Only",
        "special_instruction": "",
    },
    created_by=USER_ID,
)
print("item:", item.id, item.order_type, item.order_text)

# 3. import the pack onto the patient, exactly like handleImportPack() does
result = svc.import_template(
    db,
    template_id=template.id,
    patient_id=PATIENT_ID,
    user=user,
    ordered_by_provider_name="Dr. Test MD",
    ordered_by_provider_role="MD",
    source_type="WRITTEN",
    prescriber_authenticated=True,
)
print("import result:", result)

# 4. now query it back exactly like the Orders Hub Tx/Meds/DME/Supplies tab does
orders = physician_order_service.list_orders(
    db, tenant_id=TENANT_ID, patient_id=PATIENT_ID, category_filter="MEDICATION"
)
for o in orders:
    print("ORDER:", o.id, o.order_category, o.status, repr(o.order_text))

# cleanup
db.query(type(item)).filter(type(item).template_id == template.id).delete()
db.delete(template)
for o in orders:
    if o.order_text == item.order_text or "Debug" in (o.order_text or ""):
        pass
db.commit()
print("done")
