#!/usr/bin/env bash
docker build -t damenus/daemon:0.1 .
cat ~/my_password_docker.txt | docker login --username damenus --password-stdin
docker push damenus/daemon:0.1
