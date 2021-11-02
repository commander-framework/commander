import bcrypt
from datetime import datetime, timedelta
from flask import request, send_from_directory
from .models import Agent, Job, Library, RegistrationKey, Session, User
from os import path
import requests
from server import app
from utils import timestampToDatetime, utcNowTimestamp, convertDocsToJson


@app.get("/agent/installer")
def sendAgentInstaller():
    """ Fetch or generate an agent installer for the given operating system """
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"], request.headers["Username"]) != request.headers["Username"]:
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
def agentCheckin():
    """ Agent checking in -- send file to be executed if a job is waiting """
    if missingParams := missing(request, headers=["Agent-ID"]):
        return {"error": missingParams}, 400
    # check db for jobs
    agentQuery = Agent.objects(agentID__exact=request.headers["Agent-ID"])
    if not agentQuery:
        return {"error": "agent ID not found"}, 400
    agent = agentQuery[0]
    jobsQueue = sorted(agent["jobsQueue"], key = lambda i: i["timeCreated"])
    if not jobsQueue:
        return {"job": "no jobs"}, 200
    # get ready to send available job
    job = jobsQueue.pop(0)
    # move job to running queue
    job["timeDispatched"] = utcNowTimestamp()
    agent["jobsRunning"].append(job)
    agent.save()
    # send most recent job to agent
    return {"job": job.to_json()}, 200


@app.post("/agent/jobs")
def assignJob():
    """ Admin submitting a job -- add job to the specified agent's queue """
    if missingParams := missing(request, headers=["Auth-Token", "Username"], data=["agentID", "filename", "argv"]):
        return {"error": missingParams}, 400
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"], request.headers["Username"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}, 403
    # add job to agent's queue in db
    filename = request.json["filename"]
    argv = request.json["argv"]   # TODO: error handling (should be list of strings)
    library = Library.objects().first()
    if not library:
        return {"error": "there are no jobs in the library yet"}, 400
    jobsQuery = list(filter(lambda job: job["filename"] == request.json["filename"], library["jobs"]))
    if not jobsQuery:
        return {"error": "the library contains no executable with the given filename"}, 400
    job = jobsQuery[0]
    # TODO: search by agent id if available, otherwise hostname
    hostsQuery = Agent.objects(agentID__exact=request.json["agentID"])
    if not hostsQuery:
        return {"error": "no hosts found matching the agentID in the request"}, 400
    agent = hostsQuery[0]
    job["user"] = request.headers["Username"]
    job["argv"] = argv
    job["timeCreated"] = utcNowTimestamp()
    agent["jobsQueue"].append(job)
    agent.save()
    return {"success": "job successfully submitted -- waiting for agent to check in"}, 200


@app.get("/agent/execute")
def sendExecutable():
    """ Send executable or script to the agent for execution """
    if missingParams := missing(request, headers=["Agent-ID"], data=["filename"]):
        return {"error": missingParams}, 400
    # check db for matching job
    agentQuery = Agent.objects(agentID__exact=request.headers["Agent-ID"])
    if not agentQuery:
        return {"error": "agent ID not found"}, 400
    agent = agentQuery[0]
    jobsQuery = list(filter(lambda job: job["filename"] == request.json["filename"], agent["jobsRunning"]))
    if not jobsQuery:
        return {"error": "no matching job available for download"}, 400
    # make sure file exists
    if not path.exists(app.config["UPLOADS_DIR"] + path.sep + jobsQuery[0]["filename"]):
        return {"error": "job file missing -- please contact an administrator"}, 500
    # matching job found -- send executable to the agent
    return send_from_directory(directory=app.config["UPLOADS_DIR"],
                               path=jobsQuery[0]["filename"])


@app.get("/agent/history")
def getJobResults():
    """ Get all jobs that have executed in the last 7 days, or optionally specify a different amount of time """
    if missingParams := missing(request, headers=["Auth-Token", "Username"], data=["agentID"]):
        return {"error": missingParams}, 400
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"], request.headers["Username"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}, 403
    # check db for matching agent
    agentQuery = Agent.objects(agentID__exact=request.json["agentID"])
    if not agentQuery:
        return {"error": "agent ID not found"}, 400
    agent = agentQuery[0]
    # get all jobs that have executed in the last 7 days (or specified time)
    try:
        daysAgo = int(request.args["daysAgo"])
    except KeyError:
        daysAgo = 7
    jobHistoryQuery = list(filter(lambda job: timestampToDatetime(job["timeEnded"]) > datetime.utcnow() - timedelta(days=daysAgo), agent["jobsHistory"]))
    # convert to json
    jobHistory = convertDocsToJson(jobHistoryQuery)
    return {"jobs": jobHistory}, 200


@app.post("/agent/history")
def postJobResults():
    """ Job has been executed -- save output and return code """
    if missingParams := missing(request, headers=["Agent-ID"], data=["job"]):
        return {"error": missingParams}, 400
    # check db for matching job
    agentQuery = Agent.objects(agentID__exact=request.headers["Agent-ID"])
    if not agentQuery:
        return {"error": "agent ID not found"}, 400
    agent = agentQuery[0]
    jobRunningQuery = list(filter(lambda job: job["filename"] == request.json["filename"], agent["jobsRunning"]))
    if not jobRunningQuery:
        return {"error": "no matching jobs were supposed to be running"}, 400
    jobRunningQuery.pop(0)
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
    if authenticate(request.headers["Auth-Token"], request.headers["Username"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}, 403
    jobsQuery = Library.objects()
    return {"library": jobsQuery}


@app.post("/admin/library")
def addNewJob():
    """ Add a new executable to the Commander library """
    if missingParams := missing(request, headers=["Auth-Token", "Username"], data=["filename", "description", "os", "executor"]):
        return {"error": missingParams}, 400
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"], request.headers["Username"]) != request.headers["Username"]:
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
                       timeSubmitted=utcNowTimestamp())
    # create library if it doesn't already exist
    libraryQuery = Library.objects()
    if not libraryQuery:
        library = Library(jobs=[])
        library.save()
    else:
        library = libraryQuery[0]
    # check if filename already exists in the library
    jobsQuery = list(filter(lambda job: job["filename"] == request.json["filename"], library["jobs"]))
    if jobsQuery:
        return {"error": "file name already exists in the library"}, 400
    # save executable file to server and job entry to libary
    uploadedFile = request.files["file"]
    uploadedFile.save(app.config["UPLOADS_DIR"], filename)
    library["jobs"].append(libraryEntry)
    library.save()
    return {"success": "successfully added new executable to the commander library"}, 200


@app.patch("/admin/library")
def updateJob():
    """ Update the file or description of an existing entry in the commander library """
    if missingParams := missing(request, headers=["Auth-Token", "Username"], data=["filename"]):
        return {"error": missingParams}, 400
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"], request.headers["Username"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}, 403
    # make sure job exists
    library = Library.objects().first()
    if not library:
        return {"error": "there are no jobs in the library yet"}, 400
    jobsQuery = list(filter(lambda job: job["filename"] == request.json["filename"], library["jobs"]))
    if not jobsQuery:
        return {"error": "no existing job with that file name"}, 400
    # make sure request either updates the file or the description
    if "file" not in request.files and "description" not in request.json:
        return {"error": "niether a new file nor a new description was provided"}, 400
    # save new executable if it was provided
    if "file" in request.files:
        uploadedFile = request.files["file"]
        uploadedFile.save(app.config["UPLOADS_DIR"], request.json["filename"])
    # update library description for file if a new one was provided
    if "description" in request.json:
        job = jobsQuery[0]
        job["description"] = request.json["description"]
        job.save()
    return {"success": "successfully updated the job in the library"}


@app.delete("/admin/library")
def deleteJob():
    """ Delete an entry and its corresponding file from the commander library """
    if missingParams := missing(request, headers=["Auth-Token", "Username"], data=["filename"]):
        return {"error": missingParams}, 400
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"], request.headers["Username"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}
    # make sure job exists
    library = Library.objects().first()
    if not library:
        return {"error": "there are no jobs in the library yet"}, 400
    jobsQuery = list(filter(lambda job: job["filename"] == request.json["filename"], library["jobs"]))
    if not jobsQuery:
        return {"error": "no existing job with that file name"}
    # TODO: delete executable from file system
    # remove existing library entry in db
    job = jobsQuery[0]
    job.delete()
    job.save()


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
    expiration = utcNowTimestamp(deltaHours=24)
    session = Session(username=request.json["username"],
                      authToken=newToken,
                      expires=expiration)
    session.save()
    # add session to admin's session history
    adminAccount["sessions"].append(session)
    adminAccount.save()
    # return authentication token and expiration date
    return {"token": newToken, "expires": expiration}, 200


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
def getRegistrationKey():
    """ Get or generate the registration key that agents need to register with commander """
    if missingParams := missing(request, headers=["Auth-Token", "Username"]):
        return {"error": missingParams}, 400
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"], request.headers["Username"]) != request.headers["Username"]:
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
def updateRegistrationKey():
    """ Generate and return a new registration key that agents need to register with commander """
    if missingParams := missing(request, headers=["Auth-Token", "Username"]):
        return {"error": missingParams}, 400
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"], request.headers["Username"]) != request.headers["Username"]:
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


def authenticate(authToken, username):
    """ If the given admin authentication token is valid return its username """
    userQuery = User.objects(username__exact=username)
    if not userQuery:
        return None
    user = userQuery[0]
    sessionQuery = list(filter(lambda session: session["authToken"] == authToken, user["sessions"]))
    if not sessionQuery:
        return None
    session = sessionQuery[0]
    if timestampToDatetime(session["expires"]) < datetime.utcnow():
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
                missingData.append(field)
    if not missingHeaders and not missingData:
        return None
    errMsg = "request is missing one or more of the following parameters: "
    if missingHeaders:
        errMsg += "headers=['"
        errMsg += "', '".join(headers)
        errMsg += "']"
    if missingHeaders and missingData:
        errMsg += ", "
    if missingData:
        errMsg += "data=['"
        errMsg += "', '".join(data)
        errMsg += "']"
    return errMsg