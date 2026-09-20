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

UART_CHANGED=0

echo "==> Configuring UART for Notecard serial"
CONFIG="/boot/firmware/config.txt"
if ! grep -q "^enable_uart=1" "$CONFIG"; then
    echo "enable_uart=1" | sudo tee -a "$CONFIG" > /dev/null
    echo "    added enable_uart=1 to $CONFIG"
    UART_CHANGED=1
else
    echo "    enable_uart=1 already present"
fi

CMDLINE="/boot/firmware/cmdline.txt"
if grep -q "console=serial0,115200" "$CMDLINE"; then
    sudo sed -i 's/console=serial0,115200 //' "$CMDLINE"
    echo "    removed serial console from $CMDLINE"
    UART_CHANGED=1
else
    echo "    serial console already disabled"
fi

echo
echo "==> Setup complete."

if [ "$UART_CHANGED" -eq 1 ]; then
    echo "UART configuration changed. Reboot before running the deploy:"
    echo "    sudo reboot"
fi

if ! id -nG "$USER" | grep -qw gpio; then
    echo "Log out and back in for the gpio group to apply."
fi