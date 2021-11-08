import io
import json
from os import sep
from server import agentDB, adminDB
from tempfile import gettempdir


def testNewJob(client, sample_Job, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
    # add new job to the library
    data = {"job": sample_Job.to_json(),
            "file": (io.BytesIO(b"test content"), "testfile")}
    response = client.post("/admin/library",
                           headers={"Content-Type": "multipart/form-data",
                                    "Auth-Token": sample_valid_Session["authToken"],
                                    "Username": sample_valid_Session["username"]},
                           data=data)
    assert response.status_code == 200
    assert response.json["success"] == "successfully added new executable to the commander library"
    # get library jobs to validate that job saved successfully
    response = client.get("/admin/library",
                           headers={"Content-Type": "application/json",
                                    "Auth-Token": sample_valid_Session["authToken"],
                                    "Username": sample_valid_Session["username"]},
                           data=json.dumps({}))
    assert response.status_code == 200
    libraryDoc = json.loads(response.json["library"])
    libraryJobs = libraryDoc["jobs"]
    assert len(libraryJobs) == 1
    assert libraryJobs[0]["executor"] == sample_Job["executor"]
    assert libraryJobs[0]["filename"] == sample_Job["filename"]
    assert libraryJobs[0]["description"] == sample_Job["description"]
    assert libraryJobs[0]["os"] == sample_Job["os"]
    assert libraryJobs[0]["user"] == sample_Job["user"]
    assert libraryJobs[0]["timeCreated"] == sample_Job["timeCreated"]
    # make sure file saved correctly
    with open(gettempdir()+sep+sample_Job["filename"], "rb") as testfile:
        assert testfile.read() == b"test content"
    # clean up database for next test
    agentDB.drop_database("agents")
    adminDB.drop_database("admins")


def testExpiredSessionNewJob(client, sample_Job, sample_expired_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_expired_Session)
    user.save()
    # add new job to the library
    data = {"job": sample_Job.to_json(),
            "file": (io.BytesIO(b"test content"), "testfile")}
    response = client.post("/admin/library",
                           headers={"Content-Type": "multipart/form-data",
                                    "Auth-Token": sample_expired_Session["authToken"],
                                    "Username": sample_expired_Session["username"]},
                           data=data)
    assert response.status_code == 403
    assert response.json["error"] == "invalid auth token or token expired"
    # clean up database for next test
    agentDB.drop_database("agents")
    adminDB.drop_database("admins")