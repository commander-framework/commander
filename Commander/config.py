import os


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or "super-secret-default-key"
    DB_USER = os.environ.get("DB_USER") or None
    DB_PASS = os.environ.get("DB_PASS") or None
    DB_URI = os.environ.get("DB_URI") or None
    UPLOADS_DIR = os.environ.get("UPLOADS_DIR") or "/opt/commander/library/"
