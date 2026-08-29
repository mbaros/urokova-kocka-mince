#!/usr/bin/env bash
# Deploy / update Úroková kočka on martin1.
#
#   ssh martin1 ~/projects/urokova-kocka-mince/deploy/deploy.sh
#
# Pulls main, rebuilds the image, restarts the container, checks /api/health.
# The Caddy route (secret path + token) is configured once by hand —
# see deploy/Caddyfile.snippet — and is not touched here. Progress data in
# ./data survives redeploys (bind mount).
set -euo pipefail
cd "$(dirname "$0")/.."

git pull --ff-only
mkdir -p data
docker compose -f deploy/docker-compose.yml up -d --build --remove-orphans

for _ in $(seq 1 30); do
  if docker exec kocka python -c "import urllib.request,sys;sys.exit(0 if b'\"ok\":true' in urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=2).read() else 1)" 2>/dev/null; then
    echo "✓ kocka answers /api/health"
    exit 0
  fi
  sleep 1
done
echo "✗ kocka did not become healthy" >&2
docker logs --tail 30 kocka >&2
exit 1
