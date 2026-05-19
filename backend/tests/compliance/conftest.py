"""
Compliance test scaffolding.

These tests are guardrail tests designed to prevent regression
against /docs/compliance/core_rules.md.

Rules:
- Keep tests fast
- Deterministic only
- Use xfail for unimplemented enforcement
"""

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "core_rule(section): marks a test as covering a core_rules.md section",
    )
    config.addinivalue_line(
        "markers",
        "requires_impl(name): test requires implementation to exist",
    )