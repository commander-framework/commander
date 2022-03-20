from .models import Agent
from time import sleep
from utils import utcNowTimestamp


class JobBoard:
    def __init__(self):
        self.jobAssignments = {"groups": {}, "agents": {}}
        self.mutex = False
        self.refresh()

    def assignJob(self, job, agentID=None, groupID=None):
        """ Assign a job to an agent. Update the DB and cache the job in jobAssignments. """
        while self.mutex:
            sleep(1)
        self.mutex = True
        if not agentID and not groupID:
            raise ValueError("must specify either agentID or groupID when assigning a job.")
        # add job to DB and cache
        if agentID:
            if agentID in self.jobAssignments["agents"]:
                self.jobAssignments["agents"][agentID].append(job)
            else:
                self.jobAssignments["agents"][agentID] = [job]
            agent = Agent.objects(agentID=agentID).first()
            if not agent:
                raise ValueError("no hosts found matching the agentID in the request")
            agent.jobsQueue.append(job)
            agent.save()
        elif groupID:
            if groupID in self.jobAssignments["groups"]:
                self.jobAssignments["groups"][groupID].append(job)
            else:
                self.jobAssignments["groups"][groupID] = [job]
            agents = Agent.objects(groups__icontains=groupID)
            if not agents.first():
                raise ValueError("no hosts found matching the groupID in the request")
            agents.update(push__jobsQueue=job)
        self.mutex = False
        return True

    def agentCheckin(self, agentID, groups):
        """ Check if the agent has jobs in its queue """
        if agentID in self.jobAssignments["agents"]:
            if self.jobAssignments["agents"][agentID]:
                # job is available, return it from the cache
                return self.jobAssignments["agents"][agentID][0]
        elif groups:
            # TODO: implement
            pass


    def markSent(self, agentID):
        """ Remove first job from agent's cache and transfer from jobsQueue to jobsRunning in DB. """
        while self.mutex:
            sleep(1)
        self.mutex = True
        # job is available, return it from the cache
        agent = Agent.objects(agentID=agentID).first()
        jobsQueue = sorted(agent["jobsQueue"], key = lambda i: i["timeCreated"])
        job = jobsQueue.pop(0)
        job["timeDispatched"] = utcNowTimestamp()
        agent["jobsRunning"].append(job)
        agent["lastCheckin"] = utcNowTimestamp()
        agent.save()
        self.jobAssignments["agents"][agentID].pop(0)
        self.mutex = False


    def refresh(self):
        """ Refresh the job assignments cache from the DB. """
        while self.mutex:
            sleep(1)
        self.mutex = True
        agentsQuery = Agent.objects()
        for agent in agentsQuery:
            if agent["jobsQueue"]:
                self.jobAssignments["agents"][agent["agentID"]] = sorted(agent["jobsQueue"], key = lambda i: i["timeCreated"])
        # TODO: build groups cache once groups are implemented
        self.mutex = False