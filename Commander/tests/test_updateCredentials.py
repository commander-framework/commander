import json


def testCredChange(client, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user.save()
    # send login credentials with new password
    response = client.patch("/admin/login",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps({"username": sample_User["username"],
                                            "password": "samplePass",
                                            "newPassword": "new_Password"}))
    assert response.status_code == 200
    assert response.json["success"] == "successfully changed the password for your account"
    # make sure the database was updated with the new password
    response = client.post("/admin/login",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps({"username": sample_User["username"],
                                            "password": "new_Password"}))
    assert response.status_code == 200


def testBadUsernameCredChange(client, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user.save()
    # send login credentials with new password
    response = client.patch("/admin/login",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps({"username": "not_a_valid_user",
                                            "password": "samplePass",
                                            "newPassword": "new_Password"}))
    assert response.status_code == 401
    assert response.json["error"] == "username not found"


def testBadPasswordCredChange(client, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user.save()
    # send login credentials with new password
    response = client.patch("/admin/login",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps({"username": sample_User["username"],
                                            "password": "wrong_password",
                                            "newPassword": "new_Password"}))
    assert response.status_code == 401
    assert response.json["error"] == "password does not match"


def testMissingFieldsCredChange(client, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user.save()
    # send login credentials with new password
    response = client.patch("/admin/login",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps({}))
    assert response.status_code == 400
    assert response.json["error"] == "request is missing the following parameters: data=['username', 'password', 'newPassword']"