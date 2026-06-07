#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

export MONEYPRINTER_TURBO_DIR="${MONEYPRINTER_TURBO_DIR:-/Users/stevepark/MoneyPrinterTurbo}"
export MONEYPRINTER_TURBO_OUTPUT_DIR="${MONEYPRINTER_TURBO_OUTPUT_DIR:-/Users/stevepark/MoneyPrinterTurbo/storage/tasks}"
export MONEYPRINTER_TURBO_COMMAND="${MONEYPRINTER_TURBO_COMMAND:-/Users/stevepark/MoneyPrinterTurbo/.venv/bin/python main.py}"

python3 -m tools.youtube_healing.dashboard_server --host 0.0.0.0 --port 8787 --multi-user-root data/users
