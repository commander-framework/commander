import json


def testGenRegKey(client, sample_valid_JWT):
    # create a new registration key
    response = client.get("/admin/registration-key",
                          headers={"Content-Type": "application/json",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                          data=json.dumps({}))
    assert response.status_code == 200
    assert "registration-key" in response.json


def testGetRegKey(client, sample_RegistrationKey, sample_valid_JWT):
    # prepare mongomock with relevant sample documents
    regkey = sample_RegistrationKey
    regkey.save()
    # get the existing registration key
    response = client.get("/admin/registration-key",
                          headers={"Content-Type": "application/json",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                          data=json.dumps({}))
    assert response.status_code == 200
    assert response.json["registration-key"] == sample_RegistrationKey["regKey"]