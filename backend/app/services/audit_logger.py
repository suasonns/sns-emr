from app.models.audit_log import AuditLog


def log_event(
    *,
    user_id: str,
    role: str,
    action: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    ip_address: str | None = None,
):
    """
    Create an audit log entry.
    In production, this will be saved to the database.
    """
    audit = AuditLog(
        user_id=user_id,
        role=role,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
    )

    # TEMPORARY: Print instead of DB write
    # This will be replaced with session.add(audit)
    print(
        f"[AUDIT] user={user_id} role={role} "
        f"action={action} entity={entity_type}:{entity_id} ip={ip_address}"
    )
