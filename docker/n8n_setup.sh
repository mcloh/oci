#!/bin/bash

docker stop n8n && docker rm n8n

docker run -d \
  --name n8n \
  --network traefik-net \
  --env-file n8n.env \
  -v n8n_data:/home/node/.n8n \
  --label "traefik.enable=true" \
  --label 'traefik.http.routers.n8n.rule=Host("n8n.xptoai.com.br")' \
  --label "traefik.http.routers.n8n.entrypoints=websecure" \
  --label "traefik.http.routers.n8n.tls.certresolver=le" \
  --label "traefik.http.services.n8n.loadbalancer.server.port=5678" \
  docker.n8n.io/n8nio/n8n
  
