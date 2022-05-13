from config import Config
import json
from .models import Agent
import redis
from utils import utcNowTimestamp


class JobBoard:
    def __init__(self):
        self.josbsCache = redis.from_url(Config.REDIS_URI)
        self.refresh()

    def assignJob(self, job, agentID=None, groupID=None):
        """ Assign a job to an agent. Update the DB and cache the job in jobAssignments. """
        if not agentID and not groupID:
            raise ValueError("must specify either agentID or groupID when assigning a job")
        # add job to DB and cache
        if agentID:
            # update DB first and make sure agent exists
            agent = Agent.objects(agentID=agentID).first()
            if not agent:
                raise ValueError("no hosts found matching the agentID in the request")
            agent.jobsQueue.append(job)
            agent.save()
            # add job to cache
            agentJobs = self.jobsCache.get(f"agent:{agentID}").decode("utf-8")
            if not agentJobs:
                self.jobsCache.set(f"agent:{agentID}", json.dumps([job]))
            else:
                updatedJobs = json.loads(agentJobs).append(job)
                self.jobsCache.set(f"agent:{agentID}", json.dumps(updatedJobs))
        elif groupID:
            # update DB first and make sure group exists
            agents = Agent.objects(groups__icontains=groupID)
            if not agents.first():
                raise ValueError("no hosts found matching the groupID in the request")
            agents.update(push__jobsQueue=job)
            # add job to each agent in cache
            with self.jobsCache.pipeline() as pipe:
                for agent in agents:
                    agentJobs = self.jobsCache.get(f"agent:{agent.agentID}").decode("utf-8")
                    if not agentJobs:
                        pipe.set(f"agent:{agent.agentID}", json.dumps([job]))
                    else:
                        updatedJobs = json.loads(agentJobs).append(job)
                        pipe.set(f"agent:{agent.agentID}", json.dumps(updatedJobs))
                pipe.execute()

    def agentCheckin(self, agentID):
        """ Check if the agent has jobs in its queue """
        agentJobs = self.jobsCache.get(f"agent:{agentID}").decode("utf-8")
        if not agentJobs:
            return None
        # a job is available, return agent's job from the cache
        return json.loads(agentJobs)


    def markSent(self, agentID, jobIDs):
        """ Remove first job from agent's cache and transfer from jobsQueue to jobsRunning in DB. """
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
        agentJobs = json.loads(self.jobsCache.get(f"agent:{agentID}").decode("utf-8"))
        for job in agentJobs:
            if job["jobID"] in jobIDs:
                agentJobs.pop(agentJobs.index(job))
        if not agentJobs:
            self.jobsCache.delete(f"agent:{agentID}")
        else:
            self.jobsCache.set(f"agent:{agentID}", json.dumps(agentJobs))



    def refresh(self):
        """ Refresh the job assignments cache from the DB. """
        agentsQuery = Agent.objects()
        self.josbsCache.flushdb()
        with self.jobsCache.pipeline() as pipe:
            for agent in agentsQuery:
                if agent["jobsQueue"]:
                    pipe.set(f"agent:{agent['agentID']}", json.dumps(sorted(agent["jobsQueue"], key = lambda i: i["timeCreated"])))
            # TODO: build groups cache once groups are implemented
            pipe.execute()
