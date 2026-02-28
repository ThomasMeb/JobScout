#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="docker-compose.prod.yml"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$PROJECT_DIR"

echo "==> Pulling latest code..."
git pull --ff-only

echo "==> Loading environment..."
set -a
source .env.prod
set +a

echo "==> Building images..."
docker compose -f "$COMPOSE_FILE" build --parallel

echo "==> Starting services..."
docker compose -f "$COMPOSE_FILE" up -d

echo "==> Waiting for backend health..."
for i in $(seq 1 30); do
    if docker compose -f "$COMPOSE_FILE" exec -T backend curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "    Backend healthy!"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "    ERROR: Backend not healthy after 30 attempts"
        docker compose -f "$COMPOSE_FILE" logs backend --tail=50
        exit 1
    fi
    sleep 2
done

echo "==> Cleaning up old images..."
docker image prune -f

echo "==> Deployment complete!"
docker compose -f "$COMPOSE_FILE" ps
