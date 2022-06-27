from flask import request, send_from_directory
import json
from ..models import Agent, Job, RegistrationKey
from os import path
from server import app, jobsCache, log, sock
from simple_websocket import ConnectionClosed, ConnectionError
from time import sleep
from types import SimpleNamespace
from utils import utcNowTimestamp
from uuid import uuid4
from .validation import missing


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
    # monitor for jobs to send to the agent
    agent = agentQuery[0]
    log.debug(f"<{ws.sock.getpeername()[0]}> agent {agent['agentID']} ({agent['hostname']}) listening for jobs")
    while True:
        try:
            # check db for jobs
            jobs = jobsCache.agentCheckin(agent["agentID"])  # TODO: implement agent groups
            if not jobs:
                sleep(1)
                continue
            # send jobs to agent
            log.info(f"<{ws.sock.getpeername()[0]}> sending jobs to agent {agent['agentID']} ({agent['hostname']})")
            ws.send(json.dumps({"jobs": jobs}))
            # wait for acknowledgement from agent before marking job as running
            ack = ws.receive()
            if ack != "ack":
                continue
            # mark jobs as received by the agent
            log.info(f"<{ws.sock.getpeername()[0]}> marking jobs as received by agent {agent['agentID']} ({agent['hostname']})")
            jobIDs = [job["jobID"] for job in jobs]
            jobsCache.markSent(jobIDs, agent["agentID"])
            # stop checking for jobs if we are testing this function, otherwise continue watching for jobs
            if "isMockServer" in ws.__dict__:
                raise ConnectionClosed(1006, "mock server")
        except (ConnectionClosed, ConnectionError):
            # connection lost; update lastCheckin and close the socket
            log.debug(f"<{ws.sock.getpeername()[0]}> agent {agent['agentID']} ({agent['hostname']}) connection closed")
            agent.update(lastCheckin=utcNowTimestamp())
            agent.save()
            break


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
    finishedJob = request.json["job"]
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
