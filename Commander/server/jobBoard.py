from config import Config
import json
from .models import Agent
import redis
from server import log
from utils import utcNowTimestamp


class JobBoard:
    def __init__(self):
        self.refresh()

    def assignJob(self, job, agentID=None, groupID=None):
        """ Assign a job to an agent. Update the DB and cache the job in jobAssignments. """
        jobsCache = redis.from_url(Config.REDIS_URI)
        if not agentID and not groupID:
            raise ValueError("must specify either agentID or groupID when assigning a job")
        if agentID:
            # update DB first and make sure agent exists
            agent = Agent.objects(agentID=agentID).first()
            if not agent:
                raise ValueError("no hosts found matching the agentID in the request")
            agent.jobsQueue.append(job)
            agent.save()
            # add job to cache
            with jobsCache.lock("assign_job"):
                with jobsCache.pipeline() as pipe:
                    agentJobs = jobsCache.get(f"agent:{agentID}")
                    if not agentJobs or agentJobs == b'null':
                        pipe.set(f"agent:{agentID}", f"[{job.to_json()}]")
                        print(f"Added job '{job.filename}' to empty job queue for agent {agentID}")
                    else:
                        updatedJobs = json.loads(agentJobs).append(json.loads(job.to_json()))
                        pipe.set(f"agent:{agentID}", json.dumps(updatedJobs))
                        print(f"Added job '{job.filename}' to existing job queue for agent {agentID}")
                    pipe.execute()
        elif groupID:
            # update DB first and make sure group exists
            agents = Agent.objects(groups__icontains=groupID)
            if not agents.first():
                raise ValueError("no hosts found matching the groupID in the request")
            agents.update(push__jobsQueue=job)
            # add job to each agent in cache
            agentIDs = [agent.agentID for agent in agents]
            with jobsCache.lock("assign_job"):
                with jobsCache.pipeline() as pipe:
                    jobs = jobsCache.mget(agentIDs)
                    for agentID, agentJobs in zip(agentIDs, jobs):
                        if not agentJobs or agentJobs == b'null':
                            pipe.set(f"agent:{agentID}", f"[{job.to_json()}]")
                            log.debug(f"Created job queue for agent {agentID} and added job '{job.filename}'")
                        else:
                            updatedJobs = json.loads(agentJobs).append(json.loads(job.to_json()))
                            pipe.set(f"agent:{agentID}", json.dumps(updatedJobs))
                            log.debug(f"Added job '{job.filename}' to existing job queue for agent {agentID}")
                    pipe.execute()

    def agentCheckin(self, agentID):
        """ Check if the agent has jobs in its queue """
        jobsCache = redis.from_url(Config.REDIS_URI)
        agentJobs = jobsCache.get(f"agent:{agentID}")
        if not agentJobs:
            return None
        agentJobs = json.loads(agentJobs.decode("utf-8"))
        # a job is available, return agent's job from the cache
        return agentJobs


    def markSent(self, agentID, jobIDs):
        """ Remove first job from agent's cache and transfer from jobsQueue to jobsRunning in DB. """
        jobsCache = redis.from_url(Config.REDIS_URI)
        # update DB first
        agent = Agent.objects(agentID=agentID).first()
        for job in agent.jobsQueue:
            if job["jobID"] in jobIDs:
                job = agent.jobsQueue.pop(agent.jobsQueue.index(job))
                job["timeDispatched"] = utcNowTimestamp()
                agent["jobsRunning"].append(job)
                agent["lastCheckin"] = utcNowTimestamp()
        agent.save()
        # update cache
        agentJobs = json.loads(jobsCache.get(f"agent:{agentID}").decode("utf-8"))
        for job in agentJobs:
            if job["jobID"] in jobIDs:
                agentJobs.pop(agentJobs.index(job))
        if not agentJobs:
            jobsCache.delete(f"agent:{agentID}")
        else:
            jobsCache.set(f"agent:{agentID}", json.dumps(agentJobs))



    def refresh(self):
        """ Refresh the job assignments cache from the DB. """
        jobsCache = redis.from_url(Config.REDIS_URI)
        agentsQuery = Agent.objects()
        jobsCache.flushdb()
        with jobsCache.pipeline() as pipe:
            for agent in agentsQuery:
                if agent["jobsQueue"]:
                    jobsJson = [json.loads(job.to_json()) for job in sorted(agent["jobsQueue"], key = lambda i: i["timeCreated"])]
                    pipe.set(f"agent:{agent['agentID']}", json.dumps(jobsJson))
            # TODO: build groups cache once groups are implemented
            pipe.execute()
