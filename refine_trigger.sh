#!/usr/bin/env bash
# refine_trigger.sh - Global hotkey hook for Sentence Refiner (Popup Mode)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/main.py" --mode=popup --paste "$@"
