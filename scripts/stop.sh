#!/usr/bin/env bash
# stop.sh - Stop Universal Sentence Refiner Daemon & Web Portal

CONFIG_DIR="${HOME}/.config/refine_tool"

echo "=========================================================="
echo "  🛑 Stopping Universal Sentence Refiner Services"
echo "=========================================================="

# 1. Stop Web Server
if command -v systemctl &>/dev/null && systemctl --user is-active refine-web.service &>/dev/null; then
    systemctl --user stop refine-web.service
    echo "  [✓] Web Portal Server: Stopped (systemd)"
else
    # Try stopping via API first
    python3 -c "import urllib.request; urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8080/api/server/stop', data=b'{}'), timeout=0.5)" &>/dev/null || true
    # Kill by PID if recorded
    if [ -f "${CONFIG_DIR}/web.pid" ]; then
        PID=$(cat "${CONFIG_DIR}/web.pid")
        kill "$PID" 2>/dev/null || true
        rm -f "${CONFIG_DIR}/web.pid"
    fi
    pkill -f "python3.*main.py --serve" 2>/dev/null || true
    echo "  [✓] Web Portal Server: Stopped"
fi

# 2. Stop Resident Daemon
if command -v systemctl &>/dev/null && systemctl --user is-active refine-daemon.service &>/dev/null; then
    systemctl --user stop refine-daemon.service
    echo "  [✓] Resident Daemon: Stopped (systemd)"
else
    if [ -f "${CONFIG_DIR}/daemon.pid" ]; then
        PID=$(cat "${CONFIG_DIR}/daemon.pid")
        kill "$PID" 2>/dev/null || true
        rm -f "${CONFIG_DIR}/daemon.pid"
    fi
    pkill -f "python3.*main.py --daemon" 2>/dev/null || true
    rm -f "${CONFIG_DIR}/daemon.sock"
    echo "  [✓] Resident Daemon: Stopped"
fi

echo "=========================================================="
echo "  All services stopped successfully."
echo "=========================================================="
