from multiprocessing import Process

def test_assignJob(jobBoard, sample_Job, sample_Agent):
    # prepare mongomock with relevant sample documents
    agent = sample_Agent
    agent.save()
    # assign job to agent
    jobsCache = jobBoard
    jobsCache.assignJob(sample_Job, agentID=agent["agentID"])
    agent.reload()
    assert sample_Job in jobsCache.jobAssignments["agents"][agent["agentID"]]
    assert sample_Job in agent["jobsQueue"]


def test_noIdAssignJob(jobBoard, sample_Job):
    jobsCache = jobBoard
    try:
        jobsCache.assignJob(sample_Job)
    except ValueError as e:
        assert "must specify either agentID or groupID when assigning a job" == str(e)


# def test_async_assignJob(jobBoard, sample_Job, sample_Agent):
#     # prepare mongomock with relevant sample documents
#     agent = sample_Agent
#     agent.save()
#     # assign multiple jobs to agent in parallel
#     jobsCache = jobBoard
#     p1 = Process(target=jobsCache.assignJob, args=(sample_Job, agent["agentID"]))
#     p2 = Process(target=jobsCache.assignJob, args=(sample_Job, agent["agentID"]))
#     p3 = Process(target=jobsCache.assignJob, args=(sample_Job, agent["agentID"]))
#     p4 = Process(target=jobsCache.assignJob, args=(sample_Job, agent["agentID"]))
#     p1.start()
#     p2.start()
#     p3.start()
#     p4.start()
#     p1.join()
#     p2.join()
#     p3.join()
#     p4.join()
#     agent.reload()
#     assert sample_Job in jobsCache.jobAssignments["agents"][agent["agentID"]]
#     assert len(jobsCache.jobAssignments["agents"][agent["agentID"]]) == 4
#     assert sample_Job in agent["jobsQueue"]
#     assert len(agent["jobsQueue"]) == 4