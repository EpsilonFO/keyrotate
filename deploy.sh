#!/bin/bash
set -e
cd ~/keyrotate
git pull

echo "Rebuilding keyrotate..."
sudo docker rm -f keyrotate-frontend-build 2>/dev/null || true
sudo docker rm -f $(sudo docker ps -a -q --filter volume=keyrotate_frontend_dist) 2>/dev/null || true
sudo docker volume rm -f keyrotate_frontend_dist

sudo docker compose up -d --build

echo "KeyRotate deployed!"
