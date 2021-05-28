import json
from multiprocessing import Process
import requests
from socket import gethostname
from time import sleep


class CommanderAgent:
    def __init__(self, serverAddress="", registrationKey=""):
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

    def request(self, method, directory, body=None, headers=None, files=None):
        """ HTTPS request to Commander server using client and server verification """
        if headers is None:
            headers = self.headers
        if body is None:
            body = {}  # set here to prevent mutating default arg
        if files is None:
            files = {}
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
                                    body={"hostname": gethostname(),
                                          "registrationKey": self.registrationKey})
            # create config and save to disk
            if "error" in response.json:
                raise ValueError(response.json()["error"])
            configJson = {"hostname": gethostname(),
                          "agentID": response.json()["agentID"],
                          "commanderServer": self.commanderServer}
            with open("agentConfig.json", "w+") as configFile:
                configFile.write(json.dumps(configJson))
        return configJson["agentID"]

    def checkIn(self):
        """ Check in with the commander server to see if there are any jobs to run """
        while not self.exitSignal:
            # TODO: send request to server
            response = self.request("GET", "/agent/jobs",
                                    body={""})
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
                job = Process(target=self.execute, args=(self.jobQueue[0]))
                job.start()
                self.jobQueue.pop(0)
            sleep(3)

    def run(self):
        """ Start agent """
        self.beacon.start()
        self.runner.start()
        self.beacon.join()
        self.runner.join()
