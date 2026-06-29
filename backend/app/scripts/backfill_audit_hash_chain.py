from app.db.session import SessionLocal
from app.models.med_reconciliation_audit_log import MedReconciliationAuditLog
from app.services.med_reconciliation_audit_service import _compute_signature_hash

def run_backfill():
    db = SessionLocal()

    try:
        patients = (
            db.query(MedReconciliationAuditLog.patient_id)
            .distinct()
            .all()
        )

        for (patient_id,) in patients:
            print(f"Processing patient: {patient_id}")

            rows = (
                db.query(MedReconciliationAuditLog)
                .filter(MedReconciliationAuditLog.patient_id == patient_id)
                .order_by(MedReconciliationAuditLog.created_at.asc(), MedReconciliationAuditLog.id.asc())
                .all()
            )

            prev_hash = None

            for row in rows:
                signature_hash = _compute_signature_hash(
                    tenant_id=row.tenant_id,
                    patient_id=row.patient_id,
                    import_id=row.import_id,
                    item_id=row.item_id,
                    stage=row.stage,
                    event_type=row.event_type,
                    med_name_raw=row.med_name_raw,
                    input_payload=row.input_payload,
                    normalized_payload=row.normalized_payload,
                    comparison_payload=row.comparison_payload,
                    decision_payload=row.decision_payload,
                    created_by=row.created_by,
                    created_at=row.created_at,
                    prev_signature_hash=prev_hash,
                )

                row.prev_signature_hash = prev_hash
                row.signature_hash = signature_hash

                prev_hash = signature_hash

            db.commit()

        print("✅ Backfill complete")

    finally:
        db.close()


if __name__ == "__main__":
    run_backfill()