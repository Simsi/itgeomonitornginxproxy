#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created client/.env from .env.example. Edit SERVER_HOST and CHISEL_AUTH before production use."
fi

docker compose up -d --build

echo "Client containers started."
echo "Local services expected: 127.0.0.1:8050 and 127.0.0.1:8765"
