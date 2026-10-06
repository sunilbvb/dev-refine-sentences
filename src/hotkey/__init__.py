"""Global hotkey package (macOS)."""

from .mac_hotkey import parse_hotkey, parse_hotkey_spec, run_hotkey_listener

__all__ = ["parse_hotkey", "parse_hotkey_spec", "run_hotkey_listener"]
