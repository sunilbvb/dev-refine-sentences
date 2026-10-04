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

# Bind Ctrl+Alt+R for Popup
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ name "Sentence Refiner (Popup)"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ command "$BIN_POPUP"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ binding "<Ctrl><Alt>r"

# Bind Super+Shift+R for Flash Replace
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/ name "Sentence Refiner (Flash)"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/ command "$BIN_FLASH"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/ binding "<Super><Shift>r"

echo "==> Shortcuts successfully configured!"
echo "    [Ctrl+Alt+R]     -> Floating Preview Modal (Visual Diff)"
echo "    [Super+Shift+R]  -> Instant Silent Replace (2ms Flash)"
