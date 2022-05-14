from config import Config
import json
from .models import Agent
import redis
from server import log
from utils import utcNowTimestamp


class Cache:
    def __init__(self):
        self.cache = redis.from_url(Config.REDIS_URI)

    def assignJobToAgents(self, job, agentIDs):
        """ Assign a job to one or more agents in the Redis cache. """
        with self.cache.pipeline() as pipe:
            jobs = self.cache.mget(agentIDs)
            for agentID, agentJobs in zip(agentIDs, jobs):
                if not agentJobs or agentJobs == b'null':
                    pipe.set(f"agent:{agentID}", f"[{job.to_json()}]")
                    log.debug(f"Added job '{job.filename}' to empty job queue for agent {agentID}")
                else:
                    updatedJobs = json.loads(agentJobs).append(json.loads(job.to_json()))
                    pipe.set(f"agent:{agentID}", json.dumps(updatedJobs))
                    log.debug(f"Added job '{job.filename}' to existing job queue for agent {agentID}")
            pipe.execute()

    def removeJobsFromAgent(self, jobIDs, agentID):
        agentJobs = json.loads(self.cache.get(f"agent:{agentID}").decode("utf-8"))
        for job in agentJobs:
            if job["jobID"] in jobIDs:
                agentJobs.pop(agentJobs.index(job))
        if not agentJobs:
            self.cache.delete(f"agent:{agentID}")
        else:
            self.cache.set(f"agent:{agentID}", json.dumps(agentJobs))


    def acquireLock(self, lockID):
        """ Create a lock in Redis to prevent a race condition. """
        with self.cache.pipeline() as pipe:
            errorCount = 0
            waitCount = 0
            while True:
                try:
                    pipe.watch("lock:assignJob")
                    lock = self.cache.get("lock:assignJob")
                    if not lock:
                        pipe.set(f"lock:{lockID}", f"1")
                        break
                    waitCount += 1
                    if waitCount == 5:
                        log.info(f"Waiting {waitCount} times to aquire cache lock '{lockID}'")
                    elif waitCount == 10:
                        log.warning(f"Waiting {waitCount} times to aquire cache lock '{lockID}'")
                    elif waitCount == 20:
                        log.error(f"ERROR: cache lock '{lockID}' appears to be stuck")
                        print(f"ERROR: cache lock '{lockID}' appears to be stuck")
                        raise TimeoutError("could not acquire cache lock")
                except redis.WatchError:
                    errorCount += 1
                    if errorCount % 5 == 0:
                        log.warning(f"WatchError #{errorCount} on lock '{lockID}'")
                    waitCount = 0

    def releaseLock(self, lockID):
        """ Release a lock in Redis. """
        self.cache.delete(f"lock:{lockID}")


class JobBoard:
    def __init__(self):
        self.refresh()

    def assignJob(self, job, agentID=None, groupID=None):
        """ Assign a job to an agent. Update the DB and cache the job in jobAssignments. """
        jobsCache = Cache()
        if not agentID and not groupID:
            raise ValueError("must specify either agentID or groupID when assigning a job")
        if agentID:
            # update DB first and make sure agent exists
            agent = Agent.objects(agentID=agentID).first()
            if not agent:
                raise ValueError("no hosts found matching the agentID in the request")
            agent.jobsQueue.append(job)
            agent.save()
            agentIDs = [agentID]
        elif groupID:
            # update DB first and make sure group exists
            agents = Agent.objects(groups__icontains=groupID)
            if not agents.first():
                raise ValueError("no hosts found matching the groupID in the request")
            agents.update(push__jobsQueue=job)
            agentIDs = [agent.agentID for agent in agents]
        # add job to each agent in cache
        jobsCache.acquireLock("assignJob")
        jobsCache.assignJobToAgents(job, agentIDs)
        jobsCache.releaseLock("assignJob")

    def agentCheckin(self, agentID):
        """ Check if the agent has jobs in its queue. """
        jobsCache = redis.from_url(Config.REDIS_URI)
        agentJobs = jobsCache.get(f"agent:{agentID}")
        if not agentJobs:
            return None
        agentJobs = json.loads(agentJobs.decode("utf-8"))
        # a job is available, return agent's job from the cache
        return agentJobs


    def markSent(self, jobIDs, agentID):
        """ Remove jobs matching jobIDs from agent's cache and transfer them from jobsQueue to jobsRunning in DB. """
        jobsCache = Cache()
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
        jobsCache.acquireLock("assignJob")
        jobsCache.removeJobsFromAgent(jobIDs, agentID)
        jobsCache.releaseLock("assignJob")



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
