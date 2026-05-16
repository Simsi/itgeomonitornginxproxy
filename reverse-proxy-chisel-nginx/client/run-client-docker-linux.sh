#!/usr/bin/env bash
set -euo pipefail

: "${SERVER_PUBLIC_IP:?Нужно указать SERVER_PUBLIC_IP, например: export SERVER_PUBLIC_IP=84.237.52.214}"
: "${CHISEL_USER:?Нужно указать CHISEL_USER, например: export CHISEL_USER=user}"
: "${CHISEL_PASSWORD:?Нужно указать CHISEL_PASSWORD}"

# Вариант для Linux, если chisel не установлен локально.
# --network host нужен, чтобы контейнер видел сервисы хоста на 127.0.0.1:8050 и 127.0.0.1:8765.
docker run --rm --network host jpillora/chisel:latest \
  client \
  --auth "${CHISEL_USER}:${CHISEL_PASSWORD}" \
  "${SERVER_PUBLIC_IP}:4016" \
  R:0.0.0.0:18050:127.0.0.1:8050 \
  R:0.0.0.0:4014:127.0.0.1:8765
