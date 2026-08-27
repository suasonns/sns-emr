"""
Tenants that must never be deleted or wiped by any bulk-cleanup,
purge, or test-fixture script, regardless of environment.

These are standing infrastructure/production tenants, not disposable
test fixtures:

- SNS Hospice Solutions (platform tenant; also DEV_PLATFORM_TENANT_ID,
  home of the platform OWNER account)
- North East Billing (billing tenant; also DEV_BILLING_TENANT_ID)
- Love & Faith Hospice Services, Inc. (production hospice tenant)
- Angela Hospice (Training) (also the fixed pytest test tenant id --
  see tests/conftest.py:_test_tenant_id())
- Silva Hospice (Training)

Any script that enumerates tenants for bulk deletion (data purges,
housekeeping jobs, admin tooling) MUST exclude PROTECTED_TENANT_IDS.
"""
import uuid

PROTECTED_TENANT_IDS: frozenset[uuid.UUID] = frozenset(
    {
        uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),  # SNS Hospice Solutions (platform)
        uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),  # North East Billing
        uuid.UUID("01271980-0000-0000-0000-000005101977"),  # Love & Faith Hospice Services, Inc.
        uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),  # Angela Hospice (Training)
        uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),  # Silva Hospice (Training)
    }
)


def assert_not_protected(tenant_id: "uuid.UUID | str", *, action: str = "delete") -> None:
    """
    Raise ValueError if tenant_id is one of the standing protected
    tenants. Call this at the top of any bulk-delete/purge routine
    before it touches a tenant's data.
    """
    tid = tenant_id if isinstance(tenant_id, uuid.UUID) else uuid.UUID(str(tenant_id))
    if tid in PROTECTED_TENANT_IDS:
        raise ValueError(
            f"Refusing to {action} protected tenant {tid}: this tenant is "
            "permanently exempt from bulk deletion/purge (see "
            "app/core/protected_tenants.py)."
        )
