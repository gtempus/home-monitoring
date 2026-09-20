#!/usr/bin/env bash
set -euo pipefail
rm -rf .venv
uv venv --system-site-packages
uv sync