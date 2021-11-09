import json
from utils import timestampToDatetime


def testNoJobsCheckin(client, sample_Agent):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    agent.save()
    # check in with api server
    response = client.get("/agent/jobs",
                          headers={"Content-Type": "application/json",
                                    "Agent-ID": sample_Agent["agentID"]})
    assert response.status_code == 204


def testAvailableJobCheckin(client, sample_Agent, sample_Job):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    agent["jobsQueue"].append(sample_Job)
    agent.save()
    # check in with api server
    response = client.get("/agent/jobs",
                          headers={"Content-Type": "application/json",
                                    "Agent-ID": sample_Agent["agentID"]})
    assert response.status_code == 200
    # make sure all job fields were included from the sample job
    assert json.loads(response.json["job"])["executor"] == sample_Job["executor"]
    assert json.loads(response.json["job"])["filename"] == sample_Job["filename"]
    assert json.loads(response.json["job"])["description"] == sample_Job["description"]
    assert json.loads(response.json["job"])["os"] == sample_Job["os"]
    assert json.loads(response.json["job"])["user"] == sample_Job["user"]
    createdTimestamp = json.loads(response.json["job"])["timeCreated"]
    createdTime = timestampToDatetime(createdTimestamp)
    assert createdTime == timestampToDatetime(sample_Job["timeCreated"])
    # make sure timeDispatched was created
    dispatchTimestamp = json.loads(response.json["job"])["timeDispatched"]
    dispatchTime = timestampToDatetime(dispatchTimestamp)
    assert dispatchTime >= createdTime


def testMissingFieldsCheckin(client, sample_Agent):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    agent.save()
    # check in with api server
    response = client.get("/agent/jobs",
                          headers={"Content-Type": "application/json"})
    assert response.status_code == 400
    assert response.json["error"] == "request is missing the following parameters: headers=['Agent-ID']"


def testUnknownAgentCheckin(client, sample_Agent):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    agent.save()
    # check in with api server
    response = client.get("/agent/jobs",
                          headers={"Content-Type": "application/json",
                                    "Agent-ID": "not_an_agent"})
    assert response.status_code == 400
    assert response.json["error"] == "agent ID not found"