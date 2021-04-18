from flask import request
from server import app
from server.models import *


@app.route("/agent/register", methods=["POST"])
def register():
    # TODO: register client
    pass


@app.route("/agent/jobs", methods=["GET", "POST"])
def checkIn():
    if request.method == "GET":
        # TODO: check db for jobs
        # TODO: send most recent job to agent
        pass
    elif request.method == "POST":
        # TODO: validate operator authentication
        # TODO: save executable if not in library
        # TODO: add job to agent's queue in db
        pass


@app.route("/agent/library", methods=["GET", "POST"])
def library():
    if request.method == "GET":
        # TODO: return formatted library info
        pass
    elif request.methods == "POST":
        # TODO: save executable and generate library entry in db
        pass


@app.route("/operator/login", methods=["POST"])
def login():
    # TODO: check password hash
    # TODO: generate authentication token and set expiration
    # TODO: return authentication token
    pass


@app.route("/operator/reset-password", methods=["POST"])
def resetPassword():
    # TODO: check current password hash
    # TODO: change password
    pass
