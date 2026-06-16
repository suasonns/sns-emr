from __future__ import annotations

import secrets


def generate_user_session_reference() -> str:
    """
    Non-clinical random reference, generated per login for troubleshooting/training.
    Does not grant access and contains no PHI.
    """
    a = secrets.token_hex(2).upper()
    b = secrets.token_hex(2).upper()
    return f"USR-{a}-{b}"