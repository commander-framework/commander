import bcrypt
from datetime import datetime, timedelta
from .errors import CommanderError, CAPyError, GitHubError
from flask import request, send_from_directory
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
import json
from .models import Agent, Job, Library, RegistrationKey, User
from mongoengine import DoesNotExist
from os import path, remove
import requests
from server import app, jobsCache, log, sock
import shutil
from time import sleep
from types import SimpleNamespace
from utils import timestampToDatetime, utcNowTimestamp, convertDocsToJson
from uuid import uuid4
import zipfile


@app.get("/agent/installer")
@jwt_required()
def sendAgentInstaller():
    """ Fetch or generate an agent installer for the given operating system """
    log.debug(f"<{request.remote_addr}> requesting an agent installer")
    if missingParams := missing(request, data=["os"]):
        log.warning(f"<{request.remote_addr}> {missingParams}")
        return {"error": missingParams}, 400
    # make sure OS is valid
    targetOS = request.json["os"]
    if targetOS not in ["linux", "windows"]:
        return {"error": "the only supported agent architectures are linux and windows"}, 400
    filename = targetOS + "Installer.zip"
    # check what the latest version is
    response = requests.get("https://github.com/lawndoc/commander/releases/latest/download/version.txt", allow_redirects=True)
    if response.status_code != 200:
        log.error("failed to fetch agent version information from GitHub")
        raise CommanderError("failed to fetch agent version information from GitHub")
    version = response.content.decode("utf-8").strip()
    # check if we have the newest installers
    if not path.exists(f"agent/installers/{version}/{filename}"):
        try:
            getLatestAgentInstallers(version)
        except CommanderError as e:
            log.error(e)
            raise e
    log.info(f"<{request.remote_addr}> sending agent installer for {targetOS}")
    return send_from_directory(f"agent/installers/{version}/{filename}", filename=filename), 200


def getLatestAgentInstallers(version):
    """ Gets the latest agent installers from GitHub """
    log.debug(f"fetching latest agent installers for commander agent {version}")
    # get client cert from CAPy if we don't already have it
    if not path.exists("agent/certs/client.crt") or not path.exists("agent/certs/client.key") or not path.exists("agent/certs/root.crt"):
        response = requests.get("http://" + app.config["CA_HOSTNAME"] + "/ca/host-certificate",
                                headers={"Content-Type": "application/json"},
                                data={"hostname": "installer"})
        if response.status_code != 200:
            raise CAPyError("failed to get installer cert from CAPy")
        with open("agent/certs/client.crt", "w") as f:
            f.write(response.json["cert"])
        with open("agent/certs/client.key", "w") as f:
            f.write(response.json["key"])
        with open("agent/certs/root.crt", "w") as f:
            f.write(response.json["root"])
    # get installers from GitHub
    with requests.get(f"https://github.com/lawndoc/commander/releases/download/{version}/windowsInstaller.zip") as response:
        if response.status_code != 200:
            raise GitHubError("failed to get windows installer from GitHub")
        with open(f"agent/installers/{version}/windowsInstaller.zip", 'wb') as f:
            shutil.copyfileobj(response.raw, f)
    with requests.get(f"https://github.com/lawndoc/commander/releases/download/{version}/linuxInstaller.zip") as response:
        if response.status_code != 200:
            raise GitHubError("failed to get linux installer from GitHub")
        with open(f"agent/installers/{version}/linuxInstaller.zip", 'wb') as f:
            shutil.copyfileobj(response.raw, f)
    # add certs to installer zips
    with zipfile.ZipFile(f"agent/installers/{version}/windowsInstaller.zip", 'a') as windowsZip:
        # TODO: I think I need to convert line endings here before adding the files
        windowsZip.write("agent/certs/client.crt", arcname="client.crt")
        windowsZip.write("agent/certs/client.key", arcname="client.key")
        windowsZip.write("agent/certs/root.crt", arcname="root.crt")
    with zipfile.ZipFile(f"agent/installers/{version}/linuxInstaller.zip", 'a') as linuxZip:
        linuxZip.write("agent/certs/client.crt", arcname="client.crt")
        linuxZip.write("agent/certs/client.key", arcname="client.key")
        linuxZip.write("agent/certs/root.crt", arcname="root.crt")


@app.post("/agent/register")
def registerNewAgent():
    """ Register a new agent with the commander server """
    log.debug(f"<{request.remote_addr}> registering a new agent")
    if missingParams := missing(request, data=["registrationKey", "hostname", "os"]):
        log.warning(f"<{request.remote_addr}> {missingParams}")
        return {"error": missingParams}, 400
    # check registration key
    regKey = RegistrationKey.objects().first()
    if not regKey:
        log.error("no agent registration key found")
        return {"error": "no registration key has been generated yet"}, 500
    if regKey["regKey"] != request.json["registrationKey"]:
        log.warning(f"<{request.remote_addr}> invalid registration key")
        return {"error": "invalild registration key"}, 401
    # TODO: make sure OS is valid
    # create agent doc and add it to the db
    newAgent = Agent(hostname=request.json["hostname"],
                     agentID=str(uuid4()),
                     os=request.json["os"],
                     lastCheckin=utcNowTimestamp())
    newAgent.save()
    # return agent ID
    log.info(f"<{request.remote_addr}> registered new agent {newAgent['agentID']}")
    return {"agentID": newAgent["agentID"]}


@sock.route("/agent/checkin")
def agentCheckin(ws):
    """ Agent checking in -- send file to be executed if a job is waiting """
    log.debug(f"<{ws.sock.getpeername()[0]}> agent checking in")
    # get agent ID from socket
    while True:
        data = ws.receive()
        # validate that json data was sent
        try:
            jsonData = json.loads(data)
        except Exception:
            log.warning(f"[{ws.sock.getpeername()[0]}] invalid json data received from agent during checkin")
            ws.close(400, json.dumps({"error": "message was not a valid json object"}))
            return {"error": "message was not a valid json object"}
        # convert data to request-like object for missing()
        request = SimpleNamespace(**{"headers": jsonData,
                                     "remote_addr": ws.sock.getpeername()[0]})
        # check if the Agent ID was provided in the json data
        if missingParams := missing(request, headers=["Agent-ID"]):
            log.warning(f"<{request.remote_addr}> {missingParams}")
            ws.close(400, json.dumps({"error": missingParams}))
            return {"error": missingParams}
        # make sure Agent ID exists in the DB
        agentQuery = Agent.objects(agentID__exact=request.headers["Agent-ID"])
        if not agentQuery:
            log.warning(f"<{request.remote_addr}> agentID not found in database")
            ws.close(400, json.dumps({"error": "agent ID not found, please check ID or register"}))
            return {"error": "agent ID not found, please check ID or register"}
        break
    # monitor for jobs to send to the agent
    agent = agentQuery[0]
    while True:
        # TODO: check if the socket is closed by the agent and edit the agent's lastOnline and active fields
        # check db for jobs
        job = jobsCache.agentCheckin(agent["agentID"], "foo_group")  # TODO: implement agent groups
        if not job:
            sleep(1)
            continue
        # send most recent job to agent
        log.info(f"<{request.remote_addr}> sending job '{job['filename']}' to agent")
        ws.send(json.dumps({"job": job.to_json()}))
        # wait for acknowledgement from agent before marking job as running
        ack = ws.receive()
        if ack != "ack":
            continue
        # mark job as received by the agent
        log.info(f"<{request.remote_addr}> marking job '{job['filename']}' as received by agent")
        jobsCache.markSent(agent["agentID"])
        # stop checking for jobs if we are testing this function, otherwise continue watching for jobs
        try:
            return ws.isMockServer
        except AttributeError:
            pass


@app.post("/agent/jobs")
@jwt_required()
def assignJob():
    """ Admin submitting a job -- add job to the specified agent's queue """
    log.debug(f"<{request.remote_addr}> {get_jwt_identity()} assigning a job")
    if missingParams := missing(request, data=["agentID", "filename", "argv"]):
        log.warning(f"<{request.remote_addr}> {missingParams}")
        return {"error": missingParams}, 400
    # get job document from the db
    library = Library.objects().first()
    if not library:
        log.warning(f"<{request.remote_addr}> failed to assign a job because the library is empty")
        return {"error": "there are no jobs in the library yet"}, 400
    jobsQuery = list(filter(lambda job: job["filename"] == request.json["filename"], library["jobs"]))
    if not jobsQuery:
        log.warning(f"<{request.remote_addr}> failed to assign a job because it was not found in the library")
        return {"error": "the library contains no executable with the given filename"}, 400
    job = jobsQuery[0]
    argv = request.json["argv"]   # TODO: error handling (should be list of strings)
    job["user"] = get_jwt_identity()
    job["argv"] = argv
    job["timeCreated"] = utcNowTimestamp()
    # add job to the agent's queue
    try:
        jobsCache.assignJob(job, agentID=request.json["agentID"])
    except ValueError as e:
        log.warning(f"failed to assign job to agent: {e}")
        return {"error": str(e)}, 400
    log.info(f"<{request.remote_addr}> {get_jwt_identity()} assigned job '{job['filename']}' to agent {request.json['agentID']}")
    return {"success": "job successfully submitted -- waiting for agent to check in"}, 200


@app.get("/agent/execute")
def sendExecutable():
    """ Send executable or script to the agent for execution """
    log.debug(f"<{request.remote_addr}> sending executable")
    if missingParams := missing(request, headers=["Agent-ID"], data=["filename"]):
        log.warning(f"<{request.remote_addr}> {missingParams}")
        return {"error": missingParams}, 400
    # check db for matching job
    agentQuery = Agent.objects(agentID__exact=request.headers["Agent-ID"])
    if not agentQuery:
        log.warning(f"<{request.remote_addr}> agentID not found in database")
        return {"error": "agent ID not found"}, 400
    agent = agentQuery[0]
    jobsQuery = list(filter(lambda job: job["filename"] == request.json["filename"], agent["jobsRunning"]))
    if not jobsQuery:
        log.warning(f"<{request.remote_addr}> agent does not have a job with the given filename")
        return {"error": "no matching job available for download"}, 400
    # make sure file exists
    if not path.exists(app.config["UPLOADS_DIR"] + path.sep + jobsQuery[0]["filename"]):
        log.error(f"<{request.remote_addr}> file '{jobsQuery[0]['filename']}' does not exist")
        return {"error": "job file missing -- please contact an administrator"}, 500
    # matching job found -- send executable to the agent
    log.info(f"<{request.remote_addr}> sending file '{jobsQuery[0]['filename']}' to agent")
    return send_from_directory(directory=app.config["UPLOADS_DIR"],
                               path=jobsQuery[0]["filename"])


@app.get("/agent/history")
@jwt_required()
def getJobResults():
    """ Get all jobs that have executed in the last 7 days, or optionally specify a different amount of time """
    log.debug(f"<{request.remote_addr}> getting job results")
    if missingParams := missing(request, data=["agentID"]):
        log.warning(f"<{request.remote_addr}> {missingParams}")
        return {"error": missingParams}, 400
    # check db for matching agent
    agentQuery = Agent.objects(agentID__exact=request.json["agentID"])
    if not agentQuery:
        log.warning(f"<{request.remote_addr}> agentID not found in database")
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
    log.info(f"<{request.remote_addr}> returning {len(jobHistory)} jobs from agent {request.json['agentID']}'s history")
    return {"jobs": jobHistory}, 200


@app.post("/agent/history")
def postJobResults():
    """ Job has been executed -- save output and return code """
    log.debug(f"<{request.remote_addr}> saving job results")
    if missingParams := missing(request, headers=["Agent-ID"], data=["job"]):
        log.warning(f"<{request.remote_addr}> {missingParams}")
        return {"error": missingParams}, 400
    # check db for matching job
    agentQuery = Agent.objects(agentID__exact=request.headers["Agent-ID"])
    if not agentQuery:
        log.warning(f"<{request.remote_addr}> agentID not found in database")
        return {"error": "agent ID not found"}, 400
    agent = agentQuery[0]
    finishedJob = json.loads(request.json["job"])
    jobRunningQuery = list(filter(lambda job: job["filename"] == finishedJob["filename"], agent["jobsRunning"]))
    if not jobRunningQuery:
        log.warning(f"<{request.remote_addr}> agent does not have a running job with the given filename")
        return {"error": "no matching jobs were supposed to be running"}, 400
    agent.update(pull__jobsRunning=jobRunningQuery[0])
    completedJob = Job(**finishedJob)
    agent.jobsHistory.append(completedJob)
    agent.save()
    log.info(f"<{request.remote_addr}> agent {request.headers['Agent-ID']} has finished job '{finishedJob['filename']}'")
    return {"success": "successfully saved job response"}, 200


@app.get("/admin/library")
@jwt_required()
def getJobLibrary():
    """ Return simplified library overview in json format """
    log.debug(f"<{request.remote_addr}> getting job library")
    try:
        library = Library.objects().get()
    except DoesNotExist:
        log.info(f"<{request.remote_addr}> returning empty library")
        return "", 204
    log.info(f"<{request.remote_addr}> returning library overview")
    return {"library": library.to_json()}, 200


@app.post("/admin/library")
@jwt_required()
def addNewJob():
    """ Add a new executable to the Commander library """
    log.debug(f"<{request.remote_addr}> adding new job")
    if missingParams := missingJobForm(request, data=["job", "file"]):
        log.warning(f"<{request.remote_addr}> {missingParams}")
        return {"error": missingParams}, 400
    # generate library entry document
    if "file" not in request.files:
        log.warning(f"<{request.remote_addr}> no file uploaded with new job")
        return {"error": "file not uploaded with request"}, 400
    newJob = json.loads(request.form["job"])
    # make sure job includes all required fields
    if missingFields := missingJobFields(newJob):
        log.warning(f"<{request.remote_addr}> {missingFields}")
        return {"error": missingFields}, 400
    libraryEntry = Job(**newJob)
    # create library if it doesn't already exist
    libraryQuery = Library.objects()
    if not libraryQuery:
        log.info(f"<{request.remote_addr}> library is empty, initializing libary")
        library = Library(jobs=[])
    else:
        library = libraryQuery[0]
    # check if filename already exists in the library
    jobsQuery = list(filter(lambda job: job["filename"] == libraryEntry["filename"], library["jobs"]))
    if jobsQuery:
        log.warning(f"<{request.remote_addr}> filename already exists in the job library")
        return {"error": "file name already exists in the library"}, 400
    # save executable file to server and job entry to libary
    uploadedFile = request.files["file"]
    uploadedFile.save(app.config["UPLOADS_DIR"] + libraryEntry["filename"])
    library["jobs"].append(libraryEntry)
    library.save()
    log.info(f"<{request.remote_addr}> added new job '{libraryEntry['filename']}' to library")
    return {"success": "successfully added new executable to the commander library"}, 200


@app.patch("/admin/library")
@jwt_required()
def updateJob():
    """ Update the file or description of an existing entry in the commander library """
    log.debug(f"<{request.remote_addr}> updating job")
    if missingParams := missingJobForm(request, data=["filename"]):
        log.warning(f"<{request.remote_addr}> {missingParams}")
        return {"error": missingParams}, 400
    # make sure library exists
    library = Library.objects().first()
    if not library:
        log.warning(f"<{request.remote_addr}> failed to update job because the library is empty")
        return {"error": "there is no job library yet"}, 400
    # make sure job exists
    jobsQuery = list(filter(lambda job: job["filename"] == request.form["filename"], library["jobs"]))
    if not jobsQuery:
        log.warning(f"<{request.remote_addr}> failed to update job because the job does not exist")
        return {"error": "no existing job with that file name"}, 400
    # make sure request either updates the file or the description
    if "file" not in request.files and "description" not in request.form:
        log.warning(f"<{request.remote_addr}> failed to update job because no filename or description was provided")
        return {"error": "niether a new file nor a new description was provided"}, 400
    # save new executable if it was provided
    if "file" in request.files:
        uploadedFile = request.files["file"]
        uploadedFile.save(app.config["UPLOADS_DIR"] + request.form["filename"])
        log.info(f"<{request.remote_addr}> updated job file for '{request.form['filename']}'")
    # update library description for file if a new one was provided
    if "description" in request.form:
        job = jobsQuery[0]
        job["description"] = request.form["description"]
        job["timeCreated"] = utcNowTimestamp()
        library.save()
        log.info(f"<{request.remote_addr}> updated job description for '{request.form['filename']}'")
    return {"success": "successfully updated the job in the library"}, 200


@app.delete("/admin/library")
@jwt_required()
def deleteJob():
    """ Delete an entry and its corresponding file from the commander library """
    log.debug(f"<{request.remote_addr}> deleting job")
    if missingParams := missing(request, data=["filename"]):
        log.warning(f"<{request.remote_addr}> {missingParams}")
        return {"error": missingParams}, 400
    # make sure job exists
    library = Library.objects().first()
    if not library:
        log.warning(f"<{request.remote_addr}> failed to delete job because the library is empty")
        return {"error": "there are no jobs in the library yet"}, 400
    jobsQuery = list(filter(lambda job: job["filename"] == request.json["filename"], library["jobs"]))
    if not jobsQuery:
        log.warning(f"<{request.remote_addr}> failed to delete job because the job does not exist")
        return {"error": "no existing job with that file name"}, 400
    job = jobsQuery[0]
    # delete executable from file system
    if path.isfile(app.config["UPLOADS_DIR"] + request.json["filename"]):
        remove(app.config["UPLOADS_DIR"] + request.json["filename"])
    # remove existing library entry in db
    library.update(pull__jobs=job)
    # remove library if empty
    if not Library.objects().first()["jobs"]:
        library.delete()
    log.info(f"<{request.remote_addr}> deleted job '{request.json['filename']}' from library")
    return {"success": "successfully deleted the job from the library"}, 200


@app.post("/admin/login")
def login():
    """ Authenticate an admin and return a new session token if successful """
    log.debug(f"<{request.remote_addr}> logging in")
    if missingParams := missing(request, data=["username", "password"]):
        log.warning(f"<{request.remote_addr}> {missingParams}")
        return {"error": missingParams}, 400
    # make sure username exists
    adminQuery = User.objects(username__exact=request.json["username"])
    if not adminQuery:
        log.info(f"<{request.remote_addr}> failed to login because the username does not exist")
        return {"error": "username not found"}, 401
    adminAccount = adminQuery[0]
    # hash password and check match
    if not bcrypt.checkpw(request.json["password"].encode(), adminAccount["passwordHash"].encode()):
        # TODO: implement brute force protection
        log.info(f"<{request.remote_addr}> failed to login because the password was incorrect")
        return {"error": "password does not match"}, 401
    # generate session and set expiration
    accessToken = create_access_token(identity=request.json["username"])
    log.info(f"<{request.remote_addr}> successfully logged in and generated a new session token for '{request.json['username']}'")
    return {"token": accessToken}, 200


@app.patch("/admin/login")
def updateCredentials():
    """ Authenticate an admin and update that admin's credentials """
    log.debug(f"<{request.remote_addr}> updating credentials")
    if missingParams := missing(request, data=["username", "password", "newPassword"]):
        log.warning(f"<{request.remote_addr}> {missingParams}")
        return {"error": missingParams}, 400
    # make sure username exists
    adminQuery = User.objects(username__exact=request.json["username"])
    if not adminQuery:
        log.info(f"<{request.remote_addr}> failed to update credentials because the username does not exist")
        return {"error": "username not found"}, 401
    adminAccount = adminQuery[0]
    # hash password and check match
    if not bcrypt.checkpw(request.json["password"].encode(), adminAccount["passwordHash"].encode()):
        # TODO: implement brute force protection
        log.info(f"<{request.remote_addr}> failed to update credentials because the password was incorrect")
        return {"error": "password does not match"}, 401
    # change password and save to the database
    salt = bcrypt.gensalt()
    hashedPassword = bcrypt.hashpw(request.json["newPassword"].encode(), salt)
    adminAccount["passwordHash"] = hashedPassword.decode()
    adminAccount.save()
    log.info(f"<{request.remote_addr}> successfully updated credentials for '{request.json['username']}'")
    return {"success": "successfully changed the password for your account"}, 200


@app.post("/admin/account")
@jwt_required()
def newAdmin():
    """ Create a new admin account using valid session """
    log.debug(f"<{request.remote_addr}> creating new admin account")
    if missingParams := missing(request, data=["username", "password", "name"]):
        log.warning(f"<{request.remote_addr}> {missingParams}")
        return {"error": missingParams}, 400
    adminQuery = User.objects(username__exact=request.json["username"])
    if adminQuery:
        log.warning(f"<{request.remote_addr}> failed to create account because the username already exists")
        return {"error": "username already taken"}, 400
    # hash password and save to the database
    salt = bcrypt.gensalt()
    hashedPassword = bcrypt.hashpw(request.json["password"].encode(), salt)
    adminAccount = User(name=request.json["name"],
                        username=request.json["username"],
                        passwordHash=hashedPassword.decode())
    adminAccount.save()
    log.info(f"<{request.remote_addr}> successfully created a new admin account for '{request.json['username']}'")
    return {"success": "successfully created new admin account"}, 200


@app.get("/admin/authenticate")
@jwt_required()
def testAuthentication():
    """ Authenticate using session token to test and see if it is still valid """
    log.info(f"<{request.remote_addr}> successfully test authenticated '{get_jwt_identity()}' with a valid JWT")
    return {"success": "authentication token is valid"}, 200


@app.get("/admin/registration-key")
@jwt_required()
def getRegistrationKey():
    """ Get or generate the registration key that agents need to register with commander """
    log.debug(f"<{request.remote_addr}> getting registration key")
    # return current key if one exists
    regKeyQuery = RegistrationKey.objects()
    if regKeyQuery:
        return {"registration-key": regKeyQuery[0]["regKey"]}
    # create registration key in db
    newKey = str(uuid4())
    regKey = RegistrationKey(regKey=newKey)
    regKey.save()
    # return new key
    log.info(f"<{request.remote_addr}> successfully fetched registration key")
    return {"registration-key": newKey}


@app.put("/admin/registration-key")
@jwt_required()
def updateRegistrationKey():
    """ Generate and return a new registration key that agents need to register with commander """
    log.debug(f"<{request.remote_addr}> updating registration key")
    # make sure a current key exists
    regKeyQuery = RegistrationKey.objects()
    if not regKeyQuery:
        regKey = RegistrationKey(regKey="placeholder")
    else:
        regKey = regKeyQuery[0]
    # update the registration key and save to db
    newKey = str(uuid4())
    regKey["regKey"] = newKey
    regKey.save()
    # return new key
    log.info(f"<{request.remote_addr}> successfully regenerated the registration key")
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
    log.info(f"successfully authenticated '{username}' with auth token")
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
    errMsg = "request is missing the following parameters: "
    if missingHeaders:
        errMsg += "headers=['"
        errMsg += "', '".join(missingHeaders)
        errMsg += "']"
    if missingHeaders and missingData:
        errMsg += ", "
    if missingData:
        errMsg += "data=['"
        errMsg += "', '".join(missingData)
        errMsg += "']"
    return errMsg


def missingJobForm(request, headers=None, data=None):
    """ Return error message about missing paramaters if there are any """
    missingHeaders = []
    missingData = []
    if headers:
        for header in headers:
            if header not in request.headers:
                missingHeaders.append(header)
    if data:
        for field in data:
            if field not in request.form and field not in request.files:
                missingData.append(field)
    if not missingHeaders and not missingData:
        return None
    errMsg = "request is missing the following parameters: "
    if missingHeaders:
        errMsg += "headers=['"
        errMsg += "', '".join(missingHeaders)
        errMsg += "']"
    if missingHeaders and missingData:
        errMsg += ", "
    if missingData:
        errMsg += "data=['"
        errMsg += "', '".join(missingData)
        errMsg += "']"
    return errMsg


def missingJobFields(jobJson):
    """ Return error message about missing job fields if there are any """
    requiredFields = ["executor", "filename", "description", "os", "user", "timeCreated"]
    missingFields = []
    for field in requiredFields:
        if field not in jobJson:
            missingFields.append(field)
    if not missingFields:
        return None
    errMsg = "the job in the request is missing the following fields: ['"
    errMsg += "', '".join(missingFields)
    errMsg += "']"
    return errMsg
