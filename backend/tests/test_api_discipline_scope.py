def test_rn_can_list_patients(client, rn_headers):
    r = client.get("/patients/", headers=rn_headers)
    assert r.status_code in (200, 204), r.text


def test_chha_cannot_list_all_patients(client, chha_headers):
    r = client.get("/patients/", headers=chha_headers)
    assert r.status_code == 403, r.text


def test_volunteer_cannot_list_all_patients(client, volunteer_headers):
    r = client.get("/patients/", headers=volunteer_headers)
    assert r.status_code == 403, r.text