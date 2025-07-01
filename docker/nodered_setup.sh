#!/bin/bash

docker stop nodered && docker rm nodered

docker run -d \
  --name nodered \
  --network traefik-net \
  --env-file nodered.env \
  -v nodered_data:/data \
  --label "traefik.enable=true" \
  --label 'traefik.http.routers.nodered.rule=Host("nodered.xptoai.com.br")' \
  --label "traefik.http.routers.nodered.entrypoints=websecure" \
  --label "traefik.http.routers.nodered.tls.certresolver=le" \
  --label "traefik.http.services.nodered.loadbalancer.server.port=1880" \
  nodered/node-red
  
