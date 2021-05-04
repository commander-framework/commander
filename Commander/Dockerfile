FROM tobix/pywine:latest

# DEFAULT ARGS that can be changed
ARG SECRET_KEY="super-secret-default-key"
ARG DB_USER=""
ARG DB_PASS=""
ARG DB_URI="mongodb://localhost/"
ARG CA_HOSTNAME="CAPy.local"
ARG UPLOADS_DIR="/opt/commander/library/"

# set environment variables
ENV SECRET_KEY=$SECRET_KEY
ENV DB_USER=$DB_USER
ENV DB_PASS=$DB_PASS
ENV DB_URI=$DB_URI
ENV CA_HOSTNAME=$CA_HOSTNAME
ENV UPLOADS_DIR=$UPLOADS_DIR

# copy code and install dependencies
COPY ./* /opt/commander
RUN pip install -r /opt/commander/requirements.txt

# mostly for documentation purposes --> should still specify at runtime
EXPOSE 5000
VOLUME $UPLOADS_DIR

# start app
ENTRYPOINT ["python", "/opt/commander/commander.py"]
