#!/usr/bin/env bash
# setup_shortcuts_mac.sh - macOS global shortcut setup for Sentence Refiner.
#
# The old Quick Action / Services approach was removed: it does not work in Electron apps (Claude
# desktop) or web editors (Google Chat). Use the global hotkey listener instead - see
# docs/MACOS_SETUP.md. This script just installs it as a login item.
set -e
exec bash "$(dirname "${BASH_SOURCE[0]}")/install_mac_hotkey.sh" "$@"
