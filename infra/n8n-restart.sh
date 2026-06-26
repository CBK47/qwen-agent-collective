#!/usr/bin/env bash
# Recreate the n8n container with qwen-agent-collective env vars and repo mount.
# Safe: n8n_data is a named volume and survives container recreation.
# Run this from the superchip host as a user with Docker access.
set -euo pipefail

REPO=/home/cbk/qwen-agent-collective

echo "Stopping and removing n8n container..."
docker stop n8n
docker rm n8n

echo "Starting n8n with DashScope env vars..."
docker run -d \
  --name n8n \
  --restart unless-stopped \
  -p 127.0.0.1:5678:5678/tcp \
  --network ai_core_net \
  \
  -v n8n_data:/home/node/.n8n \
  -v /home/cbk/certs/n8n:/certs:ro \
  -v /home/cbk/.local/bin:/home/cbk/.local/bin:ro \
  -v /home/cbk/.local/lib:/home/cbk/.local/lib:ro \
  -v /home/cbk/parameter-golf:/home/cbk/parameter-golf \
  -v "${REPO}:${REPO}" \
  \
  -e "NODE_FUNCTION_ALLOW_BUILTIN=fs,path" \
  -e "N8N_SECURE_COOKIE=true" \
  -e "N8N_PROTOCOL=https" \
  -e "N8N_SSL_CERT=/certs/cert.pem" \
  -e "N8N_SSL_KEY=/certs/key.pem" \
  -e "NODES_EXCLUDE=[]" \
  -e "N8N_RELEASE_TYPE=stable" \
  -e "N8N_BLOCK_ENV_ACCESS_IN_NODE=false" \
  \
  -e "REPO_PATH=${REPO}" \
  -e "DASHSCOPE_API_KEY=$(grep '^DASHSCOPE_API_KEY=' "${REPO}/.env" | cut -d= -f2-)" \
  -e "DASHSCOPE_BASE_URL=$(grep '^DASHSCOPE_BASE_URL=' "${REPO}/.env" | cut -d= -f2-)" \
  -e "QWEN_CHAT_MODEL=$(grep '^QWEN_CHAT_MODEL=' "${REPO}/.env" | cut -d= -f2-)" \
  -e "QWEN_CODER_MODEL=$(grep '^QWEN_CODER_MODEL=' "${REPO}/.env" | cut -d= -f2-)" \
  -e "QWEN_EMBED_MODEL=$(grep '^QWEN_EMBED_MODEL=' "${REPO}/.env" | cut -d= -f2-)" \
  \
  -e "OLLAMA_CHAT_MODEL=qwen3-next-cbk:latest" \
  -e "OLLAMA_CODE_MODEL=qwen3-next-cbk:latest" \
  \
  docker.n8n.io/n8nio/n8n

echo "Done. n8n is restarting; check logs with: docker logs -f n8n"
