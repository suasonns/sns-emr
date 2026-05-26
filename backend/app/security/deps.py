from __future__ import annotations

import uuid
from fastapi import Request


def get_current_user_id(request: Request) -> str:
    """
    Development-safe user dependency.

    - Accepts any request
    - Does NOT enforce authentication during dev
    """

    # Store on request for middleware use
    user_id = str(uuid.uuid4())
    request.state.user_id = user_id

    return user_id
