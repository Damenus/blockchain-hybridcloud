FROM python:alpine

WORKDIR daemon
RUN mkdir daemon_dir
COPY main.py .

ENTRYPOINT python3 main.py
