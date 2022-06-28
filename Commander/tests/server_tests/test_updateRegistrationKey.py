import json


def testUpdateRegKey(client, sample_RegistrationKey, sample_valid_JWT):
    # prepare mongomock with relevant sample documents
    regkey = sample_RegistrationKey
    regkey.save()
    # create a new registration key
    response = client.put("/admin/registration-key",
                          headers={"Content-Type": "application/json",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                          data=json.dumps({}))
    assert response.status_code == 200
    assert "registrationKey" in response.json


def testNewRegKey(client, sample_valid_JWT):
    # create a new registration key
    response = client.put("/admin/registration-key",
                          headers={"Content-Type": "application/json",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                          data=json.dumps({}))
    assert response.status_code == 200
    assert "registrationKey" in response.json