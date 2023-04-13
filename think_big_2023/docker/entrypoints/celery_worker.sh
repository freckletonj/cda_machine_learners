#!/bin/sh

# run a worker
celery -A celeryconf worker --loglevel=info --concurrency 1 -E
