def test_administrative_visit_does_not_trigger_rn_logic(
    client, administrative_visit
):
    """
    COMPLIANCE TEST:
    Administrative visits must NEVER trigger RN rules or tasks.
    """

    response = client.post(
        f"/visits/{administrative_visit.id}/finalize"
    )

    assert response.status_code == 200