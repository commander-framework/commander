#!/bin/sh

# start flask service
gunicorn -b 0.0.0.0:5000 \
         --workers ${WORKERS} \
		 --worker_connections ${WORKER_CONNECTIONS} \
		 --worker_class gevent \
		 --worker-tmp-dir /dev/shm \
		 --preload \
		 server:app