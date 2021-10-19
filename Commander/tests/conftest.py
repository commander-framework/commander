import bcrypt
from datetime import datetime, timedelta
import pytest
from server import app
from server.models import Job, Library, Agent, RegistrationKey, Session, User
from unittest import mock


@pytest.fixture
def client():
    app.testing = True
    yield app.test_client()


@pytest.fixture
def sample_Job():
    job = Job(executor="psh",
              filename="testfile",
              description="Test job description. This job is not real.",
              os="windows",
              user="testuser",
              timeCreated=datetime.now())
    return job


@pytest.fixture
def sample_Library():
    library = Library(jobs=[])
    library["jobs"].append(sample_Job)
    return library


@pytest.fixture
def sample_Agent():
    agent = Agent(hostname="testhost",
                  agentID="123456789",
                  os="windows",
                  lastCheckin=datetime.now(),
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
                      expires=datetime.now() + timedelta(hours=1))
    return session


@pytest.fixture
def sample_expired_Session():
    session = Session(username="testuser",
                      authToken="123456abcdef",
                      expires=datetime.now() + timedelta(hours=-1))
    return session


@pytest.fixture
def sample_User():
    salt = bcrypt.gensalt()
    samplePass = "samplePass"
    hashedPass = bcrypt.hashpw(samplePass, salt)
    user = User(name="Test User",
                username="testuser",
                passwordHash=hashedPass,
                sessions=[])
    user["sessions"].append(sample_valid_Session)
    user["sessions"].append(sample_expired_Session)
    return user