def test_telephone_visit_never_closes_tasks(
    client, telephone_rn_visit
):
    """
    COMPLIANCE TEST:
    Telephone interactions are informational only.
    """

    response = client.post(
        f"/visits/{telephone_rn_visit.id}/finalize"
    )

    assert response.status_code == 400
