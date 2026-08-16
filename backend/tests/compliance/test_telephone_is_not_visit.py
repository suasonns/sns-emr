def test_telephone_visit_never_closes_tasks(
    client, rn_headers, telephone_rn_visit
):
    """
    COMPLIANCE TEST:
    Telephone interactions are informational only.
    """

    response = client.post(
        f"/visits/{telephone_rn_visit.id}/finalize",
        headers=rn_headers,
    )

    assert response.status_code == 400
