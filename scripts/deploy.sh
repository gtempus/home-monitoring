#!/usr/bin/env bash
set -euo pipefail

PI_HOST="${PI_HOST:-gtempus@project-pi-2-b.local}"
PI_DIR="${PI_DIR:-/home/gtempus/power-monitor}"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

show_state() {
    local label="${1:-}"
    echo "==> Service state${label:+ (${label})}"
    ssh "${PI_HOST}" 'bash -s' <<'REMOTE'
for unit in power-monitor.timer power-monitor.service; do
    enabled=$(systemctl is-enabled "$unit" 2>/dev/null | head -n1)
    [ -z "$enabled" ] && enabled=unknown
    active=$(systemctl is-active "$unit" 2>/dev/null | head -n1)
    [ -z "$active" ] && active=unknown
    printf '    %-24s enabled=%-9s active=%s\n' "${unit}:" "$enabled" "$active"
done
REMOTE
}

resume_timer() {
    local rc=$?
    set +e
    echo
    echo "==> Resuming timer"
    ssh "${PI_HOST}" "sudo systemctl start power-monitor.timer"
    if [[ $? -ne 0 ]]; then
        echo "    WARN: failed to resume timer; run manually:" >&2
        echo "    ssh ${PI_HOST} 'sudo systemctl start power-monitor.timer'" >&2
    fi
    show_state "after deploy"
    exit "$rc"
}
trap resume_timer EXIT

show_state "before deploy"

echo
echo "==> Pausing timer"
ssh "${PI_HOST}" "sudo systemctl stop power-monitor.timer"
ssh "${PI_HOST}" "sudo systemctl stop power-monitor.service"

show_state "paused"

echo
echo "==> Ensuring script modes are executable"
chmod +x "${LOCAL_DIR}"/scripts/*.sh

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
ssh "${PI_HOST}" "cd ${PI_DIR} && \$HOME/.local/bin/uv sync --frozen --extra pi"

echo "==> Cleaning uv cache"
ssh "${PI_HOST}" "\$HOME/.local/bin/uv cache clean"

echo "==> Running tests on the Pi"
ssh "${PI_HOST}" "cd ${PI_DIR} && .venv/bin/python -m pytest -v --color=yes"

echo
echo "==> Deploy complete"