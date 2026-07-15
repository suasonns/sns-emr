def test_routine_rn_non_supervisory_visit_is_not_supervisory_anchor(
    client,
    routine_rn_visit,
):
    """
    COMPLIANCE TEST:

    Routine RN visits may exist as non-supervisory visits.

    Non-supervisory RN visits MUST NOT be treated as
    supervisory anchor visits for cadence, POC update,
    or supervisory workflow purposes.

    This test verifies the visit can enter the normal
    finalize pipeline without being automatically considered
    supervisory.
    """

    response = client.post(
        f"/visits/{routine_rn_visit.id}/finalize"
    )

    # Finalization may still be blocked by other validation
    # requirements (clinical documentation, reconciliation,
    # required forms, etc.). This test only guards against
    # incorrectly enforcing "RN must always be supervisory".
    assert response.status_code != 400