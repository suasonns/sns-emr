from fastapi import HTTPException


def assert_tenant_ownership(
    *,
    record_tenant_id: str,
    request_tenant_id: str,
    entity: str = "record",
):
    """
    Prevent cross-tenant access
    """

    if str(record_tenant_id) != str(request_tenant_id):
        raise HTTPException(
            status_code=403,
            detail=f"{entity} belongs to another hospice"
        )