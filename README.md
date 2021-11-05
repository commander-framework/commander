![Commander Logo](resources/commanderLogo.png)

A server and agent template with easy agent capability adding. (currently in Alpha/development phase -- see project status at the bottom)

![Commander Build/Tests](https://github.com/lawndoc/commander/actions/workflows/build-test.commander.yml/badge.svg)
![CAPy Build/Tests](https://github.com/lawndoc/CAPy/actions/workflows/build-test.yml/badge.svg)

## Out of the box features:

### TLS encryption

All communication between the server and the agents is done via HTTPS and is encrypted, but there is no need to mess with certificates yourself. Server certificate generation and deployment is automatically handled by [CAPy](https://github.com/doctormay6/CAPy), and root CA trust is automatically set up on the agents when they are deployed.

### Certificate authentication (bidirectional)

In addition to a server-side certificate for encryption, admins and agents must use a host-based certificate to be able to interact with the server. This process is also completely automated during agent deployment using the [CAPy](https://github.com/doctormay6/CAPy) microservice.

### Modular capability adding

To add capabilities to your agent, you just need to add a job to the Library. A job can be an executable file or script, and can include many additional files and directories needed during execution.

### Lightweight agent

Agents are coded to do nothing but check in for jobs which keeps the memory footprint low. When a job is sent to an agent, the agent will download what it needs, execute it, and delete it afterwards.

(In the future, functionality will be added that enables agents to store persistent capabilities and background processes on the host side)

### Admin authentication

Admin actions include fetching agent installers, adding jobs to the Library, and deploying jobs to agents. Authentication is required for all admin functionality.

## Project status

The required capabilities from CAPy are fully implemented and tested. The API server is about 90% implemented/prototyped and 70% tested. Agent and admin clients are pretty much in the design phase. The last thing needed to put everything together will be the web proxy (just going to use nginx or apache with prebuilt config).
