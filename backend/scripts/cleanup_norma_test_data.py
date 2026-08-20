"""One-off cleanup: remove Orders Hub test data created on Norma Suarez during
development/verification of the Orders Hub feature (medications, patient_orders,
fax_logs). Safe to delete this script after running once.
"""
from app.core.database import SessionLocal
from app.models.medication import Medication
from app.models.patient_order import PatientOrder
from app.models.fax_log import FaxLog

PATIENT_ID = "887b7f37-bda3-4b73-aa4f-03171fca35fc"


def main():
    db = SessionLocal()
    try:
        med_count = db.query(Medication).filter(Medication.patient_id == PATIENT_ID).count()
        print(f"Deleting {med_count} medications for patient {PATIENT_ID}")
        db.query(Medication).filter(Medication.patient_id == PATIENT_ID).delete()

        order_count = db.query(PatientOrder).filter(PatientOrder.patient_id == PATIENT_ID).count()
        print(f"Deleting {order_count} patient_orders for patient {PATIENT_ID}")
        db.query(PatientOrder).filter(PatientOrder.patient_id == PATIENT_ID).delete()

        fax_count = db.query(FaxLog).filter(FaxLog.patient_id == PATIENT_ID).count()
        print(f"Deleting {fax_count} fax_logs for patient {PATIENT_ID}")
        db.query(FaxLog).filter(FaxLog.patient_id == PATIENT_ID).delete()

        db.commit()
        print("Cleanup complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
