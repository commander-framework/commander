from datetime import datetime
import json
from utils import utcNowTimestamp, timestampToDatetime


def testPostResults(client, sample_Job, sample_Agent, sample_valid_JWT):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    job = sample_Job
    job["timeDispatched"] = utcNowTimestamp()
    job.argv = ["-o", "output.txt", "-i", "input.txt"]
    agent["jobsRunning"].append(job)
    job["timeStarted"] = utcNowTimestamp()
    job["exitCode"] = 0
    job["stdout"] = "stdout"
    job["stderr"] = "stderr"
    job["timeEnded"] = utcNowTimestamp()
    agent.save()
    # send job results to the api server
    response = client.post("/agent/history",
                           headers={"Content-Type": "application/json",
                                    "Agent-ID": sample_Agent["agentID"]},
                           data=json.dumps({"job": json.loads(job.to_json())}))
    assert response.status_code == 200
    assert response.json["success"] == "successfully saved job response"
    # get finished jobs for the sample agent from the api server
    response = client.get("/admin/history",
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
    assert finishedJob["exitCode"] == job["exitCode"]
    assert finishedJob["stdout"] == job["stdout"]
    assert finishedJob["stderr"] == job["stderr"]
    # post results again to verify that job was deleted from running queue
    response = client.post("/agent/history",
                           headers={"Content-Type": "application/json",
                                    "Agent-ID": sample_Agent["agentID"]},
                           data=json.dumps({"job": json.loads(job.to_json())}))
    assert response.status_code == 400
    assert response.json["error"] == "no matching jobs were supposed to be running"


def testUnknownAgentPostResults(client, sample_Job, sample_Agent):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    job = sample_Job
    job["timeDispatched"] = utcNowTimestamp()
    job.argv = ["-o", "output.txt", "-i", "input.txt"]
    agent["jobsRunning"].append(job)
    job["timeStarted"] = utcNowTimestamp()
    job["exitCode"] = 0
    job["stdout"] = "stdout"
    job["stderr"] = "stderr"
    job["timeEnded"] = utcNowTimestamp()
    agent.save()
    # send job results to the api server
    response = client.post("/agent/history",
                           headers={"Content-Type": "application/json",
                                    "Agent-ID": "not_an_agent"},
                           data=json.dumps({"job": json.loads(job.to_json())}))
    assert response.status_code == 400
    assert response.json["error"] == "agent ID not found"


def testMissingJobPostResults(client, sample_Job, sample_Agent):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    job = sample_Job
    job["timeDispatched"] = utcNowTimestamp()
    job.argv = ["-o", "output.txt", "-i", "input.txt"]
    # intentionally not adding job to agent's running queue
    job["timeStarted"] = utcNowTimestamp()
    job["exitCode"] = 0
    job["stdout"] = "stdout"
    job["stderr"] = "stderr"
    job["timeEnded"] = utcNowTimestamp()
    agent.save()
    # send job results to the api server
    response = client.post("/agent/history",
                           headers={"Content-Type": "application/json",
                                    "Agent-ID": sample_Agent["agentID"]},
                           data=json.dumps({"job": json.loads(job.to_json())}))
    assert response.status_code == 400
    assert response.json["error"] == "no matching jobs were supposed to be running"


def testMissingFieldsPostResults(client, sample_Job, sample_Agent):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    job = sample_Job
    job["timeDispatched"] = utcNowTimestamp()
    job.argv = ["-o", "output.txt", "-i", "input.txt"]
    agent["jobsRunning"].append(job)
    job["timeStarted"] = utcNowTimestamp()
    job["exitCode"] = 0
    job["stdout"] = "stdout"
    job["stderr"] = "stderr"
    job["timeEnded"] = utcNowTimestamp()
    agent.save()
    # send job results to the api server
    response = client.post("/agent/history",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps({}))
    assert response.status_code == 400
    assert response.json["error"] == "request is missing the following parameters: headers=['Agent-ID'], data=['job']"