"""
Enterprise task completion guard.

Rule:
A task cannot be marked COMPLETED unless completion evidence exists.
"""

from __future__ import annotations

from fastapi import HTTPException, status


def assert_task_completion_is_valid(
    *,
    status: str,
    completed_at,
    completion_reference_type,
    completion_reference_id,
) -> None:
    """
    Enforces hospice compliance:
    COMPLETED tasks must have evidence.
    """

    if status != "COMPLETED":
        return

    if not completed_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="COMPLETED tasks must have completed_at timestamp.",
        )

    if not completion_reference_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="COMPLETED tasks must have completion_reference_type.",
        )

    if not completion_reference_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="COMPLETED tasks must have completion_reference_id.",
        )