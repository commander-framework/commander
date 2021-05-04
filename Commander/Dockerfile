FROM tobix/pywine:latest

# DEFAULT ARGS that can be changed
ARG SECRET_KEY="super-secret-default-key"
ARG DB_USER=""
ARG DB_PASS=""
ARG DB_NAME="commander"
ARG DB_URI="mongodb://localhost/"
ARG UPLOADS_DIR="/opt/commander/library/"

# set environment variables
ARG SECRET_KEY=$SECRET_KEY
ARG DB_USER=$DB_USER
ARG DB_PASS=$DB_PASS
ARG DB_NAME=$DB_NAME
ARG DB_URI=$DB_URI
ARG UPLOADS_DIR=$UPLOADS_DIR

# copy code and install dependencies
COPY ./* /opt/commander
RUN pip install -r /opt/commander/requirements.txt

# for documentation purposes --> still need to specify at runtime
EXPOSE 80:5000
VOLUME CommanderLibrary:$UPLOADS_DIR

# start app
ENTRYPOINT ["python", "/run/commander.py"]
