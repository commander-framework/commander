import bcrypt
import os
import pytest
from server import app
from server.models import Job, Library, Agent, RegistrationKey, Session, User
import tempfile
from utils import utcNowTimestamp


@pytest.fixture
def client():
    app.config["UPLOADS_DIR"] = tempfile.gettempdir() + os.path.sep
    app.testing = True
    yield app.test_client()


@pytest.fixture
def sample_JobFile():
    tempdir = tempfile.gettempdir() + os.path.sep
    with open(tempdir + "testfile", "wb") as f:
        f.write(b'test content')
    yield "testfile"
    if os.path.isfile(tempdir + "testfile"):
        os.remove(tempdir + "testfile")



@pytest.fixture
def sample_Job():
    job = Job(executor="psh",
              filename="testfile",
              description="Test job description. This job is not real.",
              os="windows",
              user="testuser",
              timeCreated=utcNowTimestamp())
    return job


@pytest.fixture
def sample_Library():
    library = Library(jobs=[])
    return library


@pytest.fixture
def sample_Agent():
    agent = Agent(hostname="testhost",
                  agentID="123456789",
                  os="windows",
                  lastCheckin=utcNowTimestamp(),
                  jobsQueue=[],
                  jobsRunning=[],
                  jobsHistory=[])
    return agent


@pytest.fixture
def sample_RegistrationKey():
    regKey = RegistrationKey(regKey="abcdef123456")
    return regKey


@pytest.fixture
def sample_valid_Session():
    session = Session(username="testuser",
                      authToken="abcdef123456",
                      expires=utcNowTimestamp(deltaHours=1))
    return session


@pytest.fixture
def sample_expired_Session():
    session = Session(username="testuser",
                      authToken="123456abcdef",
                      expires=utcNowTimestamp(deltaHours=-1))
    return session


@pytest.fixture
def sample_User():
    salt = bcrypt.gensalt()
    samplePass = "samplePass"
    hashedPass = bcrypt.hashpw(samplePass.encode(), salt)
    user = User(name="Test User",
                username="testuser",
                passwordHash=hashedPass.decode(),
                sessions=[])
    return user