#!/usr/bin/env bash
docker-compose -f ../docker-swarm.yml down
docker build -t damenus/hdfssb-processor:0.2 .
cat ~/my_password_docker.txt | docker login --username damenus --password-stdin
docker push damenus/hdfssb-processor:0.2
docker-compose -f ../docker-swarm.yml up --force