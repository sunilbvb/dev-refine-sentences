"""Input injection and desktop notification utility using Atspi, ydotool, wtype, or xdotool."""

import shutil
import subprocess
import time
from typing import Optional


class KeyInjector:
    """Simulates keystrokes via native Linux Atspi accessibility or CLI tools."""

    def __init__(self):
        self.ydotool = shutil.which("ydotool")
        self.wtype = shutil.which("wtype")
        self.xdotool = shutil.which("xdotool")
        self.notify_send = shutil.which("notify-send")
        self.canberra = shutil.which("canberra-gtk-play")
        self.has_atspi = self._check_atspi()

    def _check_atspi(self) -> bool:
        """Check if GNOME Atspi accessibility keyboard generator is available."""
        try:
            import gi
            gi.require_version("Atspi", "2.0")
            from gi.repository import Atspi
            return hasattr(Atspi, "generate_keyboard_event")
        except Exception:
            return False

    def play_sound(self, sound_id: str = "message-new-instant") -> None:
        """Play subtle sensory confirmation sound."""
        if self.canberra:
            try:
                subprocess.Popen([self.canberra, "-i", sound_id], stderr=subprocess.DEVNULL)
            except Exception:
                pass

    def notify(self, title: str, message: str) -> None:
        """Send transient desktop notification via notify-send."""
        if self.notify_send:
            try:
                subprocess.Popen(
                    [self.notify_send, "-a", "Sentence Refiner", "-t", "2500", "-u", "low", title, message],
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass

    def _get_keycodes(self, keysym: int, fallback_codes: list) -> list:
        """Resolve hardware keycodes for a given keysym using Gdk if available, else fallback."""
        try:
            import gi
            gi.require_version("Gtk", "3.0")
            gi.require_version("Gdk", "3.0")
            from gi.repository import Gdk
            keymap = Gdk.Keymap.get_default()
            success, entries = keymap.get_entries_for_keyval(keysym)
            if success and entries:
                return [e.keycode for e in entries]
        except Exception:
            pass
        return fallback_codes

    def simulate_copy(self) -> bool:
        """Simulate Ctrl+C to copy selected text in any focused application."""
        # Method 1: Atspi native (Wayland GNOME)
        if self.has_atspi:
            try:
                import gi
                gi.require_version("Atspi", "2.0")
                from gi.repository import Atspi

                ctrl_codes = self._get_keycodes(0xffe3, [37])
                c_codes = self._get_keycodes(0x63, [54])
                ctrl_code = ctrl_codes[0] if ctrl_codes else 37
                c_code = c_codes[0] if c_codes else 54

                Atspi.generate_keyboard_event(ctrl_code, None, Atspi.KeySynthType.PRESS)
                Atspi.generate_keyboard_event(c_code, None, Atspi.KeySynthType.PRESS)
                Atspi.generate_keyboard_event(c_code, None, Atspi.KeySynthType.RELEASE)
                Atspi.generate_keyboard_event(ctrl_code, None, Atspi.KeySynthType.RELEASE)
                time.sleep(0.08)
                return True
            except Exception:
                pass

        # Method 2: ydotool
        if self.ydotool:
            try:
                subprocess.run(["ydotool", "key", "29:1", "46:1", "46:0", "29:0"], check=False)
                time.sleep(0.08)
                return True
            except Exception:
                pass

        # Method 3: wtype
        if self.wtype:
            try:
                subprocess.run(["wtype", "-M", "ctrl", "-k", "c", "-m", "ctrl"], check=False)
                time.sleep(0.08)
                return True
            except Exception:
                pass

        # Method 4: xdotool
        if self.xdotool:
            try:
                subprocess.run(["xdotool", "key", "ctrl+c"], check=False)
                time.sleep(0.08)
                return True
            except Exception:
                pass

        return False

    def simulate_paste(self) -> bool:
        """Simulate Ctrl+V to paste refined text over selected text in any focused field."""
        # Wait small moment for user to lift fingers off hotkey combo
        time.sleep(0.15)

        # Method 1: Atspi native (Wayland GNOME)
        if self.has_atspi:
            try:
                import gi
                gi.require_version("Atspi", "2.0")
                from gi.repository import Atspi

                ctrl_codes = self._get_keycodes(0xffe3, [37])
                v_codes = self._get_keycodes(0x76, [55])
                ctrl_code = ctrl_codes[0] if ctrl_codes else 37
                v_code = v_codes[0] if v_codes else 55

                Atspi.generate_keyboard_event(ctrl_code, None, Atspi.KeySynthType.PRESS)
                Atspi.generate_keyboard_event(v_code, None, Atspi.KeySynthType.PRESS)
                Atspi.generate_keyboard_event(v_code, None, Atspi.KeySynthType.RELEASE)
                Atspi.generate_keyboard_event(ctrl_code, None, Atspi.KeySynthType.RELEASE)
                return True
            except Exception:
                pass

        # Method 2: ydotool
        if self.ydotool:
            try:
                subprocess.run(["ydotool", "key", "29:1", "47:1", "47:0", "29:0"], check=False)
                return True
            except Exception:
                pass

        # Method 3: wtype
        if self.wtype:
            try:
                subprocess.run(["wtype", "-M", "ctrl", "-k", "v", "-m", "ctrl"], check=False)
                return True
            except Exception:
                pass

        # Method 4: xdotool
        if self.xdotool:
            try:
                subprocess.run(["xdotool", "key", "ctrl+v"], check=False)
                return True
            except Exception:
                pass

        return False
