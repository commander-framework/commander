from config import Config
from flask import Flask
from mongoengine import connect

app = Flask(__name__)
app.config.from_object(Config)

connect(db=Config.DB_NAME,
        username=Config.DB_USER,
        password=Config.DB_PASS,
        host=Config.DB_URI)
