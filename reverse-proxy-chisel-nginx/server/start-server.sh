#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created server/.env from .env.example. Edit CHISEL_AUTH before production use."
fi

docker compose up -d

echo "Server containers started."
echo "Published ports: 4014, 4015, 4016"
