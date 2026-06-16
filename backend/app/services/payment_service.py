from app.models.payment import Payment
from app.db.session import db

def post_payments_from_835(tenant_id, parsed_data):
    created = []

    for item in parsed_data:
        payment = Payment(
            tenant_id=tenant_id,
            claim_control_number=item["claim_control_number"],
            total_charge=item["total_charge"],
            total_paid=item["paid_amount"],
            payment_date=item.get("payment_date"),
            is_denied=item["paid_amount"] == 0
        )

        db.add(payment)
        created.append(payment)

    db.commit()

    return created
