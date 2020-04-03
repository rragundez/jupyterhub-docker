#!/bin/bash

source .env

docker build --tag jupyterhub .
docker run \
    --env AAD_CLIENT_SECRET=${AAD_CLIENT_SECRET} \
    --env AAD_CLIENT_ID=${AAD_CLIENT_ID} \
    --env AAD_OAUTH_CALLBACK_URL=${AAD_OAUTH_CALLBACK_URL} \
    --env AAD_TENANT_ID=${AAD_TENANT_ID} \
    --publish 9443:9443 \
    jupyterhub:latest
