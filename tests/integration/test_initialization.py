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
    # prepare and send login request for test admin
    response = requests.get(f"https://{API_HOST}/admin/authenticate",
                            headers={"Content-Type": "application/json",
                                     "Authorization": f"Bearer {adminJWT}"},
                            verify=caPath)
    assert response.status_code == 200
    assert response.json()["success"] == "authentication token is valid"


@pytest.mark.order(1)
def test_registrationKey(registrationKey):
    assert len(registrationKey) == 36


@pytest.mark.order(2)
def test_agentRegistration(agentID):
    assert len(agentID) == 36
