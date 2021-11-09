import json


def testDeleteJob(client, sample_Job, sample_JobFile, sample_Library, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
    jobFile = sample_JobFile  # creates existing job file in temp directory
    library = sample_Library
    library["jobs"].append(sample_Job)
    library.save()
    # delete job from the library
    response = client.delete("/admin/library",
                           headers={"Content-Type": "application/json",
                                    "Auth-Token": sample_valid_Session["authToken"],
                                    "Username": sample_valid_Session["username"]},
                           data=json.dumps({"filename": sample_Job["filename"]}))
    assert response.status_code == 200
    assert response.json["success"] == "successfully deleted the job from the library"
    # get library jobs to validate that job was deleted successfully
    response = client.get("/admin/library",
                           headers={"Content-Type": "application/json",
                                    "Auth-Token": sample_valid_Session["authToken"],
                                    "Username": sample_valid_Session["username"]},
                           data=json.dumps({}))
    assert response.status_code == 204


def testExpiredSessionDeleteJob(client, sample_Job, sample_JobFile, sample_Library, sample_expired_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_expired_Session)
    user.save()
    jobFile = sample_JobFile  # creates existing job file in temp directory
    library = sample_Library
    library["jobs"].append(sample_Job)
    library.save()
    # delete job from the library
    response = client.delete("/admin/library",
                           headers={"Content-Type": "application/json",
                                    "Auth-Token": sample_expired_Session["authToken"],
                                    "Username": sample_expired_Session["username"]},
                           data=json.dumps({"filename": sample_Job["filename"]}))
    assert response.status_code == 401
    assert response.json["error"] == "invalid auth token or token expired"


def testNoLibraryDeleteJob(client, sample_Job, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
    # delete job from the library
    response = client.delete("/admin/library",
                           headers={"Content-Type": "application/json",
                                    "Auth-Token": sample_valid_Session["authToken"],
                                    "Username": sample_valid_Session["username"]},
                           data=json.dumps({"filename": sample_Job["filename"]}))
    assert response.status_code == 400
    assert response.json["error"] == "there are no jobs in the library yet"


def testBadFilenameDeleteJob(client, sample_Job, sample_JobFile, sample_Library, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
    jobFile = sample_JobFile  # creates existing job file in temp directory
    library = sample_Library
    library["jobs"].append(sample_Job)
    library.save()
    # delete job from the library
    response = client.delete("/admin/library",
                           headers={"Content-Type": "application/json",
                                    "Auth-Token": sample_valid_Session["authToken"],
                                    "Username": sample_valid_Session["username"]},
                           data=json.dumps({"filename": "not_a_job_filename"}))
    assert response.status_code == 400
    assert response.json["error"] == "no existing job with that file name"


def testMissingFieldsDeleteJob(client, sample_Job, sample_JobFile, sample_Library, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
    jobFile = sample_JobFile  # creates existing job file in temp directory
    library = sample_Library
    library["jobs"].append(sample_Job)
    library.save()
    # delete job from the library
    response = client.delete("/admin/library",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps({}))
    assert response.status_code == 400
    assert response.json["error"] == "request is missing the following parameters: headers=['Auth-Token', 'Username'], data=['filename']"