from mongoengine import Document, EmbeddedDocument, IntField, StringField, DateField, ListField, EmbeddedDocumentField


class Job(EmbeddedDocument):
    fileName = StringField(required=True)
    storagePath = StringField(required=True)
    description = StringField(required=True)
    user = StringField(required=True)
    timeSubmitted = DateField(required=True)
    timeRan = DateField()
    status = IntField()


class Agent(Document):
    _id = StringField(required=True)
    hostname = StringField(required=True)
    jobsQueue = ListField(EmbeddedDocumentField(Job))
    jobsHistory = ListField(EmbeddedDocumentField(Job))


class Library(Document):
    jobs = ListField(EmbeddedDocumentField(Job))


class Session(EmbeddedDocument):
    username = StringField(required=True)
    authToken = StringField(required=True)
    expires = DateField(required=True)


class User(Document):
    name = StringField(required=True)
    username = StringField(required=True)
    passwordHash = StringField(required=True)
    sessions = ListField(EmbeddedDocumentField(Session))
