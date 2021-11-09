import json


def testNewAdmin(client, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
    # send login credentials with new password
    response = client.post("/admin/account",
                           headers={"Content-Type": "application/json",
                                    "Auth-Token": sample_valid_Session["authToken"],
                                    "Username": sample_valid_Session["username"]},
                           data=json.dumps({"username": "newuser",
                                            "password": "new_Password",
                                            "name": "New User"}))
    assert response.status_code == 200
    assert response.json["success"] == "successfully created new admin account"


def testExpiredSessionNewAdmin(client, sample_expired_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_expired_Session)
    user.save()
    # send login credentials with new password
    response = client.post("/admin/account",
                           headers={"Content-Type": "application/json",
                                    "Auth-Token": sample_expired_Session["authToken"],
                                    "Username": sample_expired_Session["username"]},
                           data=json.dumps({"username": "newuser",
                                            "password": "new_Password",
                                            "name": "New User"}))
    assert response.status_code == 401
    assert response.json["error"] == "invalid auth token or token expired"


def testDuplicateUsernameNewAdmin(client, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
    # send login credentials with new password
    response = client.post("/admin/account",
                           headers={"Content-Type": "application/json",
                                    "Auth-Token": sample_valid_Session["authToken"],
                                    "Username": sample_valid_Session["username"]},
                           data=json.dumps({"username": sample_User["username"],
                                            "password": "new_Password",
                                            "name": "New User"}))
    assert response.status_code == 400
    assert response.json["error"] == "username already taken"


def testMissingFieldsNewAdmin(client, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
    # send login credentials with new password
    response = client.post("/admin/account",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps({}))
    assert response.status_code == 400
    assert response.json["error"] == "request is missing the following parameters: headers=['Auth-Token', 'Username'], data=['username', 'password', 'name']"