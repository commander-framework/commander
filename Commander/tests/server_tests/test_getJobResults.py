from datetime import datetime
import json
from utils import utcNowTimestamp, timestampToDatetime


def testGetResults(client, sample_Job, sample_Agent, sample_valid_JWT):
    # prepare mongomock with relevant sample documents
    job = sample_Job
    job["timeDispatched"] = utcNowTimestamp()
    job.argv = ["-o", "output.txt", "-i", "input.txt"]
    job["timeStarted"] = utcNowTimestamp()
    job["status"] = 0
    job["stdout"] = "stdout"
    job["stderr"] = "stderr"
    job["timeEnded"] = utcNowTimestamp()
    agent = sample_Agent
    agent["jobsHistory"].append(job)
    agent.save()
    # get finished jobs for sample agent from the api server
    response = client.get("/agent/history",
                           headers={"Content-Type": "application/json",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                           data=json.dumps({"agentID": sample_Agent["agentID"]}))
    assert response.status_code == 200
    # make sure all job fields were included from the sample job
    assert len(jobsHistory := response.json["jobs"]) == 1
    finishedJob = json.loads(jobsHistory[0])
    assert finishedJob["executor"] == job["executor"]
    assert finishedJob["filename"] == job["filename"]
    assert finishedJob["description"] == job["description"]
    assert finishedJob["os"] == job["os"]
    assert finishedJob["user"] == job["user"]
    timeCreated = timestampToDatetime(job["timeCreated"])
    timeDispatched = timestampToDatetime(job["timeDispatched"])
    timeStarted = timestampToDatetime(job["timeStarted"])
    timeEnded = timestampToDatetime(job["timeEnded"])
    assert datetime.utcnow() >= timeCreated
    assert timeDispatched >= timeCreated
    assert timeStarted >= timeDispatched
    assert timeEnded >= timeStarted
    assert finishedJob["argv"] == job["argv"]
    assert finishedJob["status"] == job["status"]
    assert finishedJob["stdout"] == job["stdout"]
    assert finishedJob["stderr"] == job["stderr"]


def testNoJobsGetResults(client, sample_Agent, sample_valid_JWT):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    # intentionally not adding job to agent history
    agent.save()
    # get finished jobs for sample agent from the api server
    response = client.get("/agent/history",
                           headers={"Content-Type": "application/json",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                           data=json.dumps({"agentID": sample_Agent["agentID"]}))
    assert response.status_code == 200
    # make sure all job fields were included from the sample job
    assert len(response.json["jobs"]) == 0


def testUnknownAgentGetResults(client, sample_Job, sample_Agent, sample_valid_JWT):
    # prepare mongomock with relevant sample documents
    job = sample_Job
    job["timeDispatched"] = utcNowTimestamp()
    job.argv = ["-o", "output.txt", "-i", "input.txt"]
    job["timeStarted"] = utcNowTimestamp()
    job["status"] = 0
    job["stdout"] = "stdout"
    job["stderr"] = "stderr"
    job["timeEnded"] = utcNowTimestamp()
    agent = sample_Agent
    agent["jobsHistory"].append(job)
    agent.save()
    # get finished jobs for sample agent from the api server
    response = client.get("/agent/history",
                           headers={"Content-Type": "application/json",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                           data=json.dumps({"agentID": "not_an_agent"}))
    assert response.status_code == 400
    assert response.json["error"] == "agent ID not found"


def testMissingFieldsGetResults(client, sample_Job, sample_Agent, sample_valid_JWT):
    # prepare mongomock with relevant sample documents
    job = sample_Job
    job["timeDispatched"] = utcNowTimestamp()
    job.argv = ["-o", "output.txt", "-i", "input.txt"]
    job["timeStarted"] = utcNowTimestamp()
    job["status"] = 0
    job["stdout"] = "stdout"
    job["stderr"] = "stderr"
    job["timeEnded"] = utcNowTimestamp()
    agent = sample_Agent
    agent["jobsHistory"].append(job)
    agent.save()
    # get finished jobs for sample agent from the api server
    response = client.get("/agent/history",
                           headers={"Content-Type": "application/json",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                           data=json.dumps({}))
    assert response.status_code == 400
    assert response.json["error"] == "request is missing the following parameters: data=['agentID']"
