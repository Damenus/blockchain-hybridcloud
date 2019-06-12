#!/usr/bin/env bash
docker build -t damenus/hdfssb-processor:0.1 .
cat ~/my_password_docker.txt | docker login --username damenus --password-stdin
docker push damenus/hdfssb-processor:0.1
