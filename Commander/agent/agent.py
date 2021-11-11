import json
import logging
from logging.handlers import TimedRotatingFileHandler
from multiprocessing import Process, Lock
from platform import system
import requests
from socket import gethostname
from time import sleep


class CommanderAgent:
    def __init__(self, serverAddress="", registrationKey="", logLevel=3):
        self.os = system()
        self.log = self.logInit(logLevel)
        self.clientCert = ("agentCert.crt", "agentKey.pem")
        self.serverCert = "commander.crt"
        self.commanderServer = serverAddress
        self.registrationKey = registrationKey
        self.agentID = self.register()
        if not self.commanderServer:
            raise ValueError("server address was not included in the installer or was not found in existing config")
        self.headers = {"Content-Type": "application/json",
                        "agentID": self.agentID}
        self.beacon = Process(target=self.checkIn)
        self.runner = Process(target=self.worker)
        self.exitSignal = False
        self.jobQueue = []
        self.jobQueueLock = Lock()
        self.connectedToServer = True

    def request(self, method, directory, body=None, headers=None, files=None):
        """ HTTPS request to Commander server using client and server verification """
        if headers is None:
            headers = self.headers
        if body is None:
            body = {}  # set here to prevent mutating default arg
        if files is None:
            files = {}
        try:
            if method == "GET":
                response = requests.get(f"https://{self.commanderServer}{directory}",
                                        headers=headers,
                                        cert=self.clientCert,
                                        verify=self.serverCert,
                                        data=body)
            elif method == "POST":
                response = requests.post(f"https://{self.commanderServer}{directory}",
                                        headers=headers,
                                        cert=self.clientCert,
                                        verify=self.serverCert,
                                        data=body,
                                        files=files)
            elif method == "PUT":
                response = requests.put(f"https://{self.commanderServer}{directory}",
                                        headers=headers,
                                        cert=self.clientCert,
                                        verify=self.serverCert,
                                        data=body,
                                        files=files)
            elif method == "DELETE":
                response = requests.delete(f"https://{self.commanderServer}{directory}",
                                        headers=headers,
                                        cert=self.clientCert,
                                        verify=self.serverCert,
                                        data=body,
                                        files=files)
            else:  # method == "PATCH":
                response = requests.patch(f"https://{self.commanderServer}{directory}",
                                        headers=headers,
                                        cert=self.clientCert,
                                        verify=self.serverCert,
                                        data=body,
                                        files=files)
        except ConnectionError:
            # only log one failure until it connects again
            if self.connectedToServer:
                self.log.warning("Unable to contact server")
                self.connectedToServer = False
        except Exception as e:
            self.log.critical(e)
            exit(1)
        self.connectedToServer = True
        return response

    def register(self):
        """ Register agent with the commander server or fetch existing configuration """
        # check for existing config to see if agent is already registered
        try:
            with open("agentConfig.json", "r") as configFile:
                configJson = json.loads(configFile.read())
                if not configJson:
                    raise FileNotFoundError
        except FileNotFoundError:
            # contact server and register agent
            response = self.request("POST", "/agent/register",
                                    headers={"Content-Type": "application/json"},
                                    body={"registrationKey": self.registrationKey,
                                            "hostname": gethostname(),
                                            "os": self.os})
            # create config and save to disk
            if "error" in response.json:
                self.log.error("HTTP"+str(response.status_code)+": "+response.json["error"])
            configJson = {"hostname": gethostname(),
                          "agentID": response.json()["agentID"],
                          "commanderServer": self.commanderServer}
            with open("agentConfig.json", "w+") as configFile:
                configFile.write(json.dumps(configJson))
        return configJson["agentID"]

    def checkIn(self):
        """ Check in with the commander server to see if there are any jobs to run """
        logError = True
        while not self.exitSignal:
            # send request to server
            response = self.request("GET", "/agent/jobs")
            if response.status_code != 200:
                if logError:
                    self.log.error("HTTP"+str(response.status_code)+": "+response.json["error"])
                    logError = False
                sleep(5)
                continue
            logError = True
            # TODO: download executable and create job
            sleep(5)

    def execute(self, filePath):
        """ Call the executable for a job and return its output and execution status """
        pass

    def cleanup(self, filePath):
        """ Remove executable for a job and send execution status back to commander server """
        pass

    def worker(self):
        """ Asynchronously execute jobs from commander server """
        while not self.exitSignal:
            if self.jobQueue:
                with self.jobQueueLock:
                    job = Process(target=self.execute, args=(self.jobQueue.pop(0)))
                    job.start()
            sleep(5)

    def logInit(self, logLevel):
        """ Configure log level (1-5) and OS-dependent log file location """
        # set log level
        level = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL][5-logLevel]
        logging.basicConfig(level=level, format="%(levelname)-8s: %(message)s")
        log = logging.getLogger("CommanderAgent")
        formatter = logging.Formatter(fmt="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
                                      datefmt="%Y-%m-%d %H:%M:%S")
        if self.os == "Linux" or self.os == "Darwin":
            handler = TimedRotatingFileHandler(filename="/var/log/commander.log",
                                                   encoding="utf-8",
                                                   when="D",  # Daily
                                                   backupCount=7)
        elif self.os == "Windows":
            handler = TimedRotatingFileHandler(filename="commander.log",
                                                   encoding="utf-8",
                                                   when="D",  # Daily
                                                   backupCount=7)
        handler.setFormatter(formatter)
        log.addHandler(handler)
        return log

    def run(self):
        """ Start agent """
        self.beacon.start()
        self.runner.start()
        self.beacon.join()
        self.runner.join()
