import os
import pytest
import requests


API_HOST = os.environ.get("API_HOST", "nginx")


@pytest.fixture(scope="session")
def adminJWT():
    response = requests.post(f"https://{API_HOST}/admin/login",
                             headers={"Content-Type": "application/json"},
                             data={"username": "admin", "password": "Th1s_i$_@_t3sT_p@$$w0rd"})
    token = response.json()["token"]
    yield token


@pytest.fixture(scope="session")
def registrationKey(adminJWT):
    response = requests.get(f"https://{API_HOST}/admin/registration-key",
                            headers={"Content-Type": "application/json",
                                     "Authorization": f"Bearer {adminJWT}"})
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
                             data=data,
                             verify=caPath,
                             cert=cert)
    agentID = response.json()["agentID"]
    yield agentID


@pytest.fixture()
def cert():
    certPath = "/app/ca/certs/proxy/proxy.crt"
    keyPath = "/app/ca/certs/proxy/proxy.pem"
    yield (certPath, keyPath)


@pytest.fixture()
def caPath():
    yield "/app/ca/capy/ca.crt"