"""Linux global hotkey listener using /dev/input and standard library.

100% Python Standard Library. Zero external pip packages.
Monitors keyboard input devices passively via /dev/input/event* (no root required
if user is in 'input' group). Detects multi-tap shortcuts (e.g. Alt+A*2) everywhere,
including Wayland, GNOME, browser input fields, and Electron apps.
"""

import os
import re
import select
import struct
import threading
import time
from typing import Callable, Dict, List, Optional, Set, Tuple

# Linux input_event struct format:
# struct timeval time (16 bytes on 64-bit); __u16 type; __u16 code; __s32 value;
EVENT_FORMAT = "qqHHi"
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)
EV_KEY = 1

LINUX_KEY_CODES: Dict[str, int] = {
    "a": 30, "b": 48, "c": 46, "d": 32, "e": 18, "f": 33, "g": 34, "h": 35,
    "i": 23, "j": 36, "k": 37, "l": 38, "m": 50, "n": 49, "o": 24, "p": 25,
    "q": 16, "r": 19, "s": 31, "t": 20, "u": 22, "v": 47, "w": 17, "x": 45,
    "y": 21, "z": 44,
    "space": 57, "enter": 28, "tab": 15, "esc": 1,
}

LINUX_MODIFIER_CODES: Dict[str, Set[int]] = {
    # On Linux with Toshy/Kinto keyremapper, physical Alt may be remapped to Super (Meta) or Option
    "alt": {56, 100, 125, 126},       # KEY_LEFTALT, KEY_RIGHTALT, KEY_LEFTMETA, KEY_RIGHTMETA
    "super": {125, 126, 56, 100},     # KEY_LEFTMETA, KEY_RIGHTMETA, KEY_LEFTALT, KEY_RIGHTALT
    "ctrl": {29, 97},                 # KEY_LEFTCTRL, KEY_RIGHTCTRL
    "shift": {42, 54},                # KEY_LEFTSHIFT, KEY_RIGHTSHIFT
}

CODE_TO_MODIFIER: Dict[int, str] = {}
for mod_name, codes in LINUX_MODIFIER_CODES.items():
    for c in codes:
        if c not in CODE_TO_MODIFIER:
            CODE_TO_MODIFIER[c] = mod_name


def discover_keyboard_devices() -> List[str]:
    """Find all keyboard event devices in /dev/input from /proc/bus/input/devices."""
    devices: List[str] = []
    proc_devices = "/proc/bus/input/devices"
    if os.path.exists(proc_devices):
        try:
            with open(proc_devices, "r", encoding="utf-8") as f:
                content = f.read()
            for block in content.split("\n\n"):
                if "Handlers=" in block and "kbd" in block:
                    for token in block.split():
                        if token.startswith("event"):
                            dev_path = f"/dev/input/{token}"
                            if os.path.exists(dev_path):
                                devices.append(dev_path)
        except Exception:
            pass

    if not devices:
        import glob
        devices = sorted(glob.glob("/dev/input/event*"))

    return devices


class LinuxHotkeyListener:
    """Listens passively for configured global hotkeys on Linux."""

    def __init__(
        self,
        hotkey_spec: str = "alt+s*2",
        on_trigger: Optional[Callable[[], None]] = None,
        tap_window: float = 0.8,
    ):
        self.hotkey_spec = hotkey_spec
        self.on_trigger = on_trigger
        self.tap_window = tap_window
        self.running = False
        self._thread: Optional[threading.Thread] = None

        self.target_code, self.required_mods, self.required_taps = self._parse_spec(hotkey_spec)

    def _parse_spec(self, spec: str) -> Tuple[int, Set[str], int]:
        """Parse combo like 'alt+a*2' -> (target_code, {'alt'}, 2)."""
        spec = spec.strip().lower().replace(" ", "")
        taps = 1
        if "*" in spec:
            spec, _, count_str = spec.partition("*")
            try:
                taps = int(count_str)
            except ValueError:
                taps = 2

        parts = spec.split("+")
        key_name = parts[-1]
        mod_aliases = {
            "control": "ctrl", "option": "alt", "opt": "alt",
            "cmd": "super", "win": "super", "command": "super",
        }
        mods = {mod_aliases.get(m, m) for m in parts[:-1]}

        target_code = LINUX_KEY_CODES.get(key_name, 30)  # default 'a'
        return target_code, mods, taps

    def update_hotkey(self, spec: str) -> None:
        """Update hotkey spec dynamically without restarting listener."""
        self.hotkey_spec = spec
        self.target_code, self.required_mods, self.required_taps = self._parse_spec(spec)

    def start(self) -> bool:
        """Start listener in a daemon thread. Returns True if keyboard devices opened."""
        if self.running:
            return True
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, name="LinuxHotkeyListener", daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        """Stop listening and close devices."""
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _run_loop(self) -> None:
        """Event loop polling /dev/input devices using select.poll()."""
        poller = select.poll()
        open_fds: Dict[int, str] = {}
        devices = discover_keyboard_devices()

        for dev in devices:
            try:
                fd = os.open(dev, os.O_RDONLY | os.O_NONBLOCK)
                poller.register(fd, select.POLLIN)
                open_fds[fd] = dev
            except (PermissionError, OSError):
                continue

        if not open_fds:
            self.running = False
            return

        active_mods: Set[str] = set()
        last_tap_time: float = 0.0
        tap_count: int = 0

        try:
            while self.running:
                # Poll with 500ms timeout so thread responds to stop()
                events = poller.poll(500)
                now = time.time()

                # Tap expiration: reset tap_count if window passed
                if tap_count > 0 and (now - last_tap_time > self.tap_window):
                    tap_count = 0

                for fd, revents in events:
                    if revents & select.POLLIN:
                        try:
                            data = os.read(fd, EVENT_SIZE * 32)
                        except OSError:
                            continue

                        offset = 0
                        while offset + EVENT_SIZE <= len(data):
                            _, _, ev_type, code, val = struct.unpack_from(EVENT_FORMAT, data, offset)
                            offset += EVENT_SIZE

                            if ev_type != EV_KEY:
                                continue

                            # Update modifier tracking
                            if code in CODE_TO_MODIFIER:
                                mod_name = CODE_TO_MODIFIER[code]
                                if val == 1:   # Key down
                                    active_mods.add(mod_name)
                                elif val == 0: # Key up
                                    active_mods.discard(mod_name)

                            # Check for target key press down (val == 1)
                            if code == self.target_code and val == 1:
                                # Check if required modifiers are satisfied
                                if self.required_mods.issubset(active_mods):
                                    # Ensure no unwanted ctrl modifier
                                    if "ctrl" not in active_mods:
                                        if now - last_tap_time <= self.tap_window:
                                            tap_count += 1
                                        else:
                                            tap_count = 1
                                        last_tap_time = now

                                        try:
                                            with open("/tmp/refine_hotkey.log", "a") as f:
                                                f.write(f"[{time.strftime('%X')}] Tap {tap_count}/{self.required_taps} detected for {self.hotkey_spec}\n")
                                        except Exception:
                                            pass

                                        if tap_count >= self.required_taps:
                                            tap_count = 0
                                            last_tap_time = 0.0
                                            try:
                                                with open("/tmp/refine_hotkey.log", "a") as f:
                                                    f.write(f"[{time.strftime('%X')}] TRIGGER FIRED for {self.hotkey_spec}!\n")
                                            except Exception:
                                                pass
                                            if self.on_trigger:
                                                # Dispatch trigger in background thread so loop continues
                                                threading.Thread(target=self.on_trigger, daemon=True).start()
        finally:
            for fd in open_fds:
                try:
                    os.close(fd)
                except OSError:
                    pass
