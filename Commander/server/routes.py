from datetime import datetime
from flask import request, send_file
import json
from .models import Agent, Job, Session, User
import requests
from server import app


@app.get("/agent/installer")
def sendAgentInstaller():
    """ Fetch or generate an agent installer for the given operating system """
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}
    # check OS version
    targetOS = request.json["os"]
    if targetOS not in ["linux", "windows"]:
        return {"error": "the only supported agent architectures are linux and windows"}
    # TODO: request installer client cert from CA
    response = requests.get("http://" + app.config["CA_HOSTNAME"] + "/ca/host-certificate",
                            headers={"Content-Type": "application/json"},
                            data={"hostname": f"{targetOS}installer"})
    # TODO: build executable installer
    # TODO: return installer
    pass


@app.post("/agent/register")
def registerNewAgent():
    """ Register a new agent with the commander server """
    # TODO: check registration key
    # TODO: add agent to db
    # TODO: return agent ID
    pass


@app.get("/agent/jobs")
def checkForJobs():
    """ Agent checking in -- send file to be executed if a job is waiting """
    if missingParams := missing(request, headers=["Agent-ID"]):
        return {"error": missingParams}, 400
    # check db for jobs
    agentQuery = Agent.objects(id__exact=request.headers["Agent-ID"])
    if not agentQuery:
        return {"error": "agent ID not found"}, 400
    agent = agentQuery[0]
    jobsQueue = agent["jobsQueue"].objects().order_by("+timeSubmitted")
    if not jobsQueue:
        return {"job": "no jobs"}, 200
    # get ready to send available job
    job = jobsQueue.pop(0)
    # move job to running queue
    job["timeDispatched"] = datetime.now()
    agent["jobsRunning"].append(job)
    agent.save()
    # send most recent job to agent
    return {"job": json.dumps(job)}


@app.post("/agent/jobs")
def assignJob():
    """ Admin submitting a job -- add job to the specified agent's queue """
    if missingParams := missing(request, headers=["Auth-Token", "Username"]):
        return {"error": missingParams}, 401
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}, 403
    # add job to agent's queue in db
    filename = request.json["filename"]  # TODO: error handling (filename should exist in library)
    command = request.json["command"]   # TODO: error handling (should be list of strings)
    jobsQuery = Job.objects(fileName__exact=filename)
    if not jobsQuery:
        return {"error": "the library contains no executable with the given filename"}
    job = jobsQuery[0]
    # TODO: search by agent id if available, otherwise hostname
    hostsQuery = Agent.objects(hostname__exact=request.json["hostname"])
    if not hostsQuery:
        return {"error": "no hosts found matching the hostname in the request"}
    if len(hostsQuery) > 1:
        return {"error": "multiple agents found with the given hostname"}
    agent = hostsQuery[0]
    job["argv"] = command
    job["timeSubmitted"] = datetime.utcnow()
    agent["jobsQueue"].append(job)
    agent.save()
    return {"success": "job successfully submitted -- waiting for agent to check in"}, 200


@app.get("/agent/execute")
def sendExecutable():
    """ Send executable or script to the agent for execution """
    if missingParams := missing(request, headers=["Agent-ID"], data=["fileName"]):
        return {"error": missingParams}, 400
    # check db for matching job
    agentQuery = Agent.objects(id__exact=request.headers["Agent-ID"])
    if not agentQuery:
        return {"error": "agent ID not found"}
    agent = agentQuery[0]
    jobRequestedQuery = agent["jobsRunning"].objects(filename__exact=request.json["fileName"])
    if not jobRequestedQuery:
        return {"error": "no matching job available for download"}, 400
    # matching job found -- send executable to the agent
    return send_file(jobRequestedQuery[0]["storagePath"],
                        attachment_filename=jobRequestedQuery[0]["fileName"])


@app.post("/agent/execute")
def collectJobResults():
    """ Job has been executed -- save output and return code """
    if missingParams := missing(request, headers=["Agent-ID"], data=["job"]):
        return {"error": missingParams}, 400
    # check db for matching job
    agentQuery = Agent.objects(id__exact=request.headers["Agent-ID"])
    if not agentQuery:
        return {"error": "agent ID not found"}
    agent = agentQuery[0]
    jobRequestedQuery = agent["jobsRunning"].objects(filename__exact=request.json["job"]["fileName"])
    if not jobRequestedQuery:
        return {"error": "no matching jobs were supposed to be running"}, 400
    jobRequestedQuery.pop(0)
    completedJob = Job(**request.json["job"])
    agent.jobsHistory.append(completedJob)
    agent.save()
    return {"success": "successfully saved job response"}, 200




@app.get("/admin/library")
def getJobLibrary():
    """ Return simplified library overview in json format """
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}
    # TODO


@app.post("/admin/library")
def addNewJob():
    """ Add a new executable to the Commander library """
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}
    # generate library entry document
    if "file" not in request.files:
        return {"error": "file not uploaded with request"}
    filename = request.json["filename"]
    description = request.json["description"]
    libraryEntry = Job(filename=filename,
                        description=description,
                        user=request.headers["Username"],
                        timeSubmitted=datetime.utcnow())
    # create library entry as long as filename doesn't already exist
    entriesQuery = Job.objects(filename__exact=filename)
    if entriesQuery:
        return {"error": f"file called '{filename}' already exists in the library"}
    libraryEntry.save()
    # save executable file to server
    uploadedFile = request.files["file"]
    uploadedFile.save(app.config["UPLOADS_DIR"], filename)
    return {"success": "successfully added new executable to the commander library"}


@app.patch("/admin/library")
def updateJob():
    """ Update the file or description of an existing entry in the commander library """
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}
    # TODO: check if update is for file or description
    # TODO: save new executable for existing library entry in db
    # or
    # TODO: update library description for file


@app.delete("/admin/library")
def deleteJob():
    """ Delete an entry and its corresponding file from the commander library """
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}
    # TODO: delete executable and existing library entry in db


@app.post("/admin/login")
def login():
    """ Authenticate an admin and return a new session token if successful """
    # TODO: hash password and check match
    # TODO: generate authentication token and set expiration
    # TODO: return authentication token and expiration date
    pass


@app.patch("/admin/login")
def updateCredentials():
    """ Authenticate an admin and update that admin's credentials """
    # TODO: hash password and check match
    # TODO: change password
    pass


@app.route("/admin/generate-registration-key", methods=["GET"])
def genRegistrationKey():
    """ Generate the registration key that agents need to register with commander """
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}
    # TODO: set registration key in db
    # TODO: return key
    pass


def authenticate(authToken):
    """ Check admin authentication token in db """
    tokenQuery = Session.objects(authToken__exact=authToken)
    if not tokenQuery:
        return None  # ensures empty username doesn't authenticate
    token = tokenQuery[0]
    if token["expires"] < datetime.utcnow():
        return None
    return token["username"]


def missing(request, headers=None, data=None):
    """ Return error message about missing paramaters if there are any """
    missingHeaders = []
    missingData = []
    if headers:
        for header in headers:
            if header not in request.headers:
                missingHeaders.append(header)
    if data:
        for field in data:
            if field not in request.json:
                missingHeaders.append(field)
    if not missingHeaders and not missingData:
        return None
    errMsg = "request is missing one or more of the following parameters: "
    if missingHeaders:
        errMsg += "header['"
        errMsg += "'], header['".join(headers)
        errMsg += "']"
    if missingHeaders and missingData:
        errMsg += ", "
    if missingData:
        errMsg += "data['"
        errMsg += ", ".join(data)
        errMsg += "']"
    return errMsg