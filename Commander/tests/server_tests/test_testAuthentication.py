import json


def testValidJWT(client):
    # test authentication with a valid JWT
    response = client.get("/admin/authenticate",
                          headers={"Content-Type": "application/json",
                                   # token generated with https://jwt.io/#debugger-io using default secret key
                                   "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.fTNmI6XjfES0SYawD41fUBSzzZheBs7A1ntD6JNuRhI"},
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


def testBadSignatureJWT(client):
    # test authentication with a fake JWT in valid format
    response = client.get("/admin/authenticate",
                          headers={"Content-Type": "application/json",
                                   "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"},
                          data=json.dumps({}))
    assert response.status_code == 422
    assert response.json["msg"] == "Signature verification failed"


def testExpiredJWT(client):
    # test authentication with an expired JWT
    response = client.get("/admin/authenticate",
                          headers={"Content-Type": "application/json",
                                   "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzk5OTB9.qYidunY1JWO58V-LfgT_yWrKgcowodGp_ucFvL4hCOE"},
                          data=json.dumps({}))
    assert response.status_code == 401
    assert response.json["msg"] == "Token has expired"
