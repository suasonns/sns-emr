import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db_session import get_db
from app.models.user import User
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/dev-login")
def dev_login(user_id: str, role: str, db: Session = Depends(get_db)):
    """
    Dev-only login:
    - user_id is treated as email if it contains '@'
    - otherwise generates <user_id>@sns.local
    - creates/returns a real User row
    - token 'sub' is the user's UUID (string)
    """
    email = user_id if "@" in user_id else f"{user_id}@sns.local"

    user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            full_name=user_id,  # dev-friendly
            role=role,
            active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # ✅ IMPORTANT: your create_access_token expects (subject, role)
    token = create_access_token(subject=str(user.id), role=user.role)

    return {"access_token": token, "token_type": "bearer"}
