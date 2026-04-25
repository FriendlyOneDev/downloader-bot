#!/bin/bash
set -e

ENV_FILE="${1:-.env}"
SERVER="192.168.3.15"
APP_DIR="/home/friendlyone/downloader-bot"
IMAGE="friendlyone/downloader-bot:latest"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE not found"
    exit 1
fi

echo "==> Using env: $ENV_FILE"

echo "==> Building image locally..."
docker build -t "$IMAGE" .

echo "==> Transferring image to $SERVER..."
docker save "$IMAGE" | ssh "$SERVER" "docker load"

echo "==> Syncing compose + env files..."
ssh "$SERVER" "mkdir -p $APP_DIR"
rsync -az docker-compose.yml "$SERVER:$APP_DIR/"
rsync -az "$ENV_FILE" "$SERVER:$APP_DIR/.env"

echo "==> Restarting container on $SERVER..."
ssh "$SERVER" "cd $APP_DIR && docker compose up -d --force-recreate"

echo "==> Done."
ssh "$SERVER" "docker ps --filter name=downloader-bot --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'"
