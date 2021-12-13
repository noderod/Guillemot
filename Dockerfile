FROM ubuntu:20.04

COPY main.py              /Guillemot/guillemot
COPY aux_handler/         /Guillemot/aux_handler/
COPY benchmarks/          /Guillemot/benchmarks/
COPY inference/           /Guillemot/inference/
COPY parser/              /Guillemot/parser/

WORKDIR /Guillemot

RUN apt-get update && apt-get install -y bc python3-pip && pip3 install lark matplotlib numpy scipy &&\
    chmod +x /Guillemot/guillemot &&\
    # Creates a simlink to guillemot so that it can be run as directly as an a program from /bin without "./"
    ln -s /Guillemot/guillemot /bin
