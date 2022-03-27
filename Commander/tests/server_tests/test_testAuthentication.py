import json


def testValidJWT(client, sample_valid_JWT):
    # test authentication with a valid JWT
    response = client.get("/admin/authenticate",
                          headers={"Content-Type": "application/json",
                                   "Authorization": f"Bearer {sample_valid_JWT}"},
                          data=json.dumps({}))
    assert response.status_code == 200
    assert response.json["success"] == "authentication token is valid"


def testMissingJWT(client):
    # test authentication with no JWT
    response = client.get("/admin/authenticate",
                          headers={"Content-Type": "application/json"},
                          data=json.dumps({}))
    assert response.status_code == 401
    assert response.json["msg"] == "Missing Authorization Header"


def testInvalidJWT(client):
    # test authentication with an invalid JWT
    response = client.get("/admin/authenticate",
                          headers={"Content-Type": "application/json",
                                   "Authorization": "Bearer " + "non.valid.token"},
                          data=json.dumps({}))
    assert response.status_code == 422
    assert response.json["msg"][:23] == "Invalid header string: "


def testBadSignatureJWT(client, sample_bad_sig_JWT):
    # test authentication with a fake JWT in valid format
    response = client.get("/admin/authenticate",
                          headers={"Content-Type": "application/json",
                                   "Authorization": f"Bearer {sample_bad_sig_JWT}"},
                          data=json.dumps({}))
    assert response.status_code == 422
    assert response.json["msg"] == "Signature verification failed"


def testExpiredJWT(client, sample_expired_JWT):
    # test authentication with an expired JWT
    response = client.get("/admin/authenticate",
                          headers={"Content-Type": "application/json",
                                   "Authorization": f"Bearer {sample_expired_JWT}"},
                          data=json.dumps({}))
    assert response.status_code == 401
    assert response.json["msg"] == "Token has expired"
