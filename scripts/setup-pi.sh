#!/usr/bin/env bash
set -euo pipefail

echo "==> Installing uv"
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

echo "==> Verifying uv is on PATH"
uv --version

echo "==> Installing system build deps"
sudo apt update
sudo apt install -y build-essential python3-dev python3-libgpiod

echo "==> Creating state directory"
sudo mkdir -p /var/lib/power-monitor
sudo chown "$USER":"$USER" /var/lib/power-monitor

echo "==> Adding $USER to gpio group"
sudo usermod -aG gpio "$USER"

echo "==> Creating project directory and venv"
mkdir -p "$HOME/power-monitor"
cd "$HOME/power-monitor"
uv venv --system-site-packages

echo
echo "==> Setup complete."
echo "Log out and back in (or reboot) for the gpio group to apply."
echo "Then run scripts/deploy.sh from your laptop."