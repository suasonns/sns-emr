import pytest


class DummyUser:
    def __init__(self, role: str):
        self.role = role


@pytest.mark.core_rule("8")
def test_finalize_requires_staff_confirmation():
    """
    Core Rule:
    No note may finalize without explicit staff review confirmation.
    """
    base = pytest.importorskip("services.documentation.finalize_base")
    policy_mod = pytest.importorskip(
        "services.documentation.finalization_policy"
    )

    user = DummyUser("RN")
    policy = policy_mod.FinalizeRequestPolicy(
        staff_confirmed_review=False,
        staff_requested_auto_finalize=False,
    )

    with pytest.raises(Exception):
        base.enforce_finalize_guards(
            discipline="RN",
            current_user=user,
            policy=policy,
            countersigning_user=None,
        )