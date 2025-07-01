#!/bin/bash

docker stop api && docker rm api

docker run -d \
  --name api \
  --network traefik-net \
  -v api_data:/home/app \
  --label "traefik.enable=true" \
  --label 'traefik.http.routers.api.rule=Host("api.xptoai.com.br")' \
  --label "traefik.http.routers.api.entrypoints=websecure" \
  --label "traefik.http.routers.api.tls.certresolver=le" \
  --label "traefik.http.services.api.loadbalancer.server.port=8000" \
  python:3.12 /home/app/start.sh
