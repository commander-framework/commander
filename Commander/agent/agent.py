from multiprocessing import Process
import requests
from time import sleep


class CommanderAgent:
    def __init__(self, serverAddress):
        self.clientCert = ("agentCert.crt", "agentKey.pem")
        self.serverCert = "commander.crt"
        self.agentID = self.register(serverAddress)
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

    def register(self, serverAddress):
        # TODO: check for existing config to see if agent is already registered
        # TODO: if not, contact server and register agent (use hostname in header instead of agentID)
        # TODO: modify config if newly registered
        agentID = ""
        return agentID

    def checkIn(self):
        while not self.exitSignal:
            # TODO: send request to server
            # TODO: download executable and create job
            sleep(5)

    def execute(self, filePath):
        pass

    def cleanup(self, filePath):
        pass

    def worker(self):
        while not self.exitSignal:
            if self.jobQueue:
                job = Process(target=self.execute, args=(self.jobQueue[0]))
                job.start()
                self.jobQueue.pop(0)
            sleep(3)

    def run(self):
        self.beacon.start()
        self.runner.start()
        self.beacon.join()
        self.runner.join()
