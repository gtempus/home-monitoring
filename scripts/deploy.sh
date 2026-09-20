#!/usr/bin/env bash
set -euo pipefail

PI_HOST="${PI_HOST:-gtempus@project-pi-2-b.local}"
PI_DIR="${PI_DIR:-/home/gtempus/power-monitor}"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Syncing source to ${PI_HOST}:${PI_DIR}"
rsync -avz --delete \
    --exclude='.venv/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.git/' \
    --exclude='.idea/' \
    --exclude='*.iml' \
    --exclude='.pytest_cache/' \
    --exclude='.mypy_cache/' \
    --exclude='.ruff_cache/' \
    --exclude='.coverage' \
    --exclude='htmlcov/' \
    "${LOCAL_DIR}/" "${PI_HOST}:${PI_DIR}/"

echo "==> Syncing dependencies on the Pi"
ssh "${PI_HOST}" "cd ${PI_DIR} && \$HOME/.local/bin/uv sync --frozen"

echo "==> Cleaning uv cache (8GB card)"
ssh "${PI_HOST}" "\$HOME/.local/bin/uv cache clean"

echo "==> Running tests on the Pi"
ssh "${PI_HOST}" "cd ${PI_DIR} && \$HOME/.local/bin/uv run pytest -v"