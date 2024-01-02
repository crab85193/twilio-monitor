#!/bin/bash

CURRENT_DIR=`cd $(dirname $0) && pwd`

container_id=`docker ps -q -f status=running -f name=twilio-monitor`

if [ -z "$container_id" ]; then
    echo "twilio-monitor is not running"
    exit 0
fi

docker exec -it twilio-monitor python main.py
