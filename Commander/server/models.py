from mongoengine import Document, EmbeddedDocument, IntField, StringField, \
                        DateTimeField, ListField, EmbeddedDocumentField


class Job(EmbeddedDocument):
    executor = StringField(required=True)
    fileName = StringField(required=True)
    description = StringField(required=True)
    os = StringField(required=True)
    user = StringField(required=True)
    timeCreated = DateTimeField(required=True)
    timeDispatched = DateTimeField()
    timeStarted = DateTimeField()
    timeEnded = DateTimeField()
    argv = ListField(StringField())
    status = IntField()
    stdout = StringField()
    stderr = StringField()
    meta = {"db_alias": "agent_db"}


class Agent(Document):
    hostname = StringField(required=True)
    agentID = StringField(required=True)
    os = StringField(required=True)
    lastCheckin = DateTimeField(required=True)
    jobsQueue = ListField(EmbeddedDocumentField(Job))
    jobsRunning = ListField(EmbeddedDocumentField(Job))
    jobsHistory = ListField(EmbeddedDocumentField(Job))
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
