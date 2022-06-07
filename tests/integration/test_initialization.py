import requests


def test_adminCreation(adminJWT):
    url = "https://localhost/admin/account"
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {adminJWT}"}
    data = {"username": "test",
            "password": "T3st_P@$$w0rd!",
            "name": "Test User"}
    response = requests.post(url,
                             headers=headers,
                             data=data)
    assert response.status_code == 200
    assert response.json()["success"] == "successfully created new admin account"


def test_agentRegistration(cert, caPath, registrationKey):
    url = "https://localhost/agent/register"
    headers = {"Content-Type": "application/json"}
    data = {"registrationKey:": registrationKey,
            "hostname": "test-hostname",
            "os": "Linux"}
    response = requests.post(url,
                             headers=headers,
                             data=data,
                             verify=caPath,
                             cert=cert)
    assert response.status_code == 200
    assert len(response.json()["agentID"]) == 36
