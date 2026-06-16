from fastapi import HTTPException

def require_owner(user) -> None:
    """
    Enforces OWNER (management) access.
    """
    if getattr(user, "role", None) != "OWNER":
        raise HTTPException(
            status_code=403,
            detail="Owner access required",
        )