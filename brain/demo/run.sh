#!/usr/bin/env bash
# run.sh — one-command MemoryAgent Track-1 demo
# Usage:  cd brain/demo && bash run.sh
#         or from repo root: bash brain/demo/run.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "  MemoryAgent Track-1 Demo — startup"
echo "=================================================="

# ── 1. Bring up Postgres ──────────────────────────────
echo ""
echo "[1/4] Starting Postgres 16 via docker compose …"
docker compose -f docker-compose.demo.yml up -d

# ── 2. Wait for healthy ────────────────────────────────
echo ""
echo "[2/4] Waiting for Postgres to become healthy …"
RETRIES=40
until docker inspect --format='{{.State.Health.Status}}' brain_demo_postgres 2>/dev/null | grep -q healthy; do
  RETRIES=$((RETRIES - 1))
  if [ "$RETRIES" -le 0 ]; then
    echo "ERROR: Postgres did not become healthy in time."
    docker compose -f docker-compose.demo.yml logs
    exit 1
  fi
  printf "."
  sleep 2
done
echo ""
echo "  Postgres is healthy."

# ── 3. Install Python deps ─────────────────────────────
echo ""
echo "[3/4] Installing Python dependencies …"
pip install -q -r requirements.txt

# ── 4. Run the demo ───────────────────────────────────
echo ""
echo "[4/4] Running track1_demo.py …"
echo ""
python track1_demo.py

echo ""
echo "=================================================="
echo "  Demo complete. To tear down Postgres:"
echo "    docker compose -f brain/demo/docker-compose.demo.yml down -v"
echo "=================================================="
