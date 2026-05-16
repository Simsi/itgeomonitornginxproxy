#!/usr/bin/env bash
set -euo pipefail

: "${SERVER_PUBLIC_IP:?Нужно указать SERVER_PUBLIC_IP, например: export SERVER_PUBLIC_IP=84.237.52.214}"
: "${CHISEL_USER:?Нужно указать CHISEL_USER, например: export CHISEL_USER=user}"
: "${CHISEL_PASSWORD:?Нужно указать CHISEL_PASSWORD}"

# Вариант для Docker Desktop на macOS/Windows.
# Здесь локальные сервисы хоста доступны контейнеру как host.docker.internal.
docker run --rm jpillora/chisel:latest \
  client \
  --auth "${CHISEL_USER}:${CHISEL_PASSWORD}" \
  "${SERVER_PUBLIC_IP}:4016" \
  R:0.0.0.0:18050:host.docker.internal:8050 \
  R:0.0.0.0:4014:host.docker.internal:8765
