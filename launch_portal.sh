#!/usr/bin/env bash
# launch_portal.sh - 1-Click launcher for developer portal & web server
set -e

PORT="${1:-8080}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if server is already running on specified port
if ! python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${PORT}/api/status', timeout=0.4)" &>/dev/null; then
    echo "==> Starting Universal Sentence Refiner Web Server on http://localhost:${PORT}..."
    python3 "${PROJECT_DIR}/main.py" --serve "${PORT}" &
    sleep 0.6
else
    echo "==> Web server already running on http://localhost:${PORT}."
fi

echo "==> Opening Developer Portal in your browser..."
if command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:${PORT}" &>/dev/null &
fi
