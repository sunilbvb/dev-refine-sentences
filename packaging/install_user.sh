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
cp -r "${PROJECT_DIR}/src" "${APP_DIR}/"
cp -r "${PROJECT_DIR}/scripts" "${APP_DIR}/"
cp -r "${PROJECT_DIR}/docs" "${APP_DIR}/"
cp -r "${PROJECT_DIR}/web" "${APP_DIR}/"
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

cat <<'EOF' > "${BIN_DIR}/refine-portal"
#!/usr/bin/env bash
exec "${HOME}/.local/share/refine-sentences/scripts/launch_portal.sh" "$@"
EOF
chmod +x "${BIN_DIR}/refine-portal"

chmod +x "${APP_DIR}/scripts/"*.sh

# Install .desktop application launcher
mkdir -p "${HOME}/.local/share/applications"
cp "${PROJECT_DIR}/packaging/refine-portal.desktop" "${HOME}/.local/share/applications/"

# Install systemd user services (daemon and optional web portal)
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

cat <<EOF > "${SYSTEMD_USER_DIR}/refine-web.service"
[Unit]
Description=Universal Sentence Refiner Web Documentation Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 ${APP_DIR}/main.py --serve 8080
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
EOF

# Reload and enable systemd user services if systemctl is available
if command -v systemctl &>/dev/null; then
    systemctl --user daemon-reload
    systemctl --user enable --now refine-daemon.service || true
    systemctl --user enable --now refine-web.service || true
    echo "==> Resident daemon & Web portal services enabled via systemd --user!"
fi

# Auto-configure GNOME keyboard shortcuts
if command -v gsettings &>/dev/null; then
    bash "${APP_DIR}/scripts/setup_shortcuts.sh" || true
fi

echo "==> Installation complete!"
echo "    Commands available in ${BIN_DIR}:"
echo "      - refine-sentences       (Interactive popup)"
echo "      - refine-sentences-flash (Instant silent replace)"
echo "      - refine-portal          (1-Click Web portal launcher)"

echo "    Commands available: ${BIN_DIR}/refine-sentences and ${BIN_DIR}/refine-sentences-flash"
echo "    Ensure ${BIN_DIR} is in your PATH."
