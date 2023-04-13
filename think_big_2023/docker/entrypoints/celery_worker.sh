#!/bin/sh

# Get the hostname from the environment variable
host=$(eval $HOSTNAME_COMMAND)

# Run a worker with concurrency equal to the number of CPU cores and using the hostname from the environment variable
celery -A celeryconf worker --loglevel=info --concurrency 1 --hostname=worker@%h --hostname="${host}" -E
