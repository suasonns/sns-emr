"""
SNS Staff & Access -- job title catalog (Phase UM-2C).

Job Title sits between Department and Platform Role in the organizational
hierarchy (Platform > Department > Job Title > Platform Role > Access
Level). Like Department, it is a presentational/organizational
classification only -- it grants NO permissions. Authorization always
flows through app.core.roles.role_can() / PLATFORM_PERMISSION_MATRIX,
never through this module.

Job titles are department-scoped: each department has its own catalog of
valid titles, so the "Add SNS Staff" form can offer a cascading
Department -> Job Title selector instead of free text. Departments not
yet represented here (e.g. PLATFORM_ADMINISTRATION) have no catalog and
therefore accept any free-text job title -- this is deliberate so rollout
of the catalog can proceed department-by-department without blocking
existing accounts in departments not yet scoped.
"""

from __future__ import annotations

JOB_TITLES_BY_DEPARTMENT: dict[str, frozenset[str]] = {
    "EXECUTIVE": frozenset({"CEO", "COO", "CFO", "Founder", "President"}),
    "DEVELOPMENT": frozenset(
        {"Software Developer", "Senior Software Developer", "Development Lead"}
    ),
    "DEVOPS": frozenset(
        {"DevOps Engineer", "Infrastructure Engineer", "Cloud Engineer"}
    ),
    "SECURITY": frozenset({"Security Administrator", "Security Analyst"}),
    "COMPLIANCE": frozenset({"Compliance Administrator", "Compliance Analyst"}),
    "BILLING_AND_LICENSING": frozenset(
        {"Billing Administrator", "Finance Administrator", "Revenue Analyst"}
    ),
    "CUSTOMER_SERVICE": frozenset(
        {"Customer Service Representative", "Customer Success Specialist"}
    ),
    "CUSTOMER_SUPPORT": frozenset(
        {"Support Specialist", "Support Engineer", "Technical Support Specialist"}
    ),
    "IMPLEMENTATION": frozenset(
        {"Implementation Specialist", "Implementation Manager"}
    ),
    "QUALITY_ASSURANCE": frozenset({"QA Analyst", "QA Engineer"}),
    "AI_OPERATIONS": frozenset({"AI Operations Specialist", "AI Administrator"}),
}


def job_titles_for_department(department: str | None) -> list[str]:
    """Sorted job-title catalog for a (already-normalized, uppercase)
    department code. Empty list if the department has no catalog yet
    (free text is accepted for those)."""
    if not department:
        return []
    return sorted(JOB_TITLES_BY_DEPARTMENT.get(department.strip().upper(), []))


def normalize_job_title(department: str | None, job_title: str | None) -> str | None:
    """Validates/normalizes a job title against its department's catalog.

    - Returns None for blank input.
    - If the department has a defined catalog, the title must match one
      of its entries (case-insensitively); the canonical-cased entry is
      returned.
    - If the department has no catalog yet (or no department was given),
      the trimmed free-text value is returned unchanged -- see module
      docstring.
    Raises ValueError when the department has a catalog and the title
    does not match any entry, so callers can turn it into a 400/422.
    """
    trimmed = (job_title or "").strip()
    if not trimmed:
        return None

    catalog = JOB_TITLES_BY_DEPARTMENT.get((department or "").strip().upper())
    if not catalog:
        return trimmed

    match = next((title for title in catalog if title.lower() == trimmed.lower()), None)
    if match is None:
        raise ValueError(
            f"job_title must be one of {sorted(catalog)} for the selected department"
        )
    return match
