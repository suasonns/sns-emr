import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.domain.rare.service import certify_and_lock_report, ReportNotFound, ReportLocked
from app.security.deps import get_current_user_id  # implement or adapt

router = APIRouter(prefix="/regulatory-reports", tags=["Regulatory Reports"])

@router.post("/{report_id}/certify", status_code=200)
def certify_report(report_id: uuid.UUID,
                   db: Session = Depends(get_db),
                   user_id: uuid.UUID = Depends(get_current_user_id)):
    try:
        report = certify_and_lock_report(db, report_id, user_id)
        return {
            "report_id": str(report.id),
            "status": report.status,
            "certified_at": report.certified_at.isoformat() if report.certified_at else None,
            "certified_by": str(report.certified_by) if report.certified_by else None,
            "integrity_hash": report.integrity_hash,
        }
    except ReportNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ReportLocked as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        # Keep error message safe; log internal exception in your logger
        raise HTTPException(status_code=500, detail="Unable to certify report")