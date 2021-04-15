from multiprocessing import Process
import requests


class CommanderAgent:
    def __init__(self, serverAddress):
        self.register(serverAddress)
        self.beacon = Process(target=self.checkIn)
        self.runner = Process(target=self.worker)
        self.exitSignal = False

    def register(self, serverAddress):
        pass

    def checkIn(self):
        while not self.exitSignal:
            pass

    def execute(self, filePath):
        pass

    def cleanup(self, filePath):
        pass

    def worker(self):
        pass

    def run(self):
        self.beacon.start()
        self.runner.start()
        self.beacon.join()
        self.runner.join()
