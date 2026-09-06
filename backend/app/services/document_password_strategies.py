"""Configurable, generic document-password strategies.

Provides an extension point for a tenant to configure candidate passwords
that should be attempted automatically before prompting a user to enter a
document password by hand. Deliberately contains NO vendor-specific (e.g.
Kaiser), patient-attribute-derived (e.g. date of birth), or filename-parsing
logic -- every candidate is an explicit, tenant-configured literal string.
Absent configuration, this always resolves to an empty list, i.e. the
upload flow falls through to prompting the user (PDF_PASSWORD_REQUIRED).
"""
from __future__ import annotations

import json
import os
import uuid


def get_configured_password_candidates(tenant_id: uuid.UUID) -> list[str]:
    """Returns this tenant's configured candidate passwords, in order.

    Configuration source: the ``DOCUMENT_PASSWORD_STRATEGIES_JSON`` env var,
    a JSON object mapping tenant id (string) -> list of candidate password
    strings for that tenant, e.g.::

        DOCUMENT_PASSWORD_STRATEGIES_JSON={"<tenant-uuid>": ["candidate1", "candidate2"]}

    Any missing/invalid configuration safely yields an empty list rather
    than raising, since this is a best-effort convenience layer in front of
    the mandatory PDF_PASSWORD_REQUIRED prompt-the-user flow, never a
    replacement for it.
    """
    raw = os.getenv("DOCUMENT_PASSWORD_STRATEGIES_JSON")
    if not raw:
        return []
    try:
        config = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(config, dict):
        return []
    candidates = config.get(str(tenant_id))
    if not isinstance(candidates, list):
        return []
    return [candidate for candidate in candidates if isinstance(candidate, str) and candidate]
