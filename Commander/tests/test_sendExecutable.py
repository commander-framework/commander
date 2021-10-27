import json
from server import agentDB, adminDB
from utils import utcNowTimestamp


def testGetExecutable(client, sample_Job, sample_JobFile, sample_Agent):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    job = sample_Job
    job.filename = sample_JobFile
    job.timeDispatched = utcNowTimestamp()
    agent["jobsRunning"].append(job)
    agent.save()
    # get job's executable from the api server
    response = client.get("/agent/execute",
                           headers={"Content-Type": "application/json",
                                    "Agent-ID": sample_Agent.agentID},
                           data=json.dumps({"filename": job.filename}))
    assert response.status_code == 200
    responseDisposition = response.headers["Content-Disposition"]
    responseFilename = responseDisposition[responseDisposition.index("filename=") + 9:]
    assert responseFilename == job.filename
    assert response.data == b'test content'
    # clean up database for next test
    agentDB.drop_database("agents")


def testUnknownAgentGetExecutable(client, sample_Job, sample_JobFile, sample_Agent):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    job = sample_Job
    job.filename = sample_JobFile
    job.timeDispatched = utcNowTimestamp()
    agent["jobsRunning"].append(job)
    agent.save()
    # check in with api server
    response = client.get("/agent/execute",
                          headers={"Content-Type": "application/json",
                                    "Agent-ID": "not_an_agent"},
                           data=json.dumps({"filename": job.filename}))
    assert response.status_code == 400
    assert response.json["error"] == "agent ID not found"
    # clean up database for next test
    agentDB.drop_database("agents")


def testNoJobGetExecutable(client, sample_Job, sample_JobFile, sample_Agent):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    job = sample_Job
    job.filename = sample_JobFile
    job.timeDispatched = utcNowTimestamp()
    # intentionally not adding job to agent's jobsRunning list
    agent.save()
    # check in with api server
    response = client.get("/agent/execute",
                          headers={"Content-Type": "application/json",
                                    "Agent-ID": sample_Agent.agentID},
                           data=json.dumps({"filename": job.filename}))
    assert response.status_code == 400
    assert response.json["error"] == "no matching job available for download"
    # clean up database for next test
    agentDB.drop_database("agents")


def testMissingFileGetExecutable(client, sample_Job, sample_JobFile, sample_Agent):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    job = sample_Job
    # intentionally not saving file to job library
    job.timeDispatched = utcNowTimestamp()
    agent["jobsRunning"].append(job)
    agent.save()
    # check in with api server
    response = client.get("/agent/execute",
                          headers={"Content-Type": "application/json",
                                    "Agent-ID": sample_Agent.agentID},
                           data=json.dumps({"filename": job.filename}))
    assert response.status_code == 500
    assert response.json["error"] == "job file missing -- please contact an administrator"
    # clean up database for next test
    agentDB.drop_database("agents")