#!/usr/bin/env bash
# build_deb.sh - Build standalone .deb package for Ubuntu / Debian

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="1.2.0"
PKG_NAME="refine-sentences"
BUILD_DIR="${PROJECT_DIR}/build/deb"
DIST_DIR="${PROJECT_DIR}/dist"
PKG_ROOT="${BUILD_DIR}/${PKG_NAME}_${VERSION}_all"

echo "==> Preparing Debian package directory structure..."
rm -rf "${BUILD_DIR}"
mkdir -p "${PKG_ROOT}/DEBIAN"
mkdir -p "${PKG_ROOT}/usr/bin"
mkdir -p "${PKG_ROOT}/usr/share/applications"
mkdir -p "${PKG_ROOT}/usr/share/${PKG_NAME}"
mkdir -p "${DIST_DIR}"

# 1. Create DEBIAN/control
cat <<EOF > "${PKG_ROOT}/DEBIAN/control"
Package: ${PKG_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: all
Maintainer: Sunil Bakale <sunilbakaleom3@gmail.com>
Depends: python3 (>= 3.9), python3-tk
Description: Universal Sentence Refiner
 A fast, system-wide sentence refinement tool with interactive visual diffs,
 multi-tone styling, Teach mode, and zero third-party pip dependencies.
 Works seamlessly across all Linux input fields (Antigravity, Chrome, Claude, ChatGPT).
EOF

# 2. Copy source code files
cp -r "${PROJECT_DIR}/refiner" "${PKG_ROOT}/usr/share/${PKG_NAME}/"
cp -r "${PROJECT_DIR}/metrics" "${PKG_ROOT}/usr/share/${PKG_NAME}/"
cp -r "${PROJECT_DIR}/config" "${PKG_ROOT}/usr/share/${PKG_NAME}/"
cp -r "${PROJECT_DIR}/history" "${PKG_ROOT}/usr/share/${PKG_NAME}/"
cp -r "${PROJECT_DIR}/clipboard" "${PKG_ROOT}/usr/share/${PKG_NAME}/"
cp -r "${PROJECT_DIR}/injector" "${PKG_ROOT}/usr/share/${PKG_NAME}/"
cp -r "${PROJECT_DIR}/ui" "${PKG_ROOT}/usr/share/${PKG_NAME}/"
cp -r "${PROJECT_DIR}/daemon" "${PKG_ROOT}/usr/share/${PKG_NAME}/"
cp "${PROJECT_DIR}/main.py" "${PKG_ROOT}/usr/share/${PKG_NAME}/"

# Clean any pycache in build package
find "${PKG_ROOT}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# 3. Create wrapper executable scripts in /usr/bin
cat <<'EOF' > "${PKG_ROOT}/usr/bin/refine-sentences"
#!/usr/bin/env bash
exec python3 /usr/share/refine-sentences/main.py --mode=popup --paste "$@"
EOF
chmod +x "${PKG_ROOT}/usr/bin/refine-sentences"

cat <<'EOF' > "${PKG_ROOT}/usr/bin/refine-sentences-flash"
#!/usr/bin/env bash
exec python3 /usr/share/refine-sentences/main.py --mode=clipboard --paste "$@"
EOF
chmod +x "${PKG_ROOT}/usr/bin/refine-sentences-flash"

# 4. Create .desktop launcher entry
cat <<EOF > "${PKG_ROOT}/usr/share/applications/${PKG_NAME}.desktop"
[Desktop Entry]
Name=Sentence Refiner
Comment=Universal system-wide sentence refinement with visual diffs
Exec=/usr/bin/refine-sentences
Terminal=false
Type=Application
Categories=Utility;TextTools;
EOF

# 5. Install systemd user service
mkdir -p "${PKG_ROOT}/usr/lib/systemd/user"
cp "${PROJECT_DIR}/packaging/refine-daemon.service" "${PKG_ROOT}/usr/lib/systemd/user/refine-daemon.service"

# 6. Build the .deb package
echo "==> Building Debian package with dpkg-deb..."
dpkg-deb --root-owner-group --build "${PKG_ROOT}" "${DIST_DIR}/${PKG_NAME}_${VERSION}_all.deb"

echo "==> Build complete: ${DIST_DIR}/${PKG_NAME}_${VERSION}_all.deb"
echo "==> Install anytime with: sudo dpkg -i dist/${PKG_NAME}_${VERSION}_all.deb"
