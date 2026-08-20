# scripts/seed_order_templates.py
"""
One-off seed script: creates the two starter system order templates
("Comfort Pack" and "Standard Admission Pack") as tenant_id=NULL /
is_system=True rows, importable by any tenant.

Run with: .\\.venv\\Scripts\\python.exe scripts\\seed_order_templates.py
"""

from app.core.database import SessionLocal
from app.models.order_template import OrderTemplate, OrderTemplateItem

COMFORT_PACK_ITEMS = [
    dict(
        order_type="MEDICATION", order_text="Acetaminophen 650mg Rectal Suppository",
        strength="650mg", dosage="650mg", route="Rectal", frequency="Every 4 hours PRN",
        indication="Fever and mild pain",
        special_instruction="Not to exceed 3g/24h from all sources (APAP, Norco, etc.)",
    ),
    dict(
        order_type="MEDICATION", order_text="Atropine Care 1%",
        strength="1%", dosage="4 drops", route="Sublingual", frequency="Every 6 hours PRN",
        indication="Excessive secretions",
        special_instruction="Not to exceed 4 doses in 24 hours",
    ),
    dict(
        order_type="MEDICATION", order_text="Bisacodyl 10mg Rectal Suppository",
        strength="10mg", dosage="10mg", route="Rectal", frequency="Once daily PRN",
        indication="Constipation",
        special_instruction="Not to exceed 1 dose in 24 hours",
    ),
    dict(
        order_type="MEDICATION", order_text="Duoneb 3mg-0.5mg/3mL Solution for Inhalation",
        strength="3mg-0.5mg/3mL", dosage="1 vial", route="Respiratory (Inhalation)", frequency="Every 4 hours PRN",
        indication="SOB/Wheezes",
        special_instruction="Not to exceed 6 doses every 24 hours",
    ),
    dict(
        order_type="MEDICATION", order_text="Lorazepam 2mg/mL Concentrate Solution",
        strength="2mg/mL", dosage="1mg (0.5 mL SL)", route="Sublingual", frequency="Every 4 hours PRN",
        indication="Anxiety/agitation",
        special_instruction="Not to exceed 2mg or 4 doses every 24 hours. Standard hospice comfort-kit combination with Morphine Sulfate for EOL symptom management — not flagged as an interaction in this system.",
    ),
    dict(
        order_type="MEDICATION", order_text="Morphine Sulfate 100mg/5mL Solution",
        strength="100mg/5mL", dosage="Titrated per pain/SOB severity", route="Sublingual",
        frequency="Every 4 hours PRN (titratable)",
        indication="Pain/SOB",
        special_instruction=(
            "Not to exceed 100mg or 5mL/24h. Titration: mild/moderate pain (4-6) = 0.5 mL q4h PRN; "
            "severe pain (7-10)/uncontrolled = 0.75 mL q2h PRN; uncontrolled pain/severe SOB = 1 mL (20mg) "
            "q1h PRN (max once/hour)."
        ),
    ),
    dict(
        order_type="MEDICATION", order_text="Zofran ODT 4mg Orally Disintegrating Tablet",
        strength="4mg", dosage="1 tab", route="Sublingual", frequency="Every 8 hours PRN",
        indication="Nausea and vomiting",
        special_instruction="Not to exceed 3 doses in 24 hours",
    ),
]

ADMISSION_PACK_ITEMS = [
    dict(
        order_type="MEDICATION", order_text="Oxygen inhalation", dosage="2-5 LPM",
        route="Respiratory (Inhalation)", frequency="PRN to maintain SpO2 >90% (see special instructions)",
        indication="Maintain O2 sat >90%", quantity="1",
        special_instruction=(
            "May initiate supplemental oxygen at 2-5 lpm via mask or nasal cannula for comfort and symptom "
            "management. 90-92% on room air = 2L, 87-89% on room air = 3L, 84-86% on room air = 4L, "
            "80-83% on room air = 5L."
        ),
    ),
    # DME
    *[dict(order_type="DME", order_text=t) for t in [
        '18" Standard Wheelchair with Footrests',
        "5L Oxygen Concentrator with nasal cannula/mask, 25 feet tube extension",
        "Front Wheel Walker",
        "Hospital Bed Full Electric with (Full Rail)",
        "Over Bed Table",
        "Oxygen E Tank with cart with Oxygen Regulator High Flow 15L",
        "Small Volume Nebulizer Compressor",
        "Suction Machine with fr14 suction catheter",
    ]],
    # Supplies
    dict(order_type="SUPPLY", order_text="A&D Ointment to promote skin healing and prevention of skin breakdown"),
    dict(
        order_type="SUPPLY", order_text="Calmoseptine - Apply to bony prominent area/skin folds",
        special_instruction="May apply Calmoseptine or skin barrier on sacrum area as needed for signs of redness.",
    ),
    dict(order_type="SUPPLY", order_text="Gloves Medium/Large"),
    dict(order_type="SUPPLY", order_text="No Rinse Body Wash"),
    dict(order_type="SUPPLY", order_text="Perineal Wash"),
    dict(order_type="SUPPLY", order_text="Under pads washable and disposable"),
    dict(order_type="SUPPLY", order_text="Wipes"),
    # Other (boilerplate admission orders, editable fill-ins left as ___)
    *[dict(order_type="OTHER", order_text=t) for t in [
        "Activity Status: Bed/Chair Fast, maximum assist with transfers, ambulatory ad lib with use of assistive devices as needed.",
        "Admit patient under Dx of ___; Routine Level of Care for benefit period #___, from ___ to ___.",
        "Allergies: ___",
        "Bereavement Coordinator to assess and evaluate bereavement and grieving risk factors within 5 days of SOC and for post death assessment.",
        "Code Status: ___",
        "Diet: ___",
        "Family/PCG to call agency at ___ for any change of condition, new orders, and other concerns.",
        "Generic equivalents may be used, unless otherwise specified. May crush oral tablet medications if needed (except Extended Release, Slow Release, Enteric Coated medications).",
        "Notify medical director (or designee) if oxygen saturation is less than 88%.",
        "Send Hospice Aide ___ x/week for personal care and support per HA assignment as instructed by the RN supervisor.",
        "Send Medical Social Worker for Psycho-social evaluation within 5 days of admission, for initial assessment.",
        "Send Spiritual Counselor for spiritual needs evaluation within 5 days of admission.",
        "Skilled nursing frequency ___ x/week for assessment, monitoring, medication reviews and administration, and updates in POC and 3 PRNs for uncontrolled pain, uncontrolled anxiety, increased SOB and any sudden change of condition starting from the start of care.",
        "SN may obtain patient's vital signs, height and weight, and complete full physical assessment as needed.",
        "SN to check oxygen saturation via pulse-oximeter every visit and as needed for SOB, congestion and/or wheezing; monitor oxygen saturation to maintain saturation level greater than 90%.",
        "Volunteer services declined by patient/family.",
    ]],
]


def _seed(db, name: str, description: str, items: list[dict]) -> None:
    existing = db.query(OrderTemplate).filter(OrderTemplate.name == name, OrderTemplate.is_system.is_(True)).first()
    if existing:
        print(f"Skipping '{name}' — already seeded ({len(existing.items)} items).")
        return

    template = OrderTemplate(tenant_id=None, name=name, description=description, is_system=True)
    db.add(template)
    db.flush()

    for i, item in enumerate(items):
        db.add(OrderTemplateItem(template_id=template.id, sub_type=item.pop("sub_type", "NEW"), sort_order=i, **item))

    db.commit()
    print(f"Seeded '{name}' with {len(items)} items.")


def main():
    db = SessionLocal()
    try:
        _seed(
            db,
            "Comfort Pack",
            "Standard hospice comfort-kit PRN medication set for end-of-life symptom management "
            "(pain, dyspnea, anxiety, secretions, constipation, nausea).",
            COMFORT_PACK_ITEMS,
        )
        _seed(
            db,
            "Standard Admission Pack",
            "Full standard admission order set applied to every new hospice patient: oxygen, DME, "
            "supplies, and boilerplate admission/consent orders.",
            ADMISSION_PACK_ITEMS,
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
