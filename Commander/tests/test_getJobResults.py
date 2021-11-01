from datetime import datetime
import json
from server import agentDB, adminDB
from utils import utcNowTimestamp, timestampToDatetime


def testGetResults(client, sample_Job, sample_Agent, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
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
    # clean up database for next test
    agentDB.drop_database("agents")
    adminDB.drop_database("admins")