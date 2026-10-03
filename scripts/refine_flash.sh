#!/usr/bin/env bash
# refine_flash.sh - Zero-dialog instantaneous in-place sentence refiner

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "${SCRIPT_DIR}/main.py" --mode=clipboard --paste "$@"
