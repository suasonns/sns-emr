def test_routine_rn_non_supervisory_visit_is_blocked(client, routine_rn_visit):
    """
    COMPLIANCE TEST:
    Routine RN visits MUST be supervisory.
    If this test ever fails, RN authority has been weakened.
    """

    response = client.post(
        f"/visits/{routine_rn_visit.id}/finalize"
    )

    assert response.status_code == 400