import pytest
from datetime import datetime

from app.models.enums import CareSettingEnum
from app.schemas.safety_assessment import (
    derive_safety_responsibility,
    validate_care_setting_change,
)


def test_home_is_hospice_managed():
    """
    HOME settings must always be hospice-managed.
    """
    assert derive_safety_responsibility(CareSettingEnum.HOME) == "HOSPICE_MANAGED"


def test_facility_is_facility_managed():
    """
    Non-HOME settings must always be facility-managed.
    """
    assert derive_safety_responsibility(CareSettingEnum.SNF) == "FACILITY_MANAGED"


def test_care_setting_locked_after_sign():
    """
    Once a safety assessment is signed, the care setting
    must not be changeable under any circumstance.
    """

    class MockAssessment:
        signed_at = datetime(2026, 1, 1)

    with pytest.raises(ValueError):
        validate_care_setting_change(
            MockAssessment(),
            CareSettingEnum.HOME,
        )
