from typing import Optional
from fastapi import Depends
import uuid


def get_current_user_id() -> str:
    """
    Temporary placeholder for authentication.

    Replace later with real JWT / auth system.
    """

    return str(uuid.uuid4())