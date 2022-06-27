import io
import json
from os import sep
from tempfile import gettempdir


def testNewJob(client, sample_Job, sample_valid_JWT):
    # add new job to the library
    data = {"job": sample_Job.to_json(),
            "file": (io.BytesIO(b"test content"), "testfile")}
    response = client.post("/admin/library",
                           headers={"Content-Type": "multipart/form-data",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                           data=data)
    assert response.status_code == 200
    assert response.json["success"] == "successfully added new executable to the commander library"
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
    assert libraryJobs[0]["description"] == sample_Job["description"]
    assert libraryJobs[0]["os"] == sample_Job["os"]
    assert libraryJobs[0]["user"] == "testuser"
    # make sure file saved correctly
    with open(gettempdir()+sep+sample_Job["filename"], "rb") as testfile:
        assert testfile.read() == b"test content"


def testMissingFileNewJob(client, sample_Job, sample_valid_JWT):
    # add new job to the library
    data = {"job": sample_Job.to_json(),
            "file": "testfile"}
    response = client.post("/admin/library",
                           headers={"Content-Type": "multipart/form-data",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                           data=data)
    assert response.status_code == 400
    assert response.json["error"] == "file not uploaded with request"


def testMissingJobFieldNewJob(client, sample_Job, sample_valid_JWT):
    # prepare mongomock sample document
    job = json.loads(sample_Job.to_json())
    job.pop("executor")
    job.pop("filename")
    job.pop("description")
    job.pop("os")
    # add new job to the library
    data = {"job": json.dumps(job),
            "file": (io.BytesIO(b"test content"), "testfile")}
    response = client.post("/admin/library",
                           headers={"Content-Type": "multipart/form-data",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                           data=data)
    assert response.status_code == 400
    assert response.json["error"] == "the job in the request is missing the following fields: ['executor', 'filename', 'description', 'os']"


def testDuplicateNewJob(client, sample_Job, sample_valid_JWT):
    # add new job to the library
    data = {"job": sample_Job.to_json(),
            "file": (io.BytesIO(b"test content"), "testfile")}
    response = client.post("/admin/library",
                           headers={"Content-Type": "multipart/form-data",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                           data=data)
    assert response.status_code == 200
    assert response.json["success"] == "successfully added new executable to the commander library"
    # add same job document with a new file to test error
    data = {"job": sample_Job.to_json(),
            "file": (io.BytesIO(b"test content 2"), "testfile2")}
    response = client.post("/admin/library",
                           headers={"Content-Type": "multipart/form-data",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                           data=data)
    assert response.status_code == 400
    assert response.json["error"] == "file name already exists in the library"


def testMissingFieldsNewJob(client, sample_valid_JWT):
    # add new job to the library
    response = client.post("/admin/library",
                           headers={"Content-Type": "multipart/form-data",
                                    "Authorization": "Bearer " + sample_valid_JWT},
                           data=json.dumps({}))
    assert response.status_code == 400
    assert response.json["error"] == "request is missing the following parameters: data=['job', 'file']"