import os
import pytest
import requests

"""
Ensure that all of our fixtures that we use in integration tests are set up correctly.
"""

API_HOST = os.environ.get("API_HOST", "nginx")

@pytest.mark.order(0)
def test_authentication(adminJWT):
    url = f"https://{API_HOST}/admin/authenticate"
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {adminJWT}"}
    response = requests.post(url,
                             headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] == "successfully created new admin account"


@pytest.mark.order(1)
def test_registrationKey(registrationKey):
    assert len(registrationKey) == 36


@pytest.mark.order(2)
def test_agentRegistration(agentID):
    assert len(agentID) == 36


@pytest.mark.order(3)
def test_adminCreation(adminJWT):
    url = f"https://{API_HOST}/admin/account"
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
