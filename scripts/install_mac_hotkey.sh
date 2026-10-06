#!/usr/bin/env bash
# install_mac_hotkey.sh - Start the global refine hotkey at login (macOS LaunchAgent).
# Usage: bash scripts/install_mac_hotkey.sh [combo]
#   No combo (recommended): the hotkey comes from config ('--set-hotkey' or the web Settings page)
#   and changes apply live. With a combo it is pinned and config changes to the hotkey are ignored.
# Uninstall: launchctl bootout gui/$(id -u)/com.refine.hotkey && rm ~/Library/LaunchAgents/com.refine.hotkey.plist
set -e
COMBO="${1:-}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYAPP="/opt/homebrew/opt/python@3.14/Frameworks/Python.framework/Versions/3.14/Resources/Python.app/Contents/MacOS/Python"
[ -x "$PYAPP" ] || { echo "Python.app not found at $PYAPP (brew install python@3.14 python-tk@3.14)"; exit 1; }
PLIST="$HOME/Library/LaunchAgents/com.refine.hotkey.plist"
LOG="$HOME/.config/refine_tool/hotkey.log"
mkdir -p "$HOME/Library/LaunchAgents" "$HOME/.config/refine_tool"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.refine.hotkey</string>
  <key>ProgramArguments</key><array>
    <string>$PYAPP</string><string>$PROJECT_DIR/main.py</string><string>--hotkey</string>${COMBO:+<string>$COMBO</string>}
  </array>
  <key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$LOG</string>
  <key>StandardErrorPath</key><string>$LOG</string>
</dict></plist>
PL
launchctl bootout "gui/$(id -u)/com.refine.hotkey" 2>/dev/null || true; sleep 1
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Hotkey listener will start at every login (${COMBO:-hotkey from config}). Log: $LOG"
