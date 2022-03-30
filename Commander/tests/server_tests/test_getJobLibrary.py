import json


def testGetLibary(client, sample_Job, sample_Library, sample_valid_JWT):
    # prepare mongomock with relevant sample documents
    library = sample_Library
    library["jobs"].append(sample_Job)
    library.save()
    # get list of available jobs in the library
    response = client.get("/admin/library",
                           headers={"Content-Type": "application/json",
                                    "Authorization": "Bearer " + sample_valid_JWT},
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


def testNoJobsGetLibary(client, sample_valid_JWT):
    # intentionally not creating library
    # get list of available jobs in the library
    response = client.get("/admin/library",
                           headers={"Content-Type": "application/json",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                           data=json.dumps({}))
    assert response.status_code == 204