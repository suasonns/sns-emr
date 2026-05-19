import pytest


@pytest.mark.core_rule("6")
def test_rn_validation_blocks_when_sections_missing():
    """
    Core Rule:
    RN notes must include core assessment sections.
    """
    rn_val = pytest.importorskip("services.documentation.rn_validation")

    validation = rn_val.validate_rn_visit(
        transcript="Routine visit.",
        structured_sections={},
        medication_list=[{"name": "morphine"}],
        prior_visit_summary="prior visit",
    )

    assert validation.is_blocking is True
