import json
from utils import timestampToDatetime


def testAssignJob(client, sample_Job, sample_Library, sample_Agent, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
    agent = sample_Agent
    agent.save()
    library = sample_Library
    library["jobs"].append(sample_Job)
    library.save()
    # send job to api
    response = client.post("/agent/jobs",
                           headers={"Content-Type": "application/json",
                                    "Auth-Token": sample_valid_Session["authToken"],
                                    "Username": sample_valid_Session["username"]},
                           data=json.dumps({"agentID": sample_Agent["agentID"],
                                 "filename": sample_Job["filename"],
                                 "argv": []}))
    assert response.status_code == 200
    assert response.json["success"] == "job successfully submitted -- waiting for agent to check in"
    # check in and make sure job is in agent's queue now
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
    assert json.loads(response.json["job"])["argv"] == []
    # make sure timeCreated was updated when the job was assigned
    createdTimestamp = json.loads(response.json["job"])["timeCreated"]
    createdTime = timestampToDatetime(createdTimestamp)
    assert createdTime >= timestampToDatetime(sample_Job["timeCreated"])
    # make sure timeDispatched was created
    dispatchTimestamp = json.loads(response.json["job"])["timeDispatched"]
    dispatchTime = timestampToDatetime(dispatchTimestamp)
    assert dispatchTime >= createdTime


def testExpiredSessionAssignJob(client, sample_Job, sample_Library, sample_Agent, sample_expired_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_expired_Session)
    user.save()
    agent = sample_Agent
    agent.save()
    library = sample_Library
    library["jobs"].append(sample_Job)
    library.save()
    # send job to api
    response = client.post("/agent/jobs",
                           headers={"Content-Type": "application/json",
                                    "Auth-Token": sample_expired_Session["authToken"],
                                    "Username": sample_expired_Session["username"]},
                           data=json.dumps({"agentID": sample_Agent["agentID"],
                                 "filename": sample_Job["filename"],
                                 "argv": []}))
    assert response.status_code == 401
    assert response.json["error"] == "invalid auth token or token expired"


def testNoLibraryAssignJob(client, sample_Job, sample_Agent, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
    agent = sample_Agent
    agent.save()
    # intentionally not creating a library document in the database
    # send job to api
    response = client.post("/agent/jobs",
                           headers={"Content-Type": "application/json",
                                    "Auth-Token": sample_valid_Session["authToken"],
                                    "Username": sample_valid_Session["username"]},
                           data=json.dumps({"agentID": sample_Agent["agentID"],
                                 "filename": sample_Job["filename"],
                                 "argv": []}))
    assert response.status_code == 400
    assert response.json["error"] == "there are no jobs in the library yet"


def testJobMissingAssignJob(client, sample_Job, sample_Library, sample_Agent, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
    agent = sample_Agent
    agent.save()
    library = sample_Library
    # intentionally not adding sample_Job to the library
    library.save()
    # send job to api
    response = client.post("/agent/jobs",
                           headers={"Content-Type": "application/json",
                                    "Auth-Token": sample_valid_Session["authToken"],
                                    "Username": sample_valid_Session["username"]},
                           data=json.dumps({"agentID": sample_Agent["agentID"],
                                 "filename": sample_Job["filename"],
                                 "argv": []}))
    assert response.status_code == 400
    assert response.json["error"] == "the library contains no executable with the given filename"


def testBadAgentIDAssignJob(client, sample_Job, sample_Library, sample_Agent, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
    # intentionally not adding agent document to the library
    library = sample_Library
    library["jobs"].append(sample_Job)
    library.save()
    # send job to api
    response = client.post("/agent/jobs",
                           headers={"Content-Type": "application/json",
                                    "Auth-Token": sample_valid_Session["authToken"],
                                    "Username": sample_valid_Session["username"]},
                           data=json.dumps({"agentID": sample_Agent["agentID"],
                                 "filename": sample_Job["filename"],
                                 "argv": []}))
    assert response.status_code == 400
    assert response.json["error"] == "no hosts found matching the agentID in the request"


def testMissingFieldsAssignJob(client, sample_Job, sample_Library, sample_Agent, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
    agent = sample_Agent
    agent.save()
    library = sample_Library
    library["jobs"].append(sample_Job)
    library.save()
    # send job to api
    response = client.post("/agent/jobs",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps({}))
    assert response.status_code == 400
    assert response.json["error"] == "request is missing the following parameters: headers=['Auth-Token', 'Username'], data=['agentID', 'filename', 'argv']"