import json
from server.models import Agent


def testRegisterAgent(client, sample_RegistrationKey, sample_Agent):
    # prepare mongomock with relevant sample documents
    regKey = sample_RegistrationKey
    regKey.save()
    # send job results to the api server
    response = client.post("/agent/register",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps({"registrationKey": sample_RegistrationKey["regKey"],
                                            "hostname": sample_Agent["hostname"],
                                            "os": sample_Agent["os"]}))
    assert response.status_code == 200
    assert "agentID" in response.json
    # make sure agent was saved to the db
    agentQuery = Agent.objects().get()
    assert agentQuery


def testNoRegKeyRegisterAgent(client, sample_RegistrationKey, sample_Agent):
    # intentionally not saving reg key to db
    # send job results to the api server
    response = client.post("/agent/register",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps({"registrationKey": sample_RegistrationKey["regKey"],
                                            "hostname": sample_Agent["hostname"],
                                            "os": sample_Agent["os"]}))
    assert response.status_code == 500
    assert response.json["error"] == "no registration key has been generated yet"


def testBadKeyRegisterAgent(client, sample_RegistrationKey, sample_Agent):
    # prepare mongomock with relevant sample documents
    regKey = sample_RegistrationKey
    regKey.save()
    # send job results to the api server
    response = client.post("/agent/register",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps({"registrationKey": "not_a_valid_regkey",
                                            "hostname": sample_Agent["hostname"],
                                            "os": sample_Agent["os"]}))
    assert response.status_code == 401
    assert response.json["error"] == "invalild registration key"


def testMissingFieldsRegisterAgent(client, sample_RegistrationKey):
    # prepare mongomock with relevant sample documents
    regKey = sample_RegistrationKey
    regKey.save()
    # send job results to the api server
    response = client.post("/agent/register",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps({}))
    assert response.status_code == 400
    assert response.json["error"] == "request is missing the following parameters: data=['registrationKey', 'hostname', 'os']"