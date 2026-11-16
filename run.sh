#!/usr/bin/env bash
# Полный подъем приложения в фоне: интерфейс, API и PostgreSQL.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT/backend"

if [[ ! -f .env ]]; then
  echo "Создай backend/.env: скопируй backend/.env.example и заполни ключи Cloudflare R2."
  exit 1
fi

if [[ $# -eq 0 ]]; then
  docker compose up --build -d
  # Висячие образы и кэш сборки. Тома, в том числе база, не удаляются.
  docker image prune -f
  docker builder prune -f
else
  docker compose "$@"
fi
