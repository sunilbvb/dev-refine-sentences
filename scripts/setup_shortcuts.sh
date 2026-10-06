#!/usr/bin/env bash
# setup_shortcuts.sh - Automatically register GNOME keyboard shortcuts for Sentence Refiner

set -e
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_POPUP="${HOME}/.local/bin/refine-sentences"
BIN_FLASH="${HOME}/.local/bin/refine-sentences-flash"

# Fallback to repository scripts if ~/.local/bin not in PATH
[ ! -x "$BIN_POPUP" ] && BIN_POPUP="${PROJECT_DIR}/scripts/refine_trigger.sh"
[ ! -x "$BIN_FLASH" ] && BIN_FLASH="${PROJECT_DIR}/scripts/refine_flash.sh"

echo "==> Registering GNOME shortcuts..."

# Read existing bindings
EXISTING=$(gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings)
if [ "$EXISTING" = "@as []" ] || [ -z "$EXISTING" ]; then
    LIST="['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/', '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/']"
else
    # Append custom0 and custom1 if not present
    LIST="['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/', '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/']"
fi

gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "$LIST"

# Bind custom0 (Popup) and custom1 (Flash)
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ name "Sentence Refiner (Popup)"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ command "$BIN_POPUP"

gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/ name "Sentence Refiner (Flash)"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/ command "$BIN_FLASH"

# Apply configured shortcuts from config.json
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, '${PROJECT_DIR}/src')
from config.settings import ConfigManager
cfg = ConfigManager()
cfg._apply_linux_shortcut('hotkey_popup', cfg.get_setting('hotkey_popup') or 'ctrl+alt+r')
cfg._apply_linux_shortcut('hotkey', cfg.get_setting('hotkey') or 'alt+a*2')
" || {
    gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ binding "<Ctrl><Alt>r"
    gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/ binding "<Alt>a"
}

POPUP_BIND=$(gsettings get org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ binding 2>/dev/null || echo "'<Ctrl><Alt>r'")
FLASH_BIND=$(gsettings get org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/ binding 2>/dev/null || echo "'<Alt>a'")

echo "==> Shortcuts successfully configured!"
echo "    [Popup] -> ${POPUP_BIND}"
echo "    [Flash] -> ${FLASH_BIND}"

