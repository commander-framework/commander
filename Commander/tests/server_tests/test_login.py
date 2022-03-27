from datetime import datetime
import json
from jwt import decode
from utils import timestampToDatetime


def testLogin(client, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user.save()
    # send login credentials to get a session token
    response = client.post("/admin/login",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps({"username": sample_User["username"],
                                            "password": "samplePass"}))
    assert response.status_code == 200
    assert "token" in response.json
    token = response.json["token"]
    # make sure a valid session was saved to the db
    response = client.get("/admin/authenticate",
                          headers={"Content-Type": "application/json",
                                   "Authorization": "Bearer " + token},
                          data=json.dumps({}))
    assert response.status_code == 200
    assert response.json["success"] == "authentication token is valid"


def testBadUsernameLogin(client, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user.save()
    # send login credentials to get a session token
    response = client.post("/admin/login",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps({"username": "not_a_valid_user",
                                            "password": "samplePass"}))
    assert response.status_code == 401
    assert response.json["error"] == "username not found"


def testBadPasswordLogin(client, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user.save()
    # send login credentials to get a session token
    response = client.post("/admin/login",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps({"username": sample_User["username"],
                                            "password": "wrong_password"}))
    assert response.status_code == 401
    assert response.json["error"] == "password does not match"


def testMissingFieldsLogin(client, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user.save()
    # send login credentials to get a session token
    response = client.post("/admin/login",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps({}))
    assert response.status_code == 400
    assert response.json["error"] == "request is missing the following parameters: data=['username', 'password']"