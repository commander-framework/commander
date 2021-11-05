import io
import json
from server import agentDB, adminDB


def testAssignJob(client, sample_Job, sample_valid_Session, sample_User):
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
    # clean up database for next test
    agentDB.drop_database("agents")
    adminDB.drop_database("admins")