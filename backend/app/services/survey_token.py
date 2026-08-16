import os
import jwt
import uuid
from datetime import datetime, timedelta, timezone

ALGORITHM = "HS256"


def _secret_key() -> str:
    """
    Survey tokens grant chart PDF access, so they are signed with the
    application secret rather than a literal. Resolved per call so the process
    cannot start holding a stale value.
    """
    secret = os.getenv("SURVEY_TOKEN_SECRET") or os.getenv("SECRET_KEY", "")

    if len(secret) < 32:
        raise RuntimeError(
            "SURVEY_TOKEN_SECRET or SECRET_KEY must be set and at least 32 characters"
        )

    return secret


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
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)

    payload = {
        "type": "survey",
        "scope": "chart_pdf",
        "patient_id": patient_id,
        "jti": jti,
        "exp": expires_at,
    }

    token = jwt.encode(payload, _secret_key(), algorithm=ALGORITHM)

    return token, jti, expires_at


def decode_survey_token(token: str) -> dict:
    """
    Decode and validate a survey token.
    Raises jwt exceptions if invalid or expired.
    """
    return jwt.decode(token, _secret_key(), algorithms=[ALGORITHM])
