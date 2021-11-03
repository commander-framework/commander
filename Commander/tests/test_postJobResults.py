from datetime import datetime
import json
from server import agentDB, adminDB
from utils import utcNowTimestamp, timestampToDatetime


def testPostResults(client, sample_Job, sample_Agent, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
    agent = sample_Agent
    job = sample_Job
    job["timeDispatched"] = utcNowTimestamp()
    job.argv = ["-o", "output.txt", "-i", "input.txt"]
    agent["jobsRunning"].append(job)
    job["timeStarted"] = utcNowTimestamp()
    job["status"] = 0
    job["stdout"] = "stdout"
    job["stderr"] = "stderr"
    job["timeEnded"] = utcNowTimestamp()
    agent.save()
    # send job results to the api server
    response = client.post("/agent/history",
                           headers={"Content-Type": "application/json",
                                    "Agent-ID": sample_Agent["agentID"]},
                           data=json.dumps({"job": job.to_json()}))
    assert response.status_code == 200
    assert response.json["success"] == "successfully saved job response"
    # get finished jobs for the sample agent from the api server
    response = client.get("/agent/history",
                           headers={"Content-Type": "application/json",
                                    "Auth-Token": sample_valid_Session["authToken"],
                                    "Username": sample_valid_Session["username"]},
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
    # post results again to verify that job was deleted from running queue
    response = client.post("/agent/history",
                           headers={"Content-Type": "application/json",
                                    "Agent-ID": sample_Agent["agentID"]},
                           data=json.dumps({"job": job.to_json()}))
    assert response.status_code == 400
    assert response.json["error"] == "no matching jobs were supposed to be running"
    # clean up database for next test
    agentDB.drop_database("agents")
    adminDB.drop_database("admins")


def testUnknownAgentPostResults(client, sample_Job, sample_Agent, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
    agent = sample_Agent
    job = sample_Job
    job["timeDispatched"] = utcNowTimestamp()
    job.argv = ["-o", "output.txt", "-i", "input.txt"]
    agent["jobsRunning"].append(job)
    job["timeStarted"] = utcNowTimestamp()
    job["status"] = 0
    job["stdout"] = "stdout"
    job["stderr"] = "stderr"
    job["timeEnded"] = utcNowTimestamp()
    agent.save()
    # send job results to the api server
    response = client.post("/agent/history",
                           headers={"Content-Type": "application/json",
                                    "Agent-ID": "not_an_agent"},
                           data=json.dumps({"job": job.to_json()}))
    assert response.status_code == 400
    assert response.json["error"] == "agent ID not found"
    # clean up database for next test
    agentDB.drop_database("agents")
    adminDB.drop_database("admins")


def testMissingJobPostResults(client, sample_Job, sample_Agent, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
    agent = sample_Agent
    job = sample_Job
    job["timeDispatched"] = utcNowTimestamp()
    job.argv = ["-o", "output.txt", "-i", "input.txt"]
    # intentionally not adding job to agent's running queue
    job["timeStarted"] = utcNowTimestamp()
    job["status"] = 0
    job["stdout"] = "stdout"
    job["stderr"] = "stderr"
    job["timeEnded"] = utcNowTimestamp()
    agent.save()
    # send job results to the api server
    response = client.post("/agent/history",
                           headers={"Content-Type": "application/json",
                                    "Agent-ID": sample_Agent["agentID"]},
                           data=json.dumps({"job": job.to_json()}))
    assert response.status_code == 400
    assert response.json["error"] == "no matching jobs were supposed to be running"
    # clean up database for next test
    agentDB.drop_database("agents")
    adminDB.drop_database("admins")


def testMissingFieldsPostResults(client, sample_Job, sample_Agent, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
    agent = sample_Agent
    job = sample_Job
    job["timeDispatched"] = utcNowTimestamp()
    job.argv = ["-o", "output.txt", "-i", "input.txt"]
    agent["jobsRunning"].append(job)
    job["timeStarted"] = utcNowTimestamp()
    job["status"] = 0
    job["stdout"] = "stdout"
    job["stderr"] = "stderr"
    job["timeEnded"] = utcNowTimestamp()
    agent.save()
    # send job results to the api server
    response = client.post("/agent/history",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps({}))
    assert response.status_code == 400
    assert response.json["error"] == "request is missing one or more of the following parameters: headers=['Agent-ID'], data=['job']"
    # clean up database for next test
    agentDB.drop_database("agents")
    adminDB.drop_database("admins")