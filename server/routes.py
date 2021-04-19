from flask import request
import json
import requests
from server import app
from server.models import *


@app.route("/agent/generate", methods=["GET"])
def generateAgentInstaller():
    # TODO: check admin authentication token
    # TODO: check OS version
    # TODO: request installer client cert from CA
    # TODO: build executable installer
    # TODO: return installer
    pass


@app.route("/agent/register", methods=["POST"])
def register():
    # TODO: check registration key
    pass


@app.route("/agent/jobs", methods=["GET", "POST"])
def jobs():
    if request.method == "GET":
        # TODO: check db for jobs
        # TODO: send most recent job to agent
        pass
    elif request.method == "POST":
        # TODO: check admin authentication token
        # TODO: save executable if not in library
        # TODO: add job to agent's queue in db
        pass


@app.route("/admin/library", methods=["GET", "POST", "PATCH", "DELETE"])
def library():
    # TODO: check admin authentication token
    if request.method == "GET":
        # TODO: return simplified library json
        pass
    elif request.method == "POST":
        # TODO: save executable and generate library entry in db
        pass
    elif request.method == "PATCH":
        # TODO: check if update is for file or description
        # TODO: save new executable for existing library entry in db
        # or
        # TODO: update library description for file
        pass
    elif request.method == "DELETE":
        # TODO: delete executable and existing library entry in db
        pass


@app.route("/admin/login", methods=["POST", "PATCH"])
def login():
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
    # TODO: check admin authentication token
    # TODO: set registration key in db
    # TODO: return key
    pass
