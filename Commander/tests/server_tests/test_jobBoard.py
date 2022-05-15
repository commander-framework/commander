from copy import deepcopy
import gevent
import json
from server import jobsCache

def test_assignJob(sample_Job, sample_Agent):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    agent.save()
    # assign job to agent
    jobsCache.assignJob(sample_Job, agentID=agent["agentID"])
    agent.reload()
    assert json.loads(sample_Job.to_json()) in jobsCache.agentCheckin(agent["agentID"])
    assert sample_Job in agent["jobsQueue"]


def test_noIdAssignJob(sample_Job):
    try:
        jobsCache.assignJob(sample_Job)
    except ValueError as e:
        assert "must specify either agentID or groupID when assigning a job" == str(e)


def test_async_assignJob(sample_Job, sample_Agent):
    # prepare mongomock and relevant sample documents
    agent = sample_Agent
    agent.save()
    sample_Job1 = deepcopy(sample_Job)
    sample_Job1.filename = "proc1"
    sample_Job2 = deepcopy(sample_Job)
    sample_Job2.filename = "proc2"
    sample_Job3 = deepcopy(sample_Job)
    sample_Job3.filename = "proc3"
    sample_Job4 = deepcopy(sample_Job)
    sample_Job4.filename = "proc4"
    # assign multiple jobs to agent in parallel
    gevent.joinall([gevent.spawn(jobsCache.assignJob, sample_Job1, agent["agentID"]),
                    gevent.spawn(jobsCache.assignJob, sample_Job2, agent["agentID"]),
                    gevent.spawn(jobsCache.assignJob, sample_Job3, agent["agentID"]),
                    gevent.spawn(jobsCache.assignJob, sample_Job4, agent["agentID"])])
    agent.reload()
    assert json.loads(sample_Job1.to_json()) in jobsCache.agentCheckin(agent["agentID"])
    assert json.loads(sample_Job2.to_json()) in jobsCache.agentCheckin(agent["agentID"])
    assert json.loads(sample_Job3.to_json()) in jobsCache.agentCheckin(agent["agentID"])
    assert json.loads(sample_Job4.to_json()) in jobsCache.agentCheckin(agent["agentID"])
    assert len(jobsCache.agentCheckin(agent["agentID"])) == 4
    assert sample_Job1 in agent["jobsQueue"]
    assert sample_Job2 in agent["jobsQueue"]
    assert sample_Job3 in agent["jobsQueue"]
    assert sample_Job4 in agent["jobsQueue"]
    assert len(agent["jobsQueue"]) == 4