from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.idg_review import IDGReview
from app.models.idg_md_attestation import IDGMDAttestation
from app.models.idg_note import IDGNote
from app.models.idg_meeting import IDGMeeting


# =========================================================
# CONFIG
# =========================================================

IDG_LOOKBACK_DAYS = 15

REQUIRED_DISCIPLINES = {"RN", "MSW", "SC"}


# =========================================================
# IDG COMPLIANCE SUMMARY
# =========================================================

def get_idg_compliance_summary(db: Session, tenant_id):

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=IDG_LOOKBACK_DAYS)

    patients = (
        db.query(Patient)
        .filter(
            Patient.tenant_id == tenant_id,
            Patient.status == "active",
        )
        .all()
    )

    results = []

    for patient in patients:

        review = (
            db.query(IDGReview)
            .filter(
                IDGReview.patient_id == patient.id,
                IDGReview.tenant_id == tenant_id,
            )
            .order_by(IDGReview.review_date.desc())
            .first()
        )

        compliant = False
        reason = "NO_REVIEW"

        if review:

            if not review.is_finalized:
                reason = "NOT_FINALIZED"

            elif not review.plan_of_care_version_id:
                reason = "NO_POC_LINK"

            else:
                # ✅ MD ATTESTATION
                md_signed = (
                    db.query(IDGMDAttestation.id)
                    .filter(
                        IDGMDAttestation.idg_review_id == review.id,
                        IDGMDAttestation.is_signed == True,
                    )
                    .first()
                )

                if not md_signed:
                    reason = "NO_MD_ATTESTATION"

                else:
                    # ✅ DISCIPLINES
                    notes = (
                        db.query(IDGNote.discipline)
                        .filter(IDGNote.idg_review_id == review.id)
                        .all()
                    )

                    disciplines_present = {
                        (d[0] or "").upper() for d in notes if d[0]
                    }

                    missing = REQUIRED_DISCIPLINES - disciplines_present

                    if missing:
                        reason = f"MISSING_DISCIPLINES:{sorted(list(missing))}"

                    elif review.review_date < cutoff:
                        reason = "OUTDATED"

                    else:
                        compliant = True
                        reason = "COMPLIANT"

        results.append(
            {
                "patient_id": str(patient.id),
                "last_idg_review_date": review.review_date if review else None,
                "compliant": compliant,
                "reason": reason,
            }
        )

    return results


# =========================================================
# MISSED IDG DETECTION
# =========================================================

def get_missed_idg_meetings(
    db: Session,
    *,
    tenant_id,
) -> List[IDGMeeting]:

    now = datetime.now(timezone.utc)

    meetings = (
        db.query(IDGMeeting)
        .filter(
            IDGMeeting.tenant_id == tenant_id,
            IDGMeeting.meeting_date < now,
        )
        .all()
    )

    missed = []

    for meeting in meetings:
        review_exists = (
            db.query(IDGReview.id)
            .filter(
                IDGReview.idg_meeting_id == meeting.id,
                IDGReview.is_finalized == True,
            )
            .first()
        )

        if not review_exists:
            missed.append(meeting)

    return missed


# =========================================================
# PATIENT-LEVEL MISSED IDG
# =========================================================

def get_patient_missed_idg(
    db: Session,
    *,
    tenant_id,
    patient_id,
):

    now = datetime.now(timezone.utc)

    meetings = (
        db.query(IDGMeeting)
        .filter(
            IDGMeeting.tenant_id == tenant_id,
            IDGMeeting.patient_id == patient_id,
            IDGMeeting.meeting_date < now,
        )
        .all()
    )

    missed = []

    for meeting in meetings:
        review_exists = (
            db.query(IDGReview.id)
            .filter(
                IDGReview.idg_meeting_id == meeting.id,
                IDGReview.is_finalized == True,
            )
            .first()
        )

        if not review_exists:
            missed.append(meeting)

    return missed