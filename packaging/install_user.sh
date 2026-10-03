#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="${HOME}/.local/bin"
SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"
APP_DIR="${HOME}/.local/share/refine-sentences"

echo "==> Installing Universal Sentence Refiner to user environment (~/.local)..."

mkdir -p "${BIN_DIR}"
mkdir -p "${SYSTEMD_USER_DIR}"
mkdir -p "${APP_DIR}"

# Copy application files
cp -r "${PROJECT_DIR}/refiner" "${APP_DIR}/"
cp -r "${PROJECT_DIR}/metrics" "${APP_DIR}/"
cp -r "${PROJECT_DIR}/config" "${APP_DIR}/"
cp -r "${PROJECT_DIR}/history" "${APP_DIR}/"
cp -r "${PROJECT_DIR}/clipboard" "${APP_DIR}/"
cp -r "${PROJECT_DIR}/injector" "${APP_DIR}/"
cp -r "${PROJECT_DIR}/ui" "${APP_DIR}/"
cp -r "${PROJECT_DIR}/daemon" "${APP_DIR}/"
cp -r "${PROJECT_DIR}/web" "${APP_DIR}/"
cp -r "${PROJECT_DIR}/web_server" "${APP_DIR}/"
cp "${PROJECT_DIR}/index.html" "${APP_DIR}/"
cp "${PROJECT_DIR}/main.py" "${APP_DIR}/"

# Clean pycache
find "${APP_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Install launchers
cat <<'EOF' > "${BIN_DIR}/refine-sentences"
#!/usr/bin/env bash
exec python3 "${HOME}/.local/share/refine-sentences/main.py" --mode=popup --paste "$@"
EOF
chmod +x "${BIN_DIR}/refine-sentences"

cat <<'EOF' > "${BIN_DIR}/refine-sentences-flash"
#!/usr/bin/env bash
exec python3 "${HOME}/.local/share/refine-sentences/main.py" --mode=clipboard --paste "$@"
EOF
chmod +x "${BIN_DIR}/refine-sentences-flash"

# Install systemd user service
cat <<EOF > "${SYSTEMD_USER_DIR}/refine-daemon.service"
[Unit]
Description=Universal Sentence Refiner Resident Daemon
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 ${APP_DIR}/main.py --daemon
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
EOF

# Reload and enable systemd user service if systemctl is available
if command -v systemctl &>/dev/null; then
    systemctl --user daemon-reload
    systemctl --user enable --now refine-daemon.service || true
    echo "==> Resident daemon service enabled and started via systemd --user!"
fi

echo "==> Installation complete!"
echo "    Commands available: ${BIN_DIR}/refine-sentences and ${BIN_DIR}/refine-sentences-flash"
echo "    Ensure ${BIN_DIR} is in your PATH."
