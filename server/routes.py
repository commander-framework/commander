from flask import request
import json
import requests
from server import app
from server.models import *


@app.route("/agent/generate", methods=["GET"])
def generateAgentInstaller():
    # TODO: check admin authentication token
    # TODO: check OS version
    osVersion = json.loads(request.json)
    # TODO: request installer client cert from CA
    # TODO: build executable installer
    # TODO: return installer
    pass


@app.route("/agent/register", methods=["POST"])
def register():
    # TODO: check registration key
    pass


@app.route("/agent/jobs", methods=["GET", "POST"])
def checkIn():
    if request.method == "GET":
        # TODO: check db for jobs
        # TODO: send most recent job to agent
        pass
    elif request.method == "POST":
        # TODO: check admin authentication token
        # TODO: save executable if not in library
        # TODO: add job to agent's queue in db
        pass


@app.route("/agent/library", methods=["GET", "POST"])
def library():
    # TODO: check admin authentication token
    if request.method == "GET":
        # TODO: return formatted library info
        pass
    elif request.methods == "POST":
        # TODO: save executable and generate library entry in db
        pass


@app.route("/admin/login", methods=["POST"])
def login():
    # TODO: hash password and check match
    # TODO: generate authentication token and set expiration
    # TODO: return authentication token and expiration date
    pass


@app.route("/admin/reset-password", methods=["POST"])
def resetPassword():
    # TODO: check current password hash
    # TODO: change password
    pass


@app.route("/admin/generate-registration-key", methods=["GET"])
def genRegistrationKey():
    # TODO: check admin authentication token
    # TODO: set registration key in db
    # TODO: return key
    pass
