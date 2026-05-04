import jwt
import uuid
from datetime import datetime, timedelta

SECRET_KEY = "CHANGE_ME_LATER"  # move to env in production
ALGORITHM = "HS256"


def create_survey_token(
    patient_id: str,
    issued_by: str | None = None,
    minutes: int = 10,
):
    """
    Create a short-lived, patient-scoped survey token
    for one-click chart PDF access.
    """
    jti = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=minutes)

    payload = {
        "type": "survey",
        "scope": "chart_pdf",
        "patient_id": patient_id,
        "jti": jti,
        "exp": expires_at,
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return token, jti, expires_at


def decode_survey_token(token: str) -> dict:
    """
    Decode and validate a survey token.
    Raises jwt exceptions if invalid or expired.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
