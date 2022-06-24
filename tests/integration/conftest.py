import json
import os
import pytest
import requests


API_HOST = os.environ.get("API_HOST", "nginx")


@pytest.fixture(scope="session")
def adminJWT(caPath):
    response = requests.post(f"https://{API_HOST}/admin/login",
                             headers={"Content-Type": "application/json"},
                             data=json.dumps({"username": "admin", "password": "Th1s_i$_@_t3sT_p@$$w0rd"}),
                             verify=caPath)
    token = response.json()["token"]
    yield token


@pytest.fixture(scope="session")
def registrationKey(adminJWT, caPath):
    response = requests.get(f"https://{API_HOST}/admin/registration-key",
                            headers={"Content-Type": "application/json",
                                     "Authorization": f"Bearer {adminJWT}"},
                            verify=caPath)
    registrationKey = response.json()["registrationKey"]
    yield registrationKey


@pytest.fixture(scope="session")
def agentID(caPath, cert, registrationKey):
    url = f"https://{API_HOST}/agent/register"
    headers = {"Content-Type": "application/json"}
    data = {"registrationKey:": registrationKey,
            "hostname": "test-hostname",
            "os": "Linux"}
    response = requests.post(url,
                             headers=headers,
                             data=json.dumps(data),
                             verify=caPath,
                             cert=cert)
    agentID = response.json()["agentID"]
    yield agentID


@pytest.fixture(scope="session")
def cert():
    certPath = "/app/ca/certs/proxy/proxy.crt"
    keyPath = "/app/ca/certs/proxy/proxy.pem"
    yield (certPath, keyPath)


@pytest.fixture(scope="session")
def caPath():
    yield "/app/ca/ca.crt"