import asyncio
import json
import os
import pytest
import requests
import ssl
import subprocess
from utils import utcNowTimestamp
import websockets
from zipfile import ZipFile


API_HOST = os.environ.get("API_HOST", "nginx")


async def checkin(caPath, cert, agentID):
    sslContext = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    sslContext.load_verify_locations(caPath)
    sslContext.load_cert_chain(certfile=cert[0], keyfile=cert[1])
    async with websockets.connect("wss://{API_HOST}/agent/checkin",
                                  ssl=sslContext) as ws:
        await ws.send(json.dumps({"Agent-ID": agentID}))
        jobs = await asyncio.wait_for(ws.recv(), timeout=2)
        if jobs:
            await ws.send("ack")
    return jobs



@pytest.mark.order(3)
def test_createJob(caPath, adminJWT, sampleJob):
    # add new job to the library
    response = requests.post(f"https://{API_HOST}/admin/library",
                            headers={"Content-Type": "multipart/form-data",
                                     "Authorization": f"Bearer {adminJWT}"},
                            data=sampleJob,
                            verify=caPath)
    assert response.status_code == 200
    assert response.json()["success"] == "successfully added new executable to the commander library"


@pytest.mark.order(4)
def test_agentCheckinNoJob(caPath, cert, agentID):
    # checkin for jobs (timeout after 2 seconds)
    jobs = asyncio.run(checkin(caPath, cert, agentID))
    assert jobs == None


@pytest.mark.order(5)
def test_assignJob(caPath, adminJWT, agentID):
    # send job to api
    response = requests.post(f"https://{API_HOST}/admin/jobs",
                            headers={"Content-Type": "application/json",
                                    "Authorization": "Bearer " + adminJWT},
                            data=json.dumps({"agentID": agentID,
                                            "filename": "hello_world.sh",
                                            "argv": []}),
                            verify=caPath)
    assert response.status_code == 200
    assert response.json["success"] == "job successfully submitted -- waiting for agent to check in"


@pytest.mark.order(6)
def test_fetchAndExecuteJob(caPath, cert, agentID):
    # get the assigned job from the server
    jobs = json.loads(asyncio.run(checkin(caPath, cert, agentID)))
    assert len(jobs) == 1
    job = jobs[0]
    assert job["executor"] == "bash"
    assert job["filename"] == "hello_world.sh"
    assert job["description"] == "Test job description. This job is not real."
    assert job["os"] == "linux"
    # get job's executable from the api server
    response = requests.get(f"https://{API_HOST}/agent/execute",
                           headers={"Content-Type": "application/json",
                                    "Agent-ID": agentID},
                           data=json.dumps({"filename": job.filename}),
                           verify=caPath,
                           cert=cert)
    assert response.status_code == 200
    responseDisposition = response.headers["Content-Disposition"]
    responseFilename = responseDisposition[responseDisposition.index("filename=") + 9:]
    assert responseFilename == job.filename
    with open(f"/tmp/{job.filename}.job", "wb") as f:
        f.write(response.data)
    with ZipFile(f"/tmp/{job.filename}.job", "r") as jobArchive:
        jobArchive.extractall(f"/tmp/{job.jobID}")
    # execute job
    commandLine = ["bash", "-c", f"/tmp/{job.jobID}/{job.filename}"] + [arg for arg in job.argv]
    job["timeStarted"] = utcNowTimestamp()
    result = subprocess.run(commandLine)
    job["timeEnded"] = utcNowTimestamp()
    job["exitCode"] = result.returncode
    job["stdout"] = result.stdout
    job["stderr"] = result.stderr
    # send job results to the api server
    response = requests.post(f"https://{API_HOST}/agent/history",
                            headers={"Content-Type": "application/json",
                                    "Agent-ID": agentID},
                            data=json.dumps({"job": job}),
                            verify=caPath,
                            cert=cert)
    assert response.status_code == 200
    assert response.json["success"] == "successfully saved job response"
