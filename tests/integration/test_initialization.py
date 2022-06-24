import json
import os
import pytest
import requests

"""
Ensure that all of our fixtures that we use in integration tests are set up correctly.
"""

API_HOST = os.environ.get("API_HOST", "nginx")

@pytest.mark.order(0)
def test_authentication(adminJWT, caPath):
    # prepare and send login request for default admin
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {adminJWT}"}
    response = requests.get(f"https://{API_HOST}/admin/authenticate",
                            headers=headers,
                            verify=caPath)
    assert response.status_code == 200
    assert response.json()["success"] == "authentication token is valid"


@pytest.mark.order(1)
def test_registrationKey(registrationKey):
    assert len(registrationKey) == 36


@pytest.mark.order(2)
def test_agentRegistration(agentID):
    assert len(agentID) == 36


@pytest.mark.order(3)
def test_adminCreation(adminJWT, caPath):
    # prepare and send new admin request
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {adminJWT}"}
    data = {"username": "test",
            "password": "T3st_P@$$w0rd!",
            "name": "Test User"}
    response = requests.post(f"https://{API_HOST}/admin/account",
                             headers=headers,
                             data=json.dumps(data),
                             verify=caPath)
    assert response.status_code == 200
    assert response.json()["success"] == "successfully created new admin account"
    # validate that we can log in with the new account
    url = f"https://{API_HOST}/admin/login"
    headers = {"Content-Type": "application/json"},
    data = {"username": "test",
            "password": "T3st_P@$$w0rd!"}
    response = requests.post(url,
                             headers=headers,
                             data=json.dumps(data),
                             verify=caPath)
    assert response.status_code == 200
    assert "token" in response.json()
