#!/usr/bin/env bash
# status.sh - Check status of Sentence Refiner services

CONFIG_DIR="${HOME}/.config/refine_tool"
PORT="${1:-8080}"

echo "=========================================================="
echo "  📊 Universal Sentence Refiner Service Status"
echo "=========================================================="

# Daemon status
if command -v systemctl &>/dev/null && systemctl --user is-active refine-daemon.service &>/dev/null; then
    echo "  ⚡ Resident Daemon:  🟢 ACTIVE (systemd: refine-daemon.service)"
elif [ -S "${CONFIG_DIR}/daemon.sock" ]; then
    echo "  ⚡ Resident Daemon:  🟢 ACTIVE (UNIX socket: ${CONFIG_DIR}/daemon.sock)"
else
    echo "  ⚡ Resident Daemon:  🔴 INACTIVE"
fi

# Web server status
if python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${PORT}/api/status', timeout=1.0)" &>/dev/null; then
    echo "  🌐 Web Portal:       🟢 ONLINE (http://localhost:${PORT})"
else
    echo "  🌐 Web Portal:       🔴 OFFLINE"
fi

echo "=========================================================="
