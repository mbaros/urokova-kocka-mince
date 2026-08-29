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
mkdir -p data data-martas
docker compose -f deploy/docker-compose.yml up -d --build --remove-orphans

rc=0
for c in kocka kocka-martas; do   # one container per instance — keep in sync with docker-compose.yml and docs/instances/
  ok=""
  for _ in $(seq 1 30); do
    if docker exec "$c" python -c "import urllib.request,sys;sys.exit(0 if b'\"ok\":true' in urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=2).read() else 1)" 2>/dev/null; then
      ok=1; break
    fi
    sleep 1
  done
  if [ -n "$ok" ]; then echo "✓ $c answers /api/health"; else echo "✗ $c did not become healthy" >&2; docker logs --tail 30 "$c" >&2; rc=1; fi
done
exit $rc
