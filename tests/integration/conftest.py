import pytest
import requests


@pytest.fixture(scope="session")
def adminJWT():
    response = requests.post("https://localhost/admin/login",
                             headers={"Content-Type": "application/json"},
                             data={"username": "admin", "password": "Th1s_i$_@_t3sT_p@$$w0rd"})
    token = response.json()["token"]
    yield token


@pytest.fixture(scope="session")
def registrationKey(adminJWT):
    response = requests.get("https://localhost/admin/registration-key",
                            headers={"Content-Type": "application/json",
                                     "Authorization": f"Bearer {adminJWT}"})
    registrationKey = response.json()["registrationKey"]
    yield registrationKey


@pytest.fixture()
def cert():
    certPath = "/app/ca/certs/proxy/proxy.crt"
    keyPath = "/app/ca/certs/proxy/proxy.pem"
    yield (certPath, keyPath)


@pytest.fixture()
def caPath():
    yield "/app/ca/capy/ca.crt"