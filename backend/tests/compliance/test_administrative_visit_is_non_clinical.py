def test_administrative_visit_does_not_trigger_rn_logic(
    client,
    rn_headers,
    administrative_visit,
):
    response = client.post(
        f"/visits/{administrative_visit.id}/finalize",
        headers=rn_headers,
    )

    print("STATUS:", response.status_code)
    print("BODY:", response.text)

    assert response.status_code == 200