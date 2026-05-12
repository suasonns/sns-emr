from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/internal/superuser", tags=["SuperUser"])


def require_super_user(current_user):
    role = current_user.get("role") if isinstance(current_user, dict) else getattr(current_user, "role", None)
    if role != "SUPER_USER":
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/trust-view")
def trust_view(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Per-person compliance & risk summary (SUPER USER ONLY).
    """
    require_super_user(current_user)

    since = datetime.now(timezone.utc) - timedelta(days=days)

    # ------------------------------------------------------------
    # 1) NOE audit summary per user
    # ------------------------------------------------------------
    noe = db.execute(
        text("""
            SELECT
              attempted_by_user_id AS user_id,
              COUNT(*) FILTER (WHERE result = 'BLOCKED') AS noe_blocked,
              COUNT(*) FILTER (WHERE result = 'GENERATED') AS noe_generated
            FROM noe_audit_events
            WHERE attempted_at >= :since
            GROUP BY attempted_by_user_id
        """),
        {"since": since},
    ).mappings().all()

    # ------------------------------------------------------------
    # 2) Reauth usage per user
    # ------------------------------------------------------------
    reauth = db.execute(
        text("""
            SELECT
              user_id,
              COUNT(*) AS reauth_issued,
              COUNT(*) FILTER (WHERE used_at IS NOT NULL) AS reauth_used
            FROM reauth_sessions
            WHERE issued_at >= :since
            GROUP BY user_id
        """),
        {"since": since},
    ).mappings().all()

    # ------------------------------------------------------------
    # 3) Bulk activity per user (JOIN users for names)
    # ------------------------------------------------------------
    bulk = db.execute(
        text("""
            SELECT
              u.id AS user_id,
              u.email,
              u.full_name,
              u.role,
              COUNT(*) FILTER (WHERE sae.event_type = 'BULK_EXPORT_ATTEMPT') AS bulk_attempts,
              COUNT(*) FILTER (WHERE sae.event_type = 'BULK_EXPORT_ALLOWED') AS bulk_allowed
            FROM security_activity_events sae
            LEFT JOIN users u
              ON u.id = sae.user_id
            WHERE sae.event_at >= :since
            GROUP BY u.id, u.email, u.full_name, u.role
        """),
        {"since": since},
    ).mappings().all()

    # ------------------------------------------------------------
    # Merge results by user_id
    # ------------------------------------------------------------
    def index(rows):
        out = {}
        for r in rows:
            key = str(r["user_id"]) if r["user_id"] is not None else "None"
            out[key] = dict(r)
        return out

    noe_i = index(noe)
    reauth_i = index(reauth)
    bulk_i = index(bulk)

    user_ids = set(noe_i.keys()) | set(reauth_i.keys()) | set(bulk_i.keys())

    summary = []
    for uid in user_ids:
        b = bulk_i.get(uid, {})

        summary.append({
            "user_id": None if uid == "None" else uid,
            "email": b.get("email"),
            "full_name": b.get("full_name"),
            "role": b.get("role"),

            "noe_blocked": noe_i.get(uid, {}).get("noe_blocked", 0),
            "noe_generated": noe_i.get(uid, {}).get("noe_generated", 0),

            "reauth_issued": reauth_i.get(uid, {}).get("reauth_issued", 0),
            "reauth_used": reauth_i.get(uid, {}).get("reauth_used", 0),

            "bulk_attempts": b.get("bulk_attempts", 0),
            "bulk_allowed": b.get("bulk_allowed", 0),
        })

    # Highest risk first
    summary.sort(
        key=lambda x: (x["noe_blocked"], x["bulk_attempts"]),
        reverse=True,
    )

    return {
        "window_days": days,
        "since": since.isoformat(),
        "trust_view": summary,
    }


@router.get("/security-activity")
def security_activity(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    require_super_user(current_user)

    since = datetime.now(timezone.utc) - timedelta(days=days)

    rows = db.execute(
        text("""
            SELECT
              sae.event_at,
              sae.event_type,
              sae.scope,
              sae.result,
              sae.patient_count,
              sae.document_count,
              u.id AS user_id,
              u.email,
              u.full_name,
              u.role
            FROM security_activity_events sae
            LEFT JOIN users u
              ON u.id = sae.user_id
            WHERE sae.event_at >= :since
            ORDER BY sae.event_at DESC
            LIMIT 500
        """),
        {"since": since},
    ).mappings().all()

    return [dict(r) for r in rows]