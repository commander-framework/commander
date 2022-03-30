import json


def testNewAdmin(client, sample_valid_JWT):
    # send login credentials with new password
    response = client.post("/admin/account",
                           headers={"Content-Type": "application/json",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                           data=json.dumps({"username": "newuser",
                                            "password": "new_Password",
                                            "name": "New User"}))
    assert response.status_code == 200
    assert response.json["success"] == "successfully created new admin account"
    # TODO: make sure admin was saved to DB


def testDuplicateUsernameNewAdmin(client, sample_valid_JWT, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user.save()
    # send login credentials with new password
    response = client.post("/admin/account",
                           headers={"Content-Type": "application/json",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                           data=json.dumps({"username": sample_User["username"],
                                            "password": "new_Password",
                                            "name": "New User"}))
    assert response.status_code == 400
    assert response.json["error"] == "username already taken"


def testMissingFieldsNewAdmin(client, sample_valid_JWT):
    # send login credentials with new password
    response = client.post("/admin/account",
                           headers={"Content-Type": "application/json",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                           data=json.dumps({}))
    assert response.status_code == 400
    assert response.json["error"] == "request is missing the following parameters: data=['username', 'password', 'name']"