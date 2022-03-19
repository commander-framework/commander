from config import Config
from flask import Flask
from flask_sock import Sock
from mongoengine import connect

app = Flask(__name__)
app.config.from_object(Config)
sock = Sock(app)

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

from . import routes
