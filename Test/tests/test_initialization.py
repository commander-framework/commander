import pytest
import requests


@pytest.mark.order(0)
def test_adminCreation():
    pass


@pytest.mark.order(1)
def test_createRegistrationKey():
    pass


@pytest.mark.order(2)
def test_getRegistrationKey():
    pass


@pytest.mark.order(3)
def test_agentRegistration():
    certPath = "/app/ca/certs/proxy/proxy.crt"
    keyPath = "/app/ca/certs/proxy/proxy.pem"
    caPath = "/app/ca/capy/ca.crt"
    cert = (certPath, keyPath)
    url = "https://localhost/agent/jobs"
    headers = {"Content-Type": "application/json"}
    data = {"agentID": "agent1", "groups": ["group1"]}

    response = requests.post(url,
                             headers=headers,
                             data=data,
                             verify=caPath,
                             cert=cert)

    print(response.status_code, response.json())


@pytest.mark.order(4)
def test_createJob():
    pass