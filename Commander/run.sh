#!/bin/sh

# start flask service
gunicorn -b 0.0.0.0:5000 \
         --workers $WORKERS \
		 --worker-connections $WORKER_CONNECTIONS \
		 --worker-class gevent \
		 --worker-tmp-dir /dev/shm \
		 server:app