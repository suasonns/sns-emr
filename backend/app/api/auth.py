import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.security import create_access_token
from app.models.user import User

# ✅ Default tenant (created in Step 2)
DEFAULT_TENANT_ID = uuid.UUID("0dac0f4a-9ce2-470d-8c1d-1c4e210b560d")

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/dev-login")
def dev_login(user_id: str, role: str, db: Session = Depends(get_db)):
    """
    Dev-only login:
    - creates/returns a real User row
    - guarantees tenant_id
    - auto-grants interface-scoped RBAC (user_interface_roles)
    - issues JWT with tenant_id embedded
    """

    role = role.strip().upper()
    email = user_id if "@" in user_id else f"{user_id}@sns.local"

    # ------------------------------------------------------------
    # 1) Create or load user
    # ------------------------------------------------------------
    user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            full_name=user_id,
            role=role,
            tenant_id=DEFAULT_TENANT_ID,
            active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Safety net for legacy rows
    if not getattr(user, "tenant_id", None):
        user.tenant_id = DEFAULT_TENANT_ID
        db.commit()
        db.refresh(user)

    # ------------------------------------------------------------
    # 2) Determine interface (CLINICAL vs SURVEY)
    # ------------------------------------------------------------
    interface_name = "SURVEY_ACCESS" if role == "SURVEYOR" else "CLINICAL_EMR"

    interface_id = db.execute(
        text("SELECT id FROM interfaces WHERE name = :name"),
        {"name": interface_name},
    ).scalar()

    role_id = db.execute(
        text(
            """
            SELECT r.id
            FROM roles r
            JOIN interfaces i ON i.id = r.interface_id
            WHERE i.name = :iname AND r.name = :rname
            """
        ),
        {"iname": interface_name, "rname": role},
    ).scalar()

    # ------------------------------------------------------------
    # 3) Grant interface-scoped RBAC if missing
    # ------------------------------------------------------------
    if interface_id and role_id:
        existing = db.execute(
            text(
                """
                SELECT 1
                FROM user_interface_roles
                WHERE tenant_id = :tenant_id
                  AND user_id = :user_id
                  AND interface_id = :interface_id
                  AND role_id = :role_id
                  AND revoked_at IS NULL
                LIMIT 1
                """
            ),
            {
                "tenant_id": user.tenant_id,
                "user_id": user.id,
                "interface_id": interface_id,
                "role_id": role_id,
            },
        ).first()

        if not existing:
            db.execute(
                text(
                    """
                    INSERT INTO user_interface_roles
                        (id, tenant_id, user_id, interface_id, role_id, assigned_at)
                    VALUES
                        (:id, :tenant_id, :user_id, :interface_id, :role_id, :assigned_at)
                    """
                ),
                {
                    "id": uuid.uuid4(),
                    "tenant_id": user.tenant_id,
                    "user_id": user.id,
                    "interface_id": interface_id,
                    "role_id": role_id,
                    "assigned_at": datetime.now(timezone.utc),
                },
            )
            db.commit()

    # ------------------------------------------------------------
    # 4) Issue JWT with tenant context
    # ------------------------------------------------------------
    token = create_access_token(
        subject=str(user.id),
        role=user.role,
        tenant_id=str(user.tenant_id),
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "tenant_id": str(user.tenant_id),
        "role": user.role,
        "interface": interface_name,
    }