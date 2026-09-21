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

# --- I2C for Notecard ---
I2C_CHANGED=0
CONFIG="/boot/firmware/config.txt"

echo "==> Configuring I2C for Notecard"
if dpkg -l i2c-tools 2>/dev/null | grep -q "^ii"; then
    echo "    i2c-tools already installed"
else
    sudo apt install -y i2c-tools
    echo "    installed i2c-tools"
fi

if getent group i2c | grep -q "\b$USER\b"; then
    echo "    $USER already in i2c group"
else
    sudo usermod -aG i2c "$USER"
    echo "    added $USER to i2c group"
fi

if grep -q "^dtparam=i2c_arm=on,i2c_arm_baudrate=100000" "$CONFIG"; then
    echo "    I2C already configured with baudrate"
elif grep -q "^dtparam=i2c_arm=on" "$CONFIG"; then
    sudo sed -i 's|^dtparam=i2c_arm=on.*|dtparam=i2c_arm=on,i2c_arm_baudrate=100000|' "$CONFIG"
    echo "    updated i2c_arm line to include baudrate"
    I2C_CHANGED=1
else
    echo "dtparam=i2c_arm=on,i2c_arm_baudrate=100000" | sudo tee -a "$CONFIG" > /dev/null
    echo "    added i2c_arm to $CONFIG"
    I2C_CHANGED=1
fi

# --- sudoers rule for shutdown ---
SUDOERS_FILE="/etc/sudoers.d/power-monitor"
SHUTDOWN_RULE="$USER ALL=(root) NOPASSWD: /usr/bin/systemctl --no-block poweroff"

echo "==> Ensuring sudoers rule for shutdown"
if [ ! -f "$SUDOERS_FILE" ]; then
    echo "$SHUTDOWN_RULE" | sudo tee "$SUDOERS_FILE" > /dev/null
    sudo chmod 0440 "$SUDOERS_FILE"
    echo "    created $SUDOERS_FILE"
elif sudo grep -qF "$SHUTDOWN_RULE" "$SUDOERS_FILE"; then
    echo "    shutdown rule already present"
else
    echo "$SHUTDOWN_RULE" | sudo tee -a "$SUDOERS_FILE" > /dev/null
    echo "    appended shutdown rule to $SUDOERS_FILE"
fi

sudo visudo -c -f "$SUDOERS_FILE" > /dev/null
echo "    sudoers syntax OK"

# --- persistent journald ---
if [ ! -d /var/log/journal ]; then
    echo "==> Enabling persistent journal"
    sudo mkdir -p /var/log/journal
    sudo systemd-tmpfiles --create --prefix /var/log/journal
    sudo systemctl restart systemd-journald
    echo "    persistent journal enabled"
else
    echo "==> Persistent journal already enabled"
fi

# --- kernel update check ---
RUNNING_KERNEL=$(uname -r)
# On 32-bit Raspberry Pi OS, the v7 kernel is the expected running kernel.
# Check for the matching v7 image, not the v8 one that apt also installs.
if echo "$RUNNING_KERNEL" | grep -q -- "-v7"; then
    EXPECTED_SUFFIX="+rpt-rpi-v7"
elif echo "$RUNNING_KERNEL" | grep -q -- "-v8"; then
    EXPECTED_SUFFIX="+rpt-rpi-v8"
else
    EXPECTED_SUFFIX=""
fi

LATEST_KERNEL=$(ls /boot/vmlinuz-*"$EXPECTED_SUFFIX" 2>/dev/null | sed 's|.*/vmlinuz-||' | sort -V | tail -1 || true)
KERNEL_CHANGED=0
if [ -n "$LATEST_KERNEL" ] && [ "$RUNNING_KERNEL" != "$LATEST_KERNEL" ]; then
    KERNEL_CHANGED=1
fi

# --- summary ---
echo
echo "==> Setup complete."

if [ "$I2C_CHANGED" -eq 1 ]; then
    REBOOT_REASONS+=("I2C configuration changed")
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