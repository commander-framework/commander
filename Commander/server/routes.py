import bcrypt
from datetime import datetime, timedelta
from flask import request, send_file
import json
from .models import Agent, Job, RegistrationKey, Session, User
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
    if missingParams := missing(request, headers=["Auth-Token", "Username"], data=["hostname", "filename", "command"]):
        return {"error": missingParams}, 400
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}, 403
    # add job to agent's queue in db
    filename = request.json["filename"]
    command = request.json["command"]   # TODO: error handling (should be list of strings)
    jobsQuery = Job.objects(filename__exact=filename)
    if not jobsQuery:
        return {"error": "the library contains no executable with the given filename"}, 400
    job = jobsQuery[0]
    # TODO: search by agent id if available, otherwise hostname
    hostsQuery = Agent.objects(hostname__exact=request.json["hostname"])
    if not hostsQuery:
        return {"error": "no hosts found matching the hostname in the request"}, 400
    if len(hostsQuery) > 1:
        return {"error": "multiple agents found with the given hostname"}, 400
    agent = hostsQuery[0]
    job["user"] = request.headers["Username"]
    job["argv"] = command
    job["timeSubmitted"] = datetime.utcnow()
    agent["jobsQueue"].append(job)
    agent.save()
    return {"success": "job successfully submitted -- waiting for agent to check in"}, 200


@app.get("/agent/execute")
def sendExecutable():
    """ Send executable or script to the agent for execution """
    if missingParams := missing(request, headers=["Agent-ID"], data=["filename"]):
        return {"error": missingParams}, 400
    # check db for matching job
    agentQuery = Agent.objects(id__exact=request.headers["Agent-ID"])
    if not agentQuery:
        return {"error": "agent ID not found"}
    agent = agentQuery[0]
    jobRequestedQuery = agent["jobsRunning"].objects(filename__exact=request.json["filename"])
    if not jobRequestedQuery:
        return {"error": "no matching job available for download"}, 400
    # matching job found -- send executable to the agent
    return send_file(jobRequestedQuery[0]["storagePath"],
                     attachment_filename=jobRequestedQuery[0]["filename"])


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
    jobRequestedQuery = agent["jobsRunning"].objects(filename__exact=request.json["job"]["filename"])
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
    if missingParams := missing(request, headers=["Auth-Token", "Username"]):
        return {"error": missingParams}, 400
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}, 403
    jobsQuery = Job.objects()
    return {"library": jobsQuery}


@app.post("/admin/library")
def addNewJob():
    """ Add a new executable to the Commander library """
    if missingParams := missing(request, headers=["Auth-Token", "Username"], data=["filename", "description", "os", "executor"]):
        return {"error": missingParams}, 400
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}, 403
    # generate library entry document
    if "file" not in request.files:
        return {"error": "file not uploaded with request"}, 400
    filename = request.json["filename"]
    libraryEntry = Job(filename=filename,
                       description=request.json["description"],
                       os=request.json["os"],
                       executor=request.json["executor"],
                       user=request.headers["Username"],
                       timeSubmitted=datetime.utcnow())
    # create library entry as long as filename doesn't already exist
    entriesQuery = Job.objects(filename__exact=filename)
    if entriesQuery:
        return {"error": "file name already exists in the library"}, 400
    libraryEntry.save()
    # save executable file to server
    uploadedFile = request.files["file"]
    uploadedFile.save(app.config["UPLOADS_DIR"], filename)
    return {"success": "successfully added new executable to the commander library"}, 200


@app.patch("/admin/library")
def updateJob():
    """ Update the file or description of an existing entry in the commander library """
    if missingParams := missing(request, headers=["Auth-Token", "Username"], data=["filename"]):
        return {"error": missingParams}, 400
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}, 403
    # make sure job exists
    jobQuery = Job.objects(filename__exact=request.json["filename"])
    if not jobQuery:
        return {"error": "no existing job with that file name"}
    # make sure request either updates the file or the description
    if "file" not in request.files and "description" not in request.json:
        return {"error": "niether a new file nor a new description was provided"}, 400
    # save new executable if it was provided
    if "file" in request.files:
        uploadedFile = request.files["file"]
        uploadedFile.save(app.config["UPLOADS_DIR"], request.json["filename"])
    # update library description for file if a new one was provided
    if "description" in request.json:
        job = jobQuery[0]
        job["description"] = request.json["description"]
        job.save()
    return {"success": "successfully updated the job in the library"}


@app.delete("/admin/library")
def deleteJob():
    """ Delete an entry and its corresponding file from the commander library """
    if missingParams := missing(request, headers=["Auth-Token", "Username"], data=["filename"]):
        return {"error": missingParams}, 400
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}
    # make sure job exists
    jobQuery = Job.objects(filename__exact=request.json["filename"])
    if not jobQuery:
        return {"error": "no existing job with that file name"}
    # TODO: delete executable and existing library entry in db


@app.post("/admin/login")
def login():
    """ Authenticate an admin and return a new session token if successful """
    if missingParams := missing(request, data=["username", "password"]):
        return {"error": missingParams}, 400
    # make sure username exists
    adminQuery = User.objects(username__exact=request.json["username"])
    if not adminQuery:
        return {"error": "username not found"}, 400
    adminAccount = adminQuery[0]
    # hash password and check match
    if not bcrypt.checkpw(request.json["password"].encode(), adminAccount["hashedPassword"].encode()):
        # TODO: implement brute force protection
        return {"error": "password does not match"}, 403
    # generate session and set expiration
    newToken = bcrypt.gensalt().decode()[7:] + bcrypt.gensalt().decode()[7:]
    expiration = datetime.now() + timedelta(hours=24)
    session = Session(username=request.json["username"],
                      authToken=newToken,
                      expires=expiration)
    session.save()
    # add session to admin's session history
    adminAccount["sessions"].append(session)
    adminAccount.save()
    # return authentication token and expiration date
    return {"token": newToken, "expires": str(expiration)}, 200


@app.patch("/admin/login")
def updateCredentials():
    """ Authenticate an admin and update that admin's credentials """
    if missingParams := missing(request, data=["username", "password", "newPassword"]):
        return {"error": missingParams}, 400
    # make sure username exists
    adminQuery = User.objects(username__exact=request.json["username"])
    if not adminQuery:
        return {"error": "username not found"}, 400
    adminAccount = adminQuery[0]
    # hash password and check match
    if not bcrypt.checkpw(request.json["password"], adminAccount["hashedPassword"]):
        # TODO: implement brute force protection
        return {"error": "password does not match"}, 403
    # change password and save to the database
    salt = bcrypt.gensalt()
    hashedPassword = bcrypt.hashpw(request.json["newPassword"].encode(), salt)
    adminAccount["passwordHash"] = hashedPassword
    adminAccount.save()
    return {"success": "successfully changed the password for your account"}, 200


@app.get("/admin/registration-key")
def genRegistrationKey():
    """ Get or generate the registration key that agents need to register with commander """
    if missingParams := missing(request, headers=["Auth-Token", "Username"]):
        return {"error": missingParams}, 400
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}, 403
    # return current key if one exists
    regKeyQuery = RegistrationKey.objects()
    if regKeyQuery:
        return {"registration-key": regKeyQuery[0]["regKey"]}
    # create registration key in db
    newKey = bcrypt.gensalt().decode()[7:] + bcrypt.gensalt().decode()[7:]
    regKey = RegistrationKey(regKey=newKey)
    regKey.save()
    # return new key
    return {"registration-key": newKey}


@app.patch("/admin/registration-key")
def genRegistrationKey():
    """ Generate and return a new registration key that agents need to register with commander """
    if missingParams := missing(request, headers=["Auth-Token", "Username"]):
        return {"error": missingParams}, 400
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}, 403
    # make sure a current key exists
    regKeyQuery = RegistrationKey.objects()
    if regKeyQuery:
        regKey = regKeyQuery[0]
    # create registration key in db
    newKey = bcrypt.gensalt().decode()[7:] + bcrypt.gensalt().decode()[7:]
    regKey["regKey"] = newKey
    regKey.save()
    # return new key
    return {"registration-key": newKey}


def authenticate(authToken):
    """ If the given admin authentication token is valid return its username """
    sessionQuery = Session.objects(authToken__exact=authToken)
    if not sessionQuery:
        return None  # ensures empty username doesn't authenticate
    session = sessionQuery[0]
    if session["expires"] < datetime.utcnow():
        return None
    return session["username"]


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