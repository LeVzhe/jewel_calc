#!/usr/bin/env bash
# Полный подъем приложения. Сейчас это API и PostgreSQL.
# Фронтенд добавится в этот же скрипт, когда появится папка frontend.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT/backend"

if [[ ! -f .env ]]; then
  echo "Создай backend/.env: скопируй backend/.env.example и заполни ключи Cloudflare R2."
  exit 1
fi

if [[ $# -eq 0 ]]; then
  docker compose up --build
else
  docker compose "$@"
fi
