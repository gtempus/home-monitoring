#!/usr/bin/env bash
set -euo pipefail

REBOOT_REASONS=()

# --- uv ---
if [ -x "$HOME/.local/bin/uv" ]; then
    echo "==> uv already installed"
else
    echo "==> Installing uv"
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"
echo "    $(uv --version)"

# --- system packages ---
echo "==> Installing system build deps"
sudo apt update
sudo apt install -y build-essential python3-dev python3-libgpiod

# --- state directory ---
echo "==> Ensuring state directory"
sudo mkdir -p /var/lib/power-monitor
sudo chown "$USER":"$USER" /var/lib/power-monitor

# --- gpio group ---
echo "==> Ensuring $USER is in gpio group"
if getent group gpio | grep -q "\b$USER\b"; then
    echo "    already a member (per /etc/group)"
else
    sudo usermod -aG gpio "$USER"
    echo "    added $USER to gpio group"
fi

# --- project directory and venv ---
echo "==> Ensuring project venv"
mkdir -p "$HOME/power-monitor"
VENV_CFG="$HOME/power-monitor/.venv/pyvenv.cfg"
if [ -f "$VENV_CFG" ] && grep -q "^include-system-site-packages = true" "$VENV_CFG"; then
    echo "    venv already configured with system site packages"
else
    cd "$HOME/power-monitor"
    uv venv --system-site-packages
fi

# --- UART for Notecard serial ---
UART_CHANGED=0
CONFIG="/boot/firmware/config.txt"
CMDLINE="/boot/firmware/cmdline.txt"

echo "==> Configuring UART for Notecard serial"
if [ ! -f "$CONFIG" ]; then
    echo "    WARNING: $CONFIG not found; skipping UART config"
elif ! grep -q "^enable_uart=1" "$CONFIG"; then
    echo "enable_uart=1" | sudo tee -a "$CONFIG" > /dev/null
    echo "    added enable_uart=1 to $CONFIG"
    UART_CHANGED=1
else
    echo "    enable_uart=1 already present"
fi

if [ -f "$CMDLINE" ] && grep -q "console=serial0,115200" "$CMDLINE"; then
    sudo sed -i 's/console=serial0,115200 //' "$CMDLINE"
    echo "    removed serial console from $CMDLINE"
    UART_CHANGED=1
else
    echo "    serial console already disabled"
fi

# --- kernel update check ---
RUNNING_KERNEL=$(uname -r)
LATEST_KERNEL=$(ls /boot/vmlinuz-* 2>/dev/null | sed 's|.*/vmlinuz-||' | sort -V | tail -1 || true)
KERNEL_CHANGED=0
if [ -n "$LATEST_KERNEL" ] && [ "$RUNNING_KERNEL" != "$LATEST_KERNEL" ]; then
    KERNEL_CHANGED=1
fi

# --- summary ---
echo
echo "==> Setup complete."

if [ "$UART_CHANGED" -eq 1 ]; then
    REBOOT_REASONS+=("UART configuration changed")
fi
if [ "$KERNEL_CHANGED" -eq 1 ]; then
    REBOOT_REASONS+=("kernel updated ($RUNNING_KERNEL -> $LATEST_KERNEL)")
fi

if [ "${#REBOOT_REASONS[@]}" -gt 0 ]; then
    echo
    echo "Reboot required:"
    for reason in "${REBOOT_REASONS[@]}"; do
        echo "  - $reason"
    done
    echo "    sudo reboot"
fi

if ! id -nG "$USER" | grep -qw gpio; then
    echo
    echo "Log out and back in for the gpio group change to take effect."
fi