import json
import os
import pytest
import requests
import zipfile


API_HOST = os.environ.get("API_HOST", "nginx")


@pytest.fixture(scope="session", params=["/app/ca/ca.crt"])
def adminJWT(request):
    # log in with default admin
    response = requests.post(f"https://{API_HOST}/admin/login",
                             headers={"Content-Type": "application/json"},
                             data=json.dumps({"username": "admin",
                                              "password": "Th1s_i$_@_t3sT_p@$$w0rd"}),
                             verify=request.param)
    assert response.status_code == 200
    assert "token" in response.json()
    token = response.json()["token"]
    # create admin account for tests
    response = requests.post(f"https://{API_HOST}/admin/account",
                             headers={"Content-Type": "application/json",
                                      "Authorization": f"Bearer {token}"},
                             data=json.dumps({"username": "test",
                                              "password": "T3st_P@$$w0rd!",
                                              "name": "Test User"}),
                             verify=request.param)
    assert response.status_code == 200
    assert response.json()["success"] == "successfully created new admin account"
    # log in with the new account
    response = requests.post(f"https://{API_HOST}/admin/login",
                             headers={"Content-Type": "application/json"},
                             data=json.dumps({"username": "test",
                                              "password": "T3st_P@$$w0rd!"}),
                             verify=request.param)
    assert response.status_code == 200
    assert "token" in response.json()
    token = response.json()["token"]
    # yield token for tests
    yield token
    # all tests done; delete test admin account
    response = requests.delete(f"https://{API_HOST}/admin/account",
                             headers={"Content-Type": "application/json",
                                      "Authorization": "Bearer " + token},
                             data=json.dumps({"username": "test"}),
                             verify=request.param)
    assert response.status_code == 200
    assert response.json()["success"] == "successfully deleted admin account"


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
    data = {"registrationKey": registrationKey,
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


@pytest.fixture(scope="session")
def sampleJob():
    # create job json
    jobDoc = {"executor": "bash",
              "filename": "hello_world.sh",
              "description": "Test job description. This job is not real.",
              "os": "linux"}
    # create job archive
    with open("/tmp/hello_world.sh", "w+") as f:
        f.write("#!/bin/bash\n\necho Hello world!\n")
    with open("/tmp/manifest.json", "w+") as f:
        f.write(json.dumps(jobDoc))
    with zipfile.ZipFile("/tmp/hello_world.sh.job", "w", zipfile.ZIP_DEFLATED) as a:
        a.write("/tmp/hello_world.sh", arcname="hello_world.sh")
        a.write("/tmp/manifest.json", arcname="manifest.json")
    jobFile = open("/tmp/hello_world.sh.job", "rb")
    job = {"job": (None, json.dumps(jobDoc), "application/json"),
           "file": ("hello_world.sh.job", jobFile, "application/octet-stream")}
    yield job
    # close file handle after tests
    jobFile.close()
    
