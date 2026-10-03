#!/usr/bin/env bash
# start.sh - Start Universal Sentence Refiner Daemon & Web Portal
set -e

PORT="${1:-8080}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_DIR="${HOME}/.config/refine_tool"
mkdir -p "${CONFIG_DIR}"

echo "=========================================================="
echo "  🚀 Starting Universal Sentence Refiner Services"
echo "=========================================================="

# 1. Start Resident Daemon (sub-5ms in-RAM processing)
if command -v systemctl &>/dev/null && systemctl --user is-enabled refine-daemon.service &>/dev/null; then
    systemctl --user start refine-daemon.service
    echo "  [✓] Resident Daemon: Active via systemd (refine-daemon.service)"
else
    if ! pgrep -f "python3.*main.py --daemon" &>/dev/null; then
        python3 "${PROJECT_DIR}/main.py" --daemon &
        echo $! > "${CONFIG_DIR}/daemon.pid"
        echo "  [✓] Resident Daemon: Started in background (PID: $(cat "${CONFIG_DIR}/daemon.pid"))"
    else
        echo "  [✓] Resident Daemon: Already running in background."
    fi
fi

# 2. Start Web Portal Server
if command -v systemctl &>/dev/null && systemctl --user is-enabled refine-web.service &>/dev/null; then
    systemctl --user start refine-web.service
    echo "  [✓] Web Portal Server: Active via systemd (refine-web.service)"
else
    if ! python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${PORT}/api/status', timeout=0.3)" &>/dev/null; then
        python3 "${PROJECT_DIR}/main.py" --serve "${PORT}" &
        echo $! > "${CONFIG_DIR}/web.pid"
        echo "  [✓] Web Portal Server: Started on port ${PORT} (PID: $(cat "${CONFIG_DIR}/web.pid"))"
    else
        echo "  [✓] Web Portal Server: Already listening on port ${PORT}."
    fi
fi

# 3. Status summary
echo "----------------------------------------------------------"
echo "  🌐 Web Portal:    http://localhost:${PORT}"
echo "  ⚡ Socket Daemon:  ${CONFIG_DIR}/daemon.sock"
echo "  ⌨️ Global Popup:   Ctrl+Alt+R (or refine-sentences)"
echo "  ⚡ Flash Replace:  Super+Shift+R (or refine-sentences-flash)"
echo "=========================================================="

# 4. Open browser if run interactively from terminal
if [ -t 0 ] && command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:${PORT}" &>/dev/null &
fi
