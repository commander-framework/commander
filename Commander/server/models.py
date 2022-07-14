from mongoengine import Document, EmbeddedDocument, IntField, StringField, \
                        ListField, EmbeddedDocumentField
from mongoengine.pymongo_support import LEGACY_JSON_OPTIONS

class LegacyDocument(Document):
    meta = {'allow_inheritance': True}
    def to_json(self, *args, **kwargs):
        return super().to_json(*args, json_options=LEGACY_JSON_OPTIONS, **kwargs)
    def from_json(cls, json_data, created=False, **kwargs):
        return super().from_json(cls, json_data, created, json_options=LEGACY_JSON_OPTIONS, **kwargs)

class Job(EmbeddedDocument):
    jobID = StringField()
    executor = StringField(required=True)
    filename = StringField(required=True)
    description = StringField(required=True)
    os = StringField(required=True)
    user = StringField()
    timeCreated = StringField()
    timeDispatched = StringField()
    timeStarted = StringField()
    timeEnded = StringField()
    argv = ListField(StringField())
    exitCode = IntField()
    stdout = StringField()
    stderr = StringField()
    meta = {"db_alias": "agent_db"}
    def to_json(self, *args, **kwargs):
        return super().to_json(*args, json_options=LEGACY_JSON_OPTIONS, **kwargs)
    def from_json(cls, json_data, created=False, **kwargs):
        return super().from_json(cls, json_data, created, json_options=LEGACY_JSON_OPTIONS, **kwargs)


class Library(LegacyDocument):
    jobs = ListField(EmbeddedDocumentField(Job))
    meta = {"db_alias": "agent_db"}


class Agent(LegacyDocument):
    hostname = StringField(required=True)
    agentID = StringField(required=True)
    os = StringField(required=True)
    lastCheckin = StringField(required=True)
    jobsQueue = ListField(EmbeddedDocumentField(Job))
    jobsRunning = ListField(EmbeddedDocumentField(Job))
    jobsHistory = ListField(EmbeddedDocumentField(Job))
    meta = {"db_alias": "agent_db"}


class RegistrationKey(LegacyDocument):
    regKey = StringField(required=True)
    meta = {"db_alias": "admin_db"}


class User(LegacyDocument):
    name = StringField(required=True)
    username = StringField(required=True)
    passwordHash = StringField(required=True)
    meta = {"db_alias": "admin_db"}
