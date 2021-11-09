import json


def testNoJobsGetLibary(client, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
    # intentionally not creating library
    # get list of available jobs in the library
    response = client.get("/admin/library",
                           headers={"Content-Type": "application/json",
                                    "Auth-Token": sample_valid_Session["authToken"],
                                    "Username": sample_valid_Session["username"]},
                           data=json.dumps({}))
    assert response.status_code == 204


def testGetLibary(client, sample_Job, sample_Library, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
    library = sample_Library
    library["jobs"].append(sample_Job)
    library.save()
    # get list of available jobs in the library
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


def testExpiredSessionGetLibary(client, sample_Job, sample_Library, sample_expired_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_expired_Session)
    user.save()
    library = sample_Library
    library["jobs"].append(sample_Job)
    library.save()
    # get list of available jobs in the library
    response = client.get("/admin/library",
                           headers={"Content-Type": "application/json",
                                    "Auth-Token": sample_expired_Session["authToken"],
                                    "Username": sample_expired_Session["username"]},
                           data=json.dumps({}))
    assert response.status_code == 401
    assert response.json["error"] == "invalid auth token or token expired"


def testMissingFieldsGetLibary(client, sample_Job, sample_Library, sample_valid_Session, sample_User):
    # prepare mongomock with relevant sample documents
    user = sample_User
    user["sessions"].append(sample_valid_Session)
    user.save()
    library = sample_Library
    library["jobs"].append(sample_Job)
    library.save()
    # get list of available jobs in the library
    response = client.get("/admin/library",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps({}))
    assert response.status_code == 400
    assert response.json["error"] == "request is missing the following parameters: headers=['Auth-Token', 'Username']"