#!/bin/bash

docker build --tag jupyterhub .
docker run --publish 9443:9443 jupyterhub:latest
