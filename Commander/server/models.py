from mongoengine import Document, EmbeddedDocument, IntField, StringField, \
                        DateTimeField, ListField, EmbeddedDocumentField


class Job(EmbeddedDocument):
    fileName = StringField(required=True)
    description = StringField(required=True)
    user = StringField(required=True)
    timeSubmitted = DateTimeField(required=True)
    timeRan = DateTimeField()
    status = IntField()
    meta = {"db_alias": "agent_db"}


class Agent(Document):
    hostname = StringField(required=True)
    jobsQueue = ListField(EmbeddedDocumentField(Job))
    jobsHistory = ListField(EmbeddedDocumentField(Job))
    meta = {"db_alias": "agent_db"}


class Library(Document):
    jobs = ListField(EmbeddedDocumentField(Job))
    meta = {"db_alias": "agent_db"}


class Session(EmbeddedDocument):
    username = StringField(required=True)
    authToken = StringField(required=True)
    expires = DateTimeField(required=True)
    meta = {"db_alias": "admin_db"}


class User(Document):
    name = StringField(required=True)
    username = StringField(required=True)
    passwordHash = StringField(required=True)
    sessions = ListField(EmbeddedDocumentField(Session))
    meta = {"db_alias": "admin_db"}
