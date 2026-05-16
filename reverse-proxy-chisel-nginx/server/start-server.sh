#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Создан server/.env. Отредактируйте CHISEL_PASSWORD и запустите скрипт снова."
  exit 1
fi

if grep -q 'change_me_before_start\|replace_this_with_a_strong_password' .env; then
  echo "Сначала отредактируйте server/.env и задайте нормальный CHISEL_PASSWORD."
  exit 1
fi

docker compose up -d
