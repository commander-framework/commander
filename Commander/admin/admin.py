from datetime import datetime
from getpass import getpass
import json
import logging
from platform import system
import requests


class Administrator:
    def __init__(self, commanderServer, logLevel):
        self.log = self.logInit(logLevel)
        self.commanderServer = commanderServer
        self.clientCert = ("adminCert.crt", "adminKey.pem")
        self.serverCert = "commander.crt"
        self.username, self.authToken = self.getAuth()
        self.headers = {"Content-Type": "application/json",
                        "Username": self.username,
                        "Auth-Token": self.authToken}

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

    def getAuth(self):
        """ Fetch authentication token, or login and get one if no valid token is found """
        try:
            with open("token.json", "r") as authFile:
                creds = json.loads(authFile.read())
            if not creds:
                raise FileNotFoundError
            if not creds.authToken[0] or datetime.strptime(creds.authToken[1], "%m/%d/%Y, %H:%M:%S") < datetime.utcnow():
                creds = self.login(creds.username)
                with open("token.json", "w") as authFile:
                    authFile.write(json.dumps(creds))
        except FileNotFoundError:
            creds = self.login()
            self.resetPassword()
        return creds.username, creds.authToken

    def login(self, username=None):
        """ Login to Commander server and get new authentication token """
        if username:
            print("Authentication token not found or expired.")
            print(f"Please enter password for '{username}' to get a new token.")
        else:
            username = input("Username: ")
        password = getpass("Password: ")
        response = self.request("GET", "/admin/login",
                                headers={"Content-Type": "application/json"},
                                body={"Username": username, "Password": password})
        if "error" in response.json():
            print(f"Error submitting request: {response.json()['error']}")
            print("Please try again.")
            creds = self.login()
        else:
            creds = response.json()
        return creds

    def resetPassword(self):
        """ Reset password in Commander server for logged in user """
        print(f"Resetting password for '{self.username}'")
        currentPassword = getpass("Current password: ")
        newPassword = getpass("New password: ")
        confirm = getpass("Confirm new password: ")
        while newPassword != confirm:
            print("Passwords do not match, please try again.")
            newPassword = getpass("New password: ")
            confirm = getpass("Confirm new password: ")
        response = self.request("PATCH", "/admin/login",
                                body={"username": self.username,
                                      "current": currentPassword,
                                      "new": newPassword})
        if "error" in response.json():
            print(f"Error submitting request: {response.json()['error']}")
            print("Please try again.")
        else:
            print(f"Successfully changed password for '{self.username}'")

    def generateRegistrationKey(self):
        """ Reset and fetch registration key to register new clients """
        response = self.request("GET", "/admin/generate-registration-key")
        if "error" in response.json():
            print(f"Error submitting request: {response.json()['error']}")
            print("Please try again.")
        else:
            print(f"Registration Key: {response.json()['registration-key']}")

    def executionRequest(self, hostname, filename):
        """ Send a file from the Commander library to the given host and execute it """
        response = self.request("POST", "/agent/jobs",
                                body={"hostname": hostname,
                                      "filename": filename})
        if "error" in response.json():
            print(f"Error submitting request: {response.json()['error']}")
            print("Please try again.")
        else:
            print("Successfully submitted execution request.")

    def getExecutionLibrary(self):
        """ Receive the execution library from Commander and format output """
        response = self.request("GET", "/admin/library")
        if "error" in response.json():
            print(f"Error submitting request: {response.json()['error']}")
            print("Please try again.")
        else:
            library = json.loads(response.json())
            for executable in library:
                print(f"<-- {executable['fileName']} -->")
                print(f"Submitted by: {executable['user']} on {executable['timeSubmitted']}")
                print(f"Description: {executable['description']}")

    def newExecutable(self, filePath, description=""):
        """ Upload a new executable to the Commander library """
        if "/" in filePath:
            filename = filePath[filePath.rindex("/"):]
        elif "\\" in filePath:
            filename = filePath[filePath.rindex("\\"):]
        else:
            filename = filePath
        try:
            with open(filePath, "r") as executable:
                response = self.request("POST", "/admin/library",
                                        files={"executable": executable},
                                        body={"filename": filename,
                                              "description": description})
                if "error" in response.json():
                    print(f"Error submitting request: {response.json()['error']}")
                    print("Please try again.")
                else:
                    print(f"Successfully added {filename} to the Commander library.")
        except FileNotFoundError:
            print("File not found, please check file path and try again.")

    def deleteExecutable(self, filename):
        """ Delete an executable from the Commander library """
        response = self.request("DELETE", "/admin/library",
                                body={"filename": filename})
        if "error" in response.json():
            print(f"Error submitting request: {response.json()['error']}")
            print("Please try again.")
        else:
            print(f"Successfully deleted {filename} from the Commander library.")

    def updateExecutable(self, filename, filePath):
        """ Upload an updated version of an executable to the Commander library """
        try:
            with open(filePath, "r") as executable:
                response = self.request("PATCH", "/admin/library",
                                        files={"executable": executable},
                                        body={"filename": filename})
                if "error" in response.json():
                    print(f"Error submitting request: {response.json()['error']}")
                    print("Please try again.")
                else:
                    print(f"Successfully updated {filename} in the Commander library.")
        except FileNotFoundError:
            print("File not found, please check file path and try again.")

    def updateDescription(self, filename, description):
        """ Update the description of an executable in the Commander library """
        response = self.request("PATCH", "/admin/library",
                                body={"filename": filename,
                                      "description": description})
        if "error" in response.json():
            print(f"Error submitting request: {response.json()['error']}")
            print("Please try again.")
        else:
            print(f"Successfully updated the description of {filename} in the Commander library.")

    def logInit(self, logLevel):
        """ Configure log level (1-5) and OS-dependent log file location """
        # set log level
        level = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL][5-logLevel]
        logging.basicConfig(level=level)
        log = logging.getLogger("CommanderAgent")
        formatter = logging.Formatter(fmt="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
                                      datefmt="%Y-%m-%d %H:%M:%S")
        os = system()
        if os == "Linux" or os == "Darwin":
            handler = logging.TimedRotatingFileHandler(filename="/var/log/commander.log",
                                                   encoding="utf-8",
                                                   when="D",  # Daily
                                                   backupCount=7)
        elif os == "Windows":
            handler = logging.TimedRotatingFileHandler(filename="commander.log",
                                                   encoding="utf-8",
                                                   when="D",  # Daily
                                                   backupCount=7)
        handler.setFormatter(formatter)
        log.addHandler(handler)
        return log
