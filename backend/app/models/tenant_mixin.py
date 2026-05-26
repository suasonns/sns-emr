from __future__ import annotations


class TenantScopedMixin:
    """
    Marker mixin for tenant-scoped models.
    Models inheriting this mixin must define tenant_id themselves.
    """
    __tenant_scoped__ = True