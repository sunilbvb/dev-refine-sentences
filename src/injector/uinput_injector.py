"""Linux kernel uinput virtual keyboard injector.

100% Python Standard Library (fcntl, struct, os). Zero external packages.
Emulates hardware keyboard events at the kernel level via /dev/uinput.
Bypasses Wayland sandbox restrictions, Snap sandboxes, Electron limitations,
and window manager event filters by appearing as a legitimate USB hardware keyboard.
"""

import fcntl
import os
import struct
import time
from typing import List, Optional

# Linux uinput ioctl constants
UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_DEV_SETUP = 0x405C5503
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502

# Linux event types and codes
EV_SYN = 0x00
EV_KEY = 0x01
SYN_REPORT = 0

# Key codes (evdev / linux/input-event-codes.h)
KEY_ESC = 1
KEY_LEFTCTRL = 29
KEY_A = 30
KEY_S = 31
KEY_LEFTSHIFT = 42
KEY_Z = 44
KEY_X = 45
KEY_C = 46
KEY_V = 47
KEY_RIGHTSHIFT = 54
KEY_LEFTALT = 56
KEY_RIGHTCTRL = 97
KEY_RIGHTALT = 100
KEY_INSERT = 110
KEY_LEFTMETA = 125
KEY_RIGHTMETA = 126

ALL_SUPPORTED_KEYS = [
    KEY_ESC,
    KEY_LEFTCTRL, KEY_A, KEY_S, KEY_LEFTSHIFT, KEY_Z, KEY_X, KEY_C, KEY_V,
    KEY_RIGHTSHIFT, KEY_LEFTALT, KEY_RIGHTCTRL, KEY_RIGHTALT, KEY_INSERT,
    KEY_LEFTMETA, KEY_RIGHTMETA,
]


class UinputVirtualKeyboard:
    """Persistent virtual hardware keyboard backed by /dev/uinput."""

    def __init__(self, device_name: str = "RefineVirtualKeyboard"):
        self.device_name = device_name
        self.fd: Optional[int] = None
        self._is_ready = False
        self._init_device()

    def _init_device(self) -> bool:
        if not os.path.exists("/dev/uinput"):
            return False

        try:
            self.fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
            fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_KEY)
            fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_SYN)

            # Enable all common keys and modifiers (1..250)
            for code in range(1, 250):
                try:
                    fcntl.ioctl(self.fd, UI_SET_KEYBIT, code)
                except OSError:
                    pass

            BUS_USB = 0x03
            input_id = struct.pack("HHHH", BUS_USB, 0x1234, 0x5678, 0x01)
            raw_name = self.device_name.encode("utf-8")[:79] + b"\x00"
            name_padded = raw_name + b"\x00" * (80 - len(raw_name))
            setup_data = input_id + name_padded + struct.pack("I", 0)

            fcntl.ioctl(self.fd, UI_DEV_SETUP, setup_data)
            fcntl.ioctl(self.fd, UI_DEV_CREATE)
            time.sleep(0.1)
            self._is_ready = True
            return True
        except Exception:
            self.close()
            return False

    @property
    def is_available(self) -> bool:
        return self._is_ready and self.fd is not None

    def _emit(self, code: int, value: int) -> None:
        if not self.is_available or self.fd is None:
            return
        try:
            ev = struct.pack("qqHHi", 0, 0, EV_KEY, code, value)
            syn = struct.pack("qqHHi", 0, 0, EV_SYN, SYN_REPORT, 0)
            os.write(self.fd, ev + syn)
        except OSError:
            pass

    def key_down(self, code: int) -> None:
        self._emit(code, 1)

    def key_up(self, code: int) -> None:
        self._emit(code, 0)

    def tap_key(self, code: int, hold_sec: float = 0.02) -> None:
        self.key_down(code)
        time.sleep(hold_sec)
        self.key_up(code)
        time.sleep(0.01)

    def send_combo(self, modifiers: List[int], key_code: int, hold_sec: float = 0.03) -> None:
        """Press modifiers, press key, release key, release modifiers."""
        for m in modifiers:
            self.key_down(m)
            time.sleep(0.01)

        self.key_down(key_code)
        time.sleep(hold_sec)
        self.key_up(key_code)
        time.sleep(0.01)

        for m in reversed(modifiers):
            self.key_up(m)
            time.sleep(0.01)

    def release_all_modifiers(self) -> None:
        """Ensure all modifier keys are in RELEASE state."""
        for mod in (
            KEY_LEFTCTRL, KEY_RIGHTCTRL,
            KEY_LEFTALT, KEY_RIGHTALT,
            KEY_LEFTSHIFT, KEY_RIGHTSHIFT,
            KEY_LEFTMETA, KEY_RIGHTMETA,
        ):
            self.key_up(mod)
        time.sleep(0.01)

    def select_all(self) -> bool:
        """Simulate Ctrl+A."""
        if not self.is_available:
            return False
        self.release_all_modifiers()
        time.sleep(0.02)
        self.send_combo([KEY_LEFTCTRL], KEY_A, hold_sec=0.03)
        time.sleep(0.05)
        return True

    def copy(self) -> bool:
        """Simulate Ctrl+C."""
        if not self.is_available:
            return False
        self.release_all_modifiers()
        time.sleep(0.02)
        self.send_combo([KEY_LEFTCTRL], KEY_C, hold_sec=0.03)
        time.sleep(0.06)
        return True

    def paste(self) -> bool:
        """Simulate Ctrl+V."""
        if not self.is_available:
            return False
        self.release_all_modifiers()
        time.sleep(0.03)
        self.send_combo([KEY_LEFTCTRL], KEY_V, hold_sec=0.04)
        time.sleep(0.05)
        return True

    def close(self) -> None:
        if self.fd is not None:
            try:
                fcntl.ioctl(self.fd, UI_DEV_DESTROY)
            except Exception:
                pass
            try:
                os.close(self.fd)
            except Exception:
                pass
            self.fd = None
        self._is_ready = False

    def __del__(self):
        self.close()
