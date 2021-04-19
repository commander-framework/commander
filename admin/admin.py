from datetime import datetime
from getpass import getpass
import json

import requests


class Administrator:
    def __init__(self, commanderServer):
        self.commanderServer = commanderServer
        self.username, self.authToken = self.getAuth()
        self.headers = {"Content-Type": "application/json",
                        "Username": self.username,
                        "Auth-Token": self.authToken}

    def getAuth(self):
        try:
            with open("token.json", "r") as authFile:
                creds = json.loads(authFile.read())
            if not creds:
                raise FileNotFoundError
            if not creds.authToken[0] or datetime.strptime(creds.authToken[1], "%m/%d/%Y, %H:%M:%S") < datetime.now():
                creds = self.login(creds.username)
                with open("token.json", "w") as authFile:
                    authFile.write(json.dumps(creds))
        except FileNotFoundError:
            creds = self.login()
        return creds.username, creds.authToken

    def login(self, username=None):
        if username:
            print("Authentication token not found or expired.")
            print(f"Please enter password for '{username}' to get a new token.")
        else:
            username = input("Username: ")
        password = getpass("Password: ")
        response = requests.get(self.commanderServer + "/admin/login",
                                headers={"Content-Type": "application/json"},
                                data={"Username": username, "Password": password})
        if "error" in response.json():
            print(f"Error submitting login info: {response.json()['error']}")
            print("Please try again.")
            creds = self.login()
        else:
            creds = response.json()
        return creds
