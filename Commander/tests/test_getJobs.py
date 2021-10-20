from datetime import datetime, timedelta
import json
from server import agentDB


def testCheckinWithNoJobs(client, sample_Agent):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    agent.save()
    # check in with api server
    response = client.get("/agent/jobs",
                          headers={"Content-Type": "application/json",
                                    "Agent-ID": "123456789"})
    assert response.status_code == 200
    assert response.json["job"] == "no jobs"
    agentDB.drop_database("agents")


def testCheckinWithJobs(client, sample_Agent, sample_Job):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    agent["jobsQueue"].append(sample_Job)
    agent.save()
    # check in with api server
    response = client.get("/agent/jobs",
                          headers={"Content-Type": "application/json",
                                    "Agent-ID": "123456789"})
    assert response.status_code == 200
    assert json.loads(response.json["job"])["executor"] == sample_Job["executor"]
    assert json.loads(response.json["job"])["filename"] == sample_Job["filename"]
    assert json.loads(response.json["job"])["description"] == sample_Job["description"]
    assert json.loads(response.json["job"])["os"] == sample_Job["os"]
    assert json.loads(response.json["job"])["user"] == sample_Job["user"]
    createdTimestamp = json.loads(response.json["job"])["timeCreated"]["$date"]/1000
    createdTime = datetime.fromtimestamp(createdTimestamp, None)
    assert timedelta(milliseconds=0) > (sample_Job["timeCreated"] - createdTime)
    dispatchTimestamp = json.loads(response.json["job"])["timeDispatched"]["$date"]/1000
    assert datetime.fromtimestamp(dispatchTimestamp, None) == sample_Job["timeDispatched"]
    agentDB.drop_database("agents")