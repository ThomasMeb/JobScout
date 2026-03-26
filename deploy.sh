#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="docker-compose.prod.yml"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$PROJECT_DIR"

# Save current commit for rollback
PREV_COMMIT=$(git rev-parse HEAD)

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
HEALTHY=false
for i in $(seq 1 30); do
    if docker compose -f "$COMPOSE_FILE" exec -T backend curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "    Backend healthy!"
        HEALTHY=true
        break
    fi
    sleep 2
done

if [ "$HEALTHY" = false ]; then
    echo "    ERROR: Backend not healthy after 30 attempts"
    docker compose -f "$COMPOSE_FILE" logs backend --tail=50

    echo "==> Rolling back to $PREV_COMMIT..."
    git checkout "$PREV_COMMIT"
    docker compose -f "$COMPOSE_FILE" build --parallel
    docker compose -f "$COMPOSE_FILE" up -d
    echo "==> Rollback complete. Please investigate the failed deployment."
    exit 1
fi

echo "==> Cleaning up old images..."
docker image prune -f

echo "==> Deployment complete!"
docker compose -f "$COMPOSE_FILE" ps
