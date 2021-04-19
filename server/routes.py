from datetime import datetime
from flask import request, send_file
import json
from .models import *
import requests
from server import app


@app.route("/agent/generate", methods=["GET"])
def generateAgentInstaller():
    """ Generate an agent installer for the given operating system """
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}
    # TODO: check OS version
    # TODO: request installer client cert from CA
    # TODO: build executable installer
    # TODO: return installer
    pass


@app.route("/agent/register", methods=["POST"])
def register():
    """ Register a new agent with the commander server """
    # TODO: check registration key
    # TODO: add agent to db
    # TODO: return agent ID
    pass


@app.route("/agent/jobs", methods=["GET", "POST"])
def jobs():
    if request.method == "GET":
        """ Agent checking in -- send file to be executed if a job is waiting """
        # check db for jobs
        agentQuery = Agent.objects(id__exact=request.headers["Agent-ID"])
        if not agentQuery:
            return {"error": "agent ID not found"}
        agent = agentQuery[0]
        jobsQueue = agent["jobsQueue"].objects().order_by("+timeSubmitted")
        if not jobsQueue:
            return {"jobs": "no jobs"}
        # send most recent job to agent
        return send_file(jobsQueue[0]["storagePath"], attachment_filename=jobsQueue[0]["fileName"])
    elif request.method == "POST":
        """ Admin submitting a job -- add job to the specified agent's queue """
        # check admin authentication token
        if authenticate(request.headers["Auth-Token"]) != request.headers["Username"]:
            return {"error": "invalid auth token or token expired"}
        # add job to agent's queue in db
        filename = request.json["filename"]  # TODO: error checking
        libraryQuery = Library.objects()[0]
        if not libraryQuery:
            return {"error": "no executables found in library"}
        commanderLibrary = libraryQuery[0]
        jobsQuery = commanderLibrary["jobs"].objects(fileName__exact=filename)
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
        agent["jobsQueue"].append(job)
        return {"success": "job successfully submitted -- waiting for agent to check in"}


@app.route("/admin/library", methods=["GET", "POST", "PATCH", "DELETE"])
def library():
    # check admin authentication token
    if authenticate(request.headers["Auth-Token"]) != request.headers["Username"]:
        return {"error": "invalid auth token or token expired"}
    if request.method == "GET":
        """ Return simplified library overview in json format """
        pass
    elif request.method == "POST":
        """ Add a new executable to the Commander library """
        # generate library entry document
        if "file" not in request.files:
            return {"error": "file not uploaded with request"}
        filename = request.json["filename"]
        description = request.json["description"]
        libraryEntry = Job(filename=filename,
                           description=description,
                           user=request.headers["Username"],
                           timeSubmitted=datetime.utcnow())
        # open library document or create the library if it doesn't exist yet
        commanderLibraryQuery = Library.objects()
        if not commanderLibraryQuery:
            commanderLibrary = Library(jobs=[])
        else:
            commanderLibrary = commanderLibraryQuery[0]
        # create library entry as long as filename doesn't already exist
        entriesQuery = commanderLibrary["jobs"].objects(filename__exact=filename)
        if entriesQuery:
            return {"error": f"file called '{filename}' already exists in the library"}
        commanderLibrary["jobs"].append(libraryEntry)
        # save executable file to server
        uploadedFile = request.files["file"]
        uploadedFile.save(app.config["UPLOADS_DIR"], filename)
        return {"success": "successfully added new executable to the commander library"}
    elif request.method == "PATCH":
        """ Update the file or description of an existing entry in the commander library """
        # TODO: check if update is for file or description
        # TODO: save new executable for existing library entry in db
        # or
        # TODO: update library description for file
        pass
    elif request.method == "DELETE":
        """ Delete an entry and its corresponding file from the commander library """
        # TODO: delete executable and existing library entry in db
        pass


@app.route("/admin/login", methods=["POST", "PATCH"])
def login():
    """ Authenticate an admin and return a new session token if successful """
    # TODO: hash password and check match
    if request.method == "POST":
        # TODO: generate authentication token and set expiration
        # TODO: return authentication token and expiration date
        pass
    elif request.method == "PATCH":
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
