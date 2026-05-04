from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.idg_note import IDGNote
from app.models.idg_md_attestation import IDGMDAttestation

REQUIRED_NOTE_DISCIPLINES = {"RN", "MSW", "SC"}

DISCIPLINE_ALIAS = {
    "SW": "MSW",
    "SOCIAL_WORKER": "MSW",
    "CHAPLAIN": "SC",
    "SPIRITUAL": "SC",
}

def normalize_discipline(d: str) -> str:
    if not d:
        return d
    d = d.strip().upper()
    return DISCIPLINE_ALIAS.get(d, d)


def validate_idg_ready_to_complete(db: Session, idg_id):
    # 1) Required discipline notes must exist & be signed
    notes = db.query(IDGNote).filter(IDGNote.idg_id == idg_id).all()

    signed_disciplines = {
        normalize_discipline(n.discipline)
        for n in notes
        if n.signed_at is not None
    }

    missing = REQUIRED_NOTE_DISCIPLINES - signed_disciplines
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"IDG cannot be completed. Missing signed notes from: {sorted(missing)}",
        )

    # 2) MD attestation must exist (and ideally be signed if you track signed_at)
    md_att = db.query(IDGMDAttestation).filter(IDGMDAttestation.idg_id == idg_id).first()
    if not md_att:
        raise HTTPException(
            status_code=400,
            detail="IDG cannot be completed. Missing MD attestation.",
        )

    # Optional: if attestation has signed_at, enforce it:
    if hasattr(md_att, "signed_at") and md_att.signed_at is None:
        raise HTTPException(
            status_code=400,
            detail="IDG cannot be completed. MD attestation not signed.",
        )

    return notes