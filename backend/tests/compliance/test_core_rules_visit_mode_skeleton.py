import pytest


@pytest.mark.core_rule("2")
@pytest.mark.requires_impl("visit_mode_enforcement")
@pytest.mark.xfail(
    reason="visit_mode enforcement not implemented yet"
)
def test_rn_telephone_not_counted_as_visit():
    """
    Core Rule:
    RN TELEPHONE interactions must never count as visits.
    """
    assert False