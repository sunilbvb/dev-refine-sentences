#!/usr/bin/env bash
# restart.sh - Restart Universal Sentence Refiner Daemon & Web Portal
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Restarting Universal Sentence Refiner Services..."
bash "${SCRIPT_DIR}/stop.sh"
sleep 0.6
bash "${SCRIPT_DIR}/start.sh" "$@"
