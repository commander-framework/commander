import json


def testDeleteAdmin(client, sample_valid_JWT, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user.save()
    # delete the admin account
    response = client.delete("/admin/account",
                             headers={"Content-Type": "application/json",
                                      "Authorization": "Bearer " + sample_valid_JWT},
                             data=json.dumps({"username": "testuser"}))
    assert response.status_code == 200
    assert response.json["success"] == "successfully deleted admin account"


def testMissingUserDeleteAdmin(client, sample_valid_JWT, sample_User):
    # attempt to delete the admin acount
    response = client.delete("/admin/account",
                             headers={"Content-Type": "application/json",
                                      "Authorization": "Bearer " + sample_valid_JWT},
                             data=json.dumps({"username": "testuser"}))
    assert response.status_code == 400
    assert response.json["error"] == "username not found"


def testMissingFieldsDeleteAdmin(client, sample_valid_JWT):
    # send login credentials with new password
    response = client.delete("/admin/account",
                           headers={"Content-Type": "application/json",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                           data=json.dumps({}))
    assert response.status_code == 400
    assert response.json["error"] == "request is missing the following parameters: data=['username']"