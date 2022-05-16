from datetime import datetime
import json
from server import jobsCache
from server.routes import agentCheckin
from utils import timestampToDatetime


class MockServer:
    def __init__(self, agentID):
        self.lastMessage = None
        self.agentID = agentID
        self.sock = self
        self.isMockServer = True
    def send(self, msg):
        self.lastMessage = msg
    def receive(self):
        if not self.lastMessage:
            if self.agentID == "bad-request":
                # send invalid json
                return "bad-request"
            elif self.agentID == "missing-fields":
                # leave out required Agent-ID field
                return json.dumps({"test": "missing-fields"})
            # send given Agent ID in valid json format
            return json.dumps({"Agent-ID": self.agentID})
        else:
            # response to a job being assigned to the endpoint
            return "ack"
    def close(self, *args, **kwargs):
        return
    def getpeername(self):
        return "mock-server"


def testAvailableJobCheckin(sample_Agent, sample_Job):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    agent["jobsQueue"].append(sample_Job)
    agent.save()
    jobsCache.refresh()  # because we added the job to the DB manually
    # check in with api server
    agentCheckin.__wrapped__(MockServer(agent["agentID"]))
    # make sure all job fields were included from the sample job
    agent.reload()
    job = agent.jobsRunning[0]
    assert job["executor"] == sample_Job["executor"]
    assert job["filename"] == sample_Job["filename"]
    assert job["description"] == sample_Job["description"]
    assert job["os"] == sample_Job["os"]
    assert job["user"] == sample_Job["user"]
    createdTimestamp = job["timeCreated"]
    createdTime = timestampToDatetime(createdTimestamp)
    assert createdTime == timestampToDatetime(sample_Job["timeCreated"])
    # make sure timeDispatched was created
    dispatchTimestamp = job["timeDispatched"]
    dispatchTime = timestampToDatetime(dispatchTimestamp)
    assert dispatchTime >= createdTime
    # make sure lastCheckin was created
    assert timestampToDatetime(agent["lastCheckin"]) <= datetime.utcnow()


def testBadRequestCheckin(sample_Agent):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    agent.save()
    # check in with api server
    error = agentCheckin.__wrapped__(MockServer("bad-request"))
    assert error["error"] == "message was not a valid json object"


def testMissingFieldsCheckin(sample_Agent):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    agent.save()
    # check in with api server
    error = agentCheckin.__wrapped__(MockServer("missing-fields"))
    assert error["error"] == "request is missing the following parameters: headers=['Agent-ID']"


def testUnknownAgentCheckin(sample_Agent):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    agent.save()
    # check in with api server
    error = agentCheckin.__wrapped__(MockServer("not-a-real-agent"))
    assert error["error"] == "agent ID not found, please check ID or register"