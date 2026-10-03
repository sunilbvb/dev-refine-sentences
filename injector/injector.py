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
        """Send desktop notification via notify-send."""
        if self.notify_send:
            try:
                subprocess.run([self.notify_send, "-a", "Sentence Refiner", title, message], check=False)
            except Exception:
                pass

    def simulate_copy(self) -> bool:
        """Simulate Ctrl+C to copy selected text in any focused application."""
        # Method 1: Atspi native (Wayland GNOME)
        if self.has_atspi:
            try:
                import gi
                gi.require_version("Atspi", "2.0")
                from gi.repository import Atspi
                Atspi.generate_keyboard_event(65507, None, Atspi.KeySynthType.PRESS)
                Atspi.generate_keyboard_event(99, "c", Atspi.KeySynthType.PRESSRELEASE)
                Atspi.generate_keyboard_event(65507, None, Atspi.KeySynthType.RELEASE)
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
        # Wait tiny moment for window focus to return to original input field
        time.sleep(0.08)

        # Method 1: Atspi native (Wayland GNOME)
        if self.has_atspi:
            try:
                import gi
                gi.require_version("Atspi", "2.0")
                from gi.repository import Atspi
                Atspi.generate_keyboard_event(65507, None, Atspi.KeySynthType.PRESS)
                Atspi.generate_keyboard_event(118, "v", Atspi.KeySynthType.PRESSRELEASE)
                Atspi.generate_keyboard_event(65507, None, Atspi.KeySynthType.RELEASE)
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
