#!/bin/bash

$COMPOSE_CMD -f docker-compose.prod.yml -p danswer-stack up --force-recreate -d
