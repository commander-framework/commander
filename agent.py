from multiprocessing import Process
import requests
from time import sleep


class CommanderAgent:
    def __init__(self, serverAddress):
        self.register(serverAddress)
        self.beacon = Process(target=self.checkIn)
        self.runner = Process(target=self.worker)
        self.exitSignal = False
        self.jobQueue = []

    def register(self, serverAddress):
        # TODO: generate client side cert to identify agent
        # TODO: contact server and register agent
        pass

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
