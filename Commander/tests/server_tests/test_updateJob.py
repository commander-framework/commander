import io
import json
from os import sep
from tempfile import gettempdir


def testUpdateJob(client, sample_Job, sample_JobFile, sample_Library, sample_valid_JWT):
    # prepare mongomock with relevant sample documents
    jobFile = sample_JobFile  # creates existing job file in temp directory
    library = sample_Library
    library["jobs"].append(sample_Job)
    library.save()
    # update existing job in the library
    data = {"filename": sample_Job["filename"],
            "description": "updated description",
            "file": (io.BytesIO(b"updated content"), "testfile")}
    response = client.patch("/admin/library",
                           headers={"Content-Type": "multipart/form-data",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                           data=data)
    assert response.status_code == 200
    assert response.json["success"] == "successfully updated the job in the library"
    # get library jobs to validate that job saved successfully
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
    assert libraryJobs[0]["description"] == "updated description"
    assert libraryJobs[0]["os"] == sample_Job["os"]
    assert libraryJobs[0]["user"] == sample_Job["user"]
    # make sure timestamp updated
    assert libraryJobs[0]["timeCreated"] > sample_Job["timeCreated"]
    # make sure file saved correctly
    with open(gettempdir()+sep+sample_Job["filename"], "rb") as testfile:
        assert testfile.read() == b"updated content"


def testNoLibraryUpdateJob(client, sample_Job, sample_valid_JWT):
    # update existing job in the library
    data = {"filename": sample_Job["filename"],
            "description": "updated description",
            "file": (io.BytesIO(b"updated content"), "testfile")}
    response = client.patch("/admin/library",
                           headers={"Content-Type": "multipart/form-data",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                           data=data)
    assert response.status_code == 400
    assert response.json["error"] == "there is no job library yet"


def testBadFilenameUpdateJob(client, sample_Job, sample_JobFile, sample_Library, sample_valid_JWT):
    # prepare mongomock with relevant sample documents
    jobFile = sample_JobFile  # creates existing job file in temp directory
    library = sample_Library
    library["jobs"].append(sample_Job)
    library.save()
    # update existing job in the library
    data = {"filename": "not_a_job_filename",
            "description": "updated description",
            "file": (io.BytesIO(b"updated content"), "testfile")}
    response = client.patch("/admin/library",
                           headers={"Content-Type": "multipart/form-data",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                           data=data)
    assert response.status_code == 400
    assert response.json["error"] == "no existing job with that file name"


def testNothingNewUpdateJob(client, sample_Job, sample_JobFile, sample_Library, sample_valid_JWT):
    # prepare mongomock with relevant sample documents
    jobFile = sample_JobFile  # creates existing job file in temp directory
    library = sample_Library
    library["jobs"].append(sample_Job)
    library.save()
    # update existing job in the library
    data = {"filename": sample_Job["filename"]}
    response = client.patch("/admin/library",
                           headers={"Content-Type": "multipart/form-data",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                           data=data)
    assert response.status_code == 400
    assert response.json["error"] == "niether a new file nor a new description was provided"


def testMissingFieldsUpdateJob(client, sample_Job, sample_JobFile, sample_Library, sample_valid_JWT):
    # prepare mongomock with relevant sample documents
    jobFile = sample_JobFile  # creates existing job file in temp directory
    library = sample_Library
    library["jobs"].append(sample_Job)
    library.save()
    # update existing job in the library
    data = {"description": "updated description",
            "file": (io.BytesIO(b"updated content"), "testfile")}
    response = client.patch("/admin/library",
                           headers={"Content-Type": "multipart/form-data",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                           data=data)
    assert response.status_code == 400
    assert response.json["error"] == "request is missing the following parameters: data=['filename']"