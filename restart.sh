#!/usr/bin/env bash
# restart.sh - Restart Universal Sentence Refiner Daemon & Web Portal
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Restarting Universal Sentence Refiner Services..."
bash "${PROJECT_DIR}/stop.sh"
sleep 0.6
bash "${PROJECT_DIR}/start.sh" "$@"
