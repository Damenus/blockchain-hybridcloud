#FROM python:3
#WORKDIR /hdfssb_client
#COPY . .
#RUN cp ./libRaptorQ.so* /usr/lib
#RUN pip install libraptorq
#CMD /bin/bash

FROM ubuntu

RUN apt-get update
RUN apt-get install -y software-properties-common vim
RUN add-apt-repository ppa:jonathonf/python-3.6
RUN apt-get update

RUN apt-get install -y build-essential python3.6 python3.6-dev python3-pip python3.6-venv
RUN apt-get install -y build-essential python python-dev python-pip
RUN apt-get install -y git

# update pip
#RUN python3.6 -m pip install pip --upgrade
#RUN python3.6 -m pip install wheel


WORKDIR /hdfssb_client
COPY . .
RUN cp ./libRaptorQ.so* /usr/lib
RUN pip install libraptorq
CMD /bin/bash
