from config import Config
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sock import Sock
import logging
from .models import User
from mongoengine import connect

# initialize app
app = Flask(__name__)
app.config.from_object(Config)
sock = Sock(app)
jwt = JWTManager(app)

# set logging options
level = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL][5-Config.LOG_LEVEL]
fmt = "%(asctime)s.%(msecs)03d %(levelname)-8s [%(name)s"
if Config.LOG_LEVEL == 5:  # debug
    fmt += ".%(funcName)s:%(lineno)d"
fmt += "] %(message)s"
logging.basicConfig(level=level,
                    format=fmt,
                    datefmt='%Y-%m-%dT%H:%M:%S')
log = logging.getLogger(Config.APP_NAME)

#connect to DB
agentDB = connect(db="agents",
                  alias="agent_db",
                  username=Config.DB_USER,
                  password=Config.DB_PASS,
                  host=Config.DB_URI)
adminDB = connect(db="admins",
                  alias="admin_db",
                  username=Config.DB_USER,
                  password=Config.DB_PASS,
                  host=Config.DB_URI)

# create first admin if it doesn't already exist
adminQuery = User.objects(username="admin")
if not adminQuery:
    defaultAdmin = User(username="admin",
                   name="Default Admin",
                   passwordHash=Config.ADMIN_HASH)
    defaultAdmin.save()
    log.info("Created admin user")

# initialize jobBoard cache
from .jobBoard import JobBoard
jobsCache = JobBoard()

from server import errors
from server.routes import admin, agent
