#####################
### Builder image ###
#####################
# using ubuntu LTS version
FROM lsiobase/ubuntu:focal AS builder-image

# avoid stuck build due to user prompt
ARG DEBIAN_FRONTEND=noninteractive

# install python
RUN apt-get update && apt-get install --no-install-recommends -y python3.9 python3.9-dev python3.9-venv python3-pip python3-wheel build-essential && \
	apt-get clean && rm -rf /var/lib/apt/lists/*

# create and activate virtual environment
# using final folder name to avoid path issues with packages
RUN python3.9 -m venv /home/abc/venv
ENV PATH="/home/abc/venv/bin:$PATH"

# install requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir wheel
RUN pip3 install --no-cache-dir -r requirements.txt

####################
### Runner image ###
####################
FROM lsiobase/ubuntu:focal AS runner-image

# DEFAULT ARGS that can be changed
ARG ADMIN_HASH=""
ARG APP_NAME="Commander"
ARG CA_HOSTNAME="CAPy.local"
ARG DB_URI="mongomock://localhost/"
ARG DB_USER=""
ARG DB_PASS=""
ARG LOG_LEVEL="4"
ARG REDIS_PASS=""
ARG REDIS_URI="redis://localhost:6379"
ARG SECRET_KEY="super-secret-default-key"
ARG UPLOADS_DIR="/opt/${APP_NAME}/library/"
# specify WORKERS to match the number of CPU cores allocated to your container
ARG WORKERS="2"
# specify WORKER_CONNECTIONS to the number determined by (client_count/workers)*2
ARG WORKER_CONNECTIONS="1000"

# set environment variables
ENV ADMIN_HASH=$ADMIN_HASH
ENV APP_NAME=$APP_NAME
ENV CA_HOSTNAME=$CA_HOSTNAME
ENV DB_URI=$DB_URI
ENV DB_USER=$DB_USER
ENV DB_PASS=$DB_PASS
ENV LOG_LEVEL=$LOG_LEVEL
ENV REDIS_PASS=$REDIS_PASS
ENV REDIS_URI=$REDIS_URI
ENV SECRET_KEY=$SECRET_KEY
ENV UPLOADS_DIR=$UPLOADS_DIR
ENV WORKERS=$WORKERS
ENV WORKER_CONNECTIONS=$WORKER_CONNECTIONS

# install python
RUN apt-get update && apt-get install --no-install-recommends -y python3.9 python3-venv && \
	apt-get clean && rm -rf /var/lib/apt/lists/*

# use unprivileged user and virtual environment
RUN chsh -s /bin/bash abc
COPY --from=builder-image /home/abc/venv /home/abc/venv

# create directory for runtime and switch to user
WORKDIR /app
COPY . .
RUN chmod +x ./run.sh

# expose port
EXPOSE 5000
# mark library as volume and set permissions
VOLUME ${UPLOADS_DIR}
RUN echo chown -R abc:abc ${UPLOADS_DIR} >> /etc/cont-init.d/10-adduser


# make sure all messages always reach console
ENV PYTHONUNBUFFERED=1

# activate virtual environment
ENV VIRTUAL_ENV=/home/abc/venv
ENV PATH="/home/abc/venv/bin:$PATH"

# /dev/shm is mapped to shared memory and is used to improve gunicorn heartbeat performance
# each active agent counts as 1 constant event due to web sockets staying connected
CMD ["su", "-c", "'./run.sh'", "abc"]
