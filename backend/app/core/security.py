from datetime import datetime, timedelta
from typing import Optional
from jose import jwt

SECRET_KEY = "CHANGE_ME_LATER"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
):
    to_encode = {
        "sub": subject,
        "role": role,
        "iat": datetime.utcnow(),
    }

    if expires_delta:
        to_encode["exp"] = datetime.utcnow() + expires_delta
    else:
        to_encode["exp"] = datetime.utcnow() + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
