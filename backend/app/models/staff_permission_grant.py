# models/staff_permission_grant.py
#
# SNS Staff & Access -- delegated capability grants (Phase UM-3, "problems
# escalate upward, work delegates downward").
#
# A row here ADDS one `staff.*` capability (see app.core.roles.
# STAFF_CAPABILITIES) to one target platform-staff account, on top of
# whatever their PLATFORM_PERMISSION_MATRIX role default already grants.
# It never removes/overrides a role default, never grants Ownership
# Continuity authority (staff.assign_owner_role is permanently
# non-delegable -- enforced in app.core.roles, not here), and never raises
# an actor's authority above their own ceiling (enforced by
# app.core.roles.can_delegate_capability at grant time).
#
# A grant is "active" while `revoked_at IS NULL` and
# (`expires_at IS NULL OR expires_at > now()`). Revoking never deletes the
# row -- this table is itself an audit trail of who delegated what, when,
# why, and who (if anyone) took it back.

from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class StaffPermissionGrant(BaseModel):
    __tablename__ = "staff_permission_grants"

    __table_args__ = (
        Index("ix_staff_permission_grants_target_user_id", "target_user_id"),
    )

    target_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # One entry from app.core.roles.STAFF_CAPABILITIES. Validated in
    # Python (owner_admin.py) at grant time -- no DB enum, same convention
    # as platform/department/job_title/account_type/platform_staff_status.
    capability = Column(String(64), nullable=False)

    granted_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    granted_at = Column(DateTime(timezone=True), nullable=True)
    reason = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    revoke_reason = Column(Text, nullable=True)
