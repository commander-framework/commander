import bcrypt
import os
import pytest
from server import app, agentDB, adminDB
from server.jobBoard import JobBoard
from server.models import Job, Library, Agent, RegistrationKey, User
import tempfile
from utils import utcNowTimestamp
from uuid import uuid4


@pytest.fixture(autouse=True)
def cleanup():
    yield
    # clean up database for next test
    agentDB.drop_database("agents")
    adminDB.drop_database("admins")


@pytest.fixture
def client():
    app.config["UPLOADS_DIR"] = tempfile.gettempdir() + os.path.sep
    app.config["LOG_LEVEL"] = 5
    app.testing = True
    yield app.test_client()


@pytest.fixture
def jobBoard():
    jobsCache = JobBoard()
    return jobsCache


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
    job = Job(jobID=str(uuid4()),
              executor="psh",
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
                  agentID=str(uuid4()),
                  os="windows",
                  lastCheckin=utcNowTimestamp(),
                  jobsQueue=[],
                  jobsRunning=[],
                  jobsHistory=[])
    return agent


@pytest.fixture
def sample_RegistrationKey():
    regKey = RegistrationKey(regKey=str(uuid4()))
    return regKey


@pytest.fixture
def sample_valid_JWT():
    # token generated with https://jwt.io/#debugger-io using default secret key
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsIm5hbWUiOiJKb2huIERvZSIsImlhdCI6MTUxNjIzOTAyMn0.DaLVgOpbaxsenHiV0LVW3D1z07TbDwo8qOp3OtoqACk"
    return token


@pytest.fixture
def sample_bad_sig_JWT():
    # token generated with https://jwt.io/#debugger-io using bad secret key
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    return token


@pytest.fixture
def sample_expired_JWT():
    # token generated with https://jwt.io/#debugger-io using default secret key
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzk5OTB9.qYidunY1JWO58V-LfgT_yWrKgcowodGp_ucFvL4hCOE"
    return token


@pytest.fixture
def sample_User():
    salt = bcrypt.gensalt()
    samplePass = "samplePass"
    hashedPass = bcrypt.hashpw(samplePass.encode(), salt)
    user = User(name="Test User",
                username="testuser",
                passwordHash=hashedPass.decode())
    return user