#!/bin/bash

docker stop webui && docker rm webui

docker run -d \
  -p 8080:8080
  --name webui \
  --network traefik-net \
  --env-file webui.env \
  -v webui_data:/home/node/.n8n \
  --label "traefik.enable=true" \
  --label 'traefik.http.routers.webui.rule=Host("chat.xptoai.com.br")' \
  --label "traefik.http.routers.webui.entrypoints=websecure" \
  --label "traefik.http.routers.webui.tls.certresolver=le" \
  --label "traefik.http.services.webui.loadbalancer.server.port=8080" \
  ghcr.io/open-webui/open-webui:main
